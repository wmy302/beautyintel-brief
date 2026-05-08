import logging
import re
from time import perf_counter

from sqlalchemy.orm import Session

from app.db.models import NewsItem, Source
from app.ingestion.deduper import Deduper
from app.ingestion.normalizer import normalize_item
from app.intelligence.classifier import RuleBasedClassifier
from app.intelligence.risk_detector import RiskDetector
from app.intelligence.scorer import ScoringEngine
from app.intelligence.summarizer import RuleBasedSummarizer
from app.sources.manager import SourceManager
from app.sources.manual_importer import ManualCSVImporter
from app.sources.rss_fetcher import RSSFetcher
from app.sources.webpage_fetcher import WebpageFetcher
from app.sources.xhs_api_fetcher import XHSSearchAPIFetcher

logger = logging.getLogger(__name__)

BEAUTY_RE = re.compile(
    r"\b(beauty|cosmetic|cosmetics|skin|skincare|hair|sunscreen|makeup|fragrance|lip|lips|serum|grooming|personal care)\b"
    r"|美妆|化妆品|护肤|彩妆|口红|香水|防晒|面霜|精华|洗护|小红书",
    re.IGNORECASE,
)

MAINSTREAM_CONTEXT_RE = re.compile(
    r"消费|零售|品牌|电商|直播|市场|营销|广告|质量|监管|标准|抽检|召回|投诉|内卷|促消费|新消费|产业链|供应链|商贸|商超|百货|回暖|增长|进口|国货|行业|财报|销售额|GMV"
)

SEARCH_NOISE_RE = re.compile(
    r"#|教程|分享|日常妆|日常生活|大赏哪家强|短视频|视频|自拍视频|种草合集|麻豆|妆容"
)

MAINSTREAM_SOURCE_NAMES = [
    "人民网",
    "央视网",
    "新华网",
    "中国网",
    "中国日报",
    "中国经济网",
    "中新",
    "澎湃",
    "界面",
]


class IngestionPipeline:
    def __init__(self) -> None:
        self.manager = SourceManager()
        self.manual = ManualCSVImporter()
        self.rss = RSSFetcher()
        self.webpage = WebpageFetcher()
        self.xhs_api = XHSSearchAPIFetcher()
        self.deduper = Deduper()
        self.classifier = RuleBasedClassifier()
        self.risk = RiskDetector()
        self.scorer = ScoringEngine()
        self.summarizer = RuleBasedSummarizer()

    def run(self, db: Session, dry_run: bool = False) -> dict:
        started = perf_counter()
        sources = self.manager.sync_to_db(db)
        enabled = [s for s in sources if s.enabled]
        collected: list[tuple[NewsItem, Source]] = []
        raw_fetched = 0
        for source in enabled:
            try:
                logger.info("source_fetch_start source=%s type=%s", source.name, source.source_type)
                raw_items = self._fetch(source)
                raw_fetched += len(raw_items)
                logger.info("source_fetch_done source=%s count=%s", source.name, len(raw_items))
                for item in raw_items:
                    if not self._is_relevant(item, source):
                        continue
                    collected.append((normalize_item(item), source))
            except Exception:  # noqa: BLE001
                logger.exception("source_fetch_failed source=%s", source.name)

        unique_items = self.deduper.dedupe_batch([item for item, _ in collected])
        source_by_name = {source.name: source for _, source in collected}
        existing_by_hash = {row.title_hash: row for row in db.query(NewsItem).all() if row.title_hash}
        inserted = 0
        refreshed = 0
        touched_item_ids: list[int] = []
        processed: list[NewsItem] = []
        for item in unique_items:
            existing = existing_by_hash.get(item.title_hash)
            if existing is not None:
                if not dry_run:
                    existing.fetched_at = item.fetched_at
                    existing.raw_excerpt = item.raw_excerpt or existing.raw_excerpt
                    existing.content_text = item.content_text or existing.content_text
                    if item.url:
                        existing.url = item.url
                        existing.canonical_url = item.canonical_url
                    if item.published_at is not None:
                        existing.published_at = item.published_at
                    refreshed += 1
                    touched_item_ids.append(existing.id)
                continue
            source = source_by_name.get(item.source_name) or db.query(Source).filter(Source.id == item.source_id).one_or_none()
            try:
                self.classifier.classify(item)
                self.risk.detect(item)
                self.scorer.score(item, source)
                self.summarizer.summarize(item)
                item.status = "processed"
            except Exception as exc:  # noqa: BLE001
                item.status = "error"
                item.error_message = str(exc)
                logger.exception("item_process_failed title=%s", item.title)
            processed.append(item)
            if not dry_run:
                db.add(item)
                db.flush()
                touched_item_ids.append(item.id)
                inserted += 1
        if not dry_run:
            db.commit()
        return {
            "source_count": len(enabled),
            "raw_fetched_count": raw_fetched,
            "fetched_count": len(collected),
            "unique_count": len(unique_items),
            "inserted_count": inserted if not dry_run else 0,
            "refreshed_count": refreshed if not dry_run else 0,
            "item_ids": touched_item_ids if not dry_run else [],
            "dry_run": dry_run,
            "elapsed_seconds": round(perf_counter() - started, 2),
        }

    def _fetch(self, source: Source) -> list[NewsItem]:
        if source.source_type == "manual_csv":
            return self.manual.import_file(source)
        if source.source_type == "rss":
            return self.rss.fetch(source)
        if source.source_type == "webpage":
            return self.webpage.fetch(source)
        if source.source_type == "xhs_api":
            return self.xhs_api.fetch(source)
        logger.info("source_skipped_placeholder source=%s type=%s", source.name, source.source_type)
        return []

    def _is_relevant(self, item: NewsItem, source: Source) -> bool:
        text = f"{item.title} {item.raw_excerpt} {item.content_text}"
        source_name = source.name.lower()
        if "搜狗新闻" in source.name:
            if SEARCH_NOISE_RE.search(text) or any(domain in item.url for domain in ["post.mp.qq.com", "newsa.html5.qq.com"]):
                return False
            return bool(BEAUTY_RE.search(text) and MAINSTREAM_CONTEXT_RE.search(text))
        if any(name.lower() in source_name for name in ["pr.com", "pr newswire"]):
            return bool(BEAUTY_RE.search(text))
        if any(name.lower() in source_name for name in MAINSTREAM_SOURCE_NAMES):
            return bool(BEAUTY_RE.search(text) or MAINSTREAM_CONTEXT_RE.search(text))
        return True
