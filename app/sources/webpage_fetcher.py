import logging
import re
from datetime import datetime, timedelta, timezone
from html import unescape
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from zoneinfo import ZoneInfo

from app.core.time import utc_now
from app.db.models import NewsItem, Source

logger = logging.getLogger(__name__)

REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


class WebpageFetcher:
    def fetch(self, source: Source) -> list[NewsItem]:
        try:
            response = httpx.get(
                source.url,
                timeout=15,
                follow_redirects=True,
                headers=REQUEST_HEADERS,
            )
            response.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            logger.warning("webpage_fetch_skipped source=%s url=%s error=%s", source.name, source.url, exc)
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        if "m.sohu.com/media/" in source.url:
            return self._fetch_sohu_author_page(response.text, source)
        items: list[NewsItem] = []
        seen: set[str] = set()
        for anchor in soup.find_all("a", href=True):
            title = " ".join(anchor.get_text(" ").split())
            href = self._article_url(urljoin(source.url, anchor["href"]), source)
            if not href:
                continue
            if not self._looks_like_news(title, href, source):
                continue
            if href in seen:
                continue
            seen.add(href)
            excerpt = self._nearby_text(anchor)
            published_at = self._published_at_from_text(excerpt)
            items.append(
                NewsItem(
                    source_id=source.id,
                    source_name=source.name,
                    url=href,
                    title=title,
                    raw_excerpt=excerpt,
                    content_text=excerpt or title,
                    published_at=published_at,
                    fetched_at=utc_now(),
                    language=source.language,
                    country_or_region=source.country_or_region,
                    category=source.category,
                )
            )
            if len(items) >= 20:
                break
        return items

    def _article_url(self, href: str, source: Source) -> str | None:
        parsed = urlparse(href)
        if "news.sogou.com" not in urlparse(source.url).netloc:
            return href
        if parsed.netloc == "news.sogou.com" and parsed.path.startswith("/link"):
            return self._resolve_sogou_link(href, source.url)
        return href

    def _resolve_sogou_link(self, href: str, referer: str) -> str | None:
        try:
            response = httpx.get(
                href,
                timeout=8,
                follow_redirects=True,
                headers={**REQUEST_HEADERS, "Referer": referer},
            )
        except Exception as exc:  # noqa: BLE001
            logger.info("sogou_link_resolve_failed url=%s error=%s", href, exc)
            return None
        final_url = str(response.url)
        final_parsed = urlparse(final_url)
        if response.status_code >= 400 or final_parsed.netloc == "news.sogou.com":
            logger.info("sogou_link_skipped url=%s status=%s final=%s", href, response.status_code, final_url)
            return None
        return final_url.split("#")[0]

    def _fetch_sohu_author_page(self, html: str, source: Source) -> list[NewsItem]:
        items: list[NewsItem] = []
        pattern = re.compile(
            r'"title":"(?P<title>[^"]+)".{0,2500}?"postTime":(?P<post>\d+).{0,2500}?"brief":"(?P<brief>[^"]*)".{0,2500}?"url":"(?P<url>//m\.sohu\.com/a/[^"]+)"',
            re.DOTALL,
        )
        for match in pattern.finditer(html):
            title = unescape(match.group("title"))
            brief = unescape(match.group("brief"))
            url = "https:" + match.group("url").split("?")[0]
            post_ms = int(match.group("post"))
            published_at = datetime.fromtimestamp(post_ms / 1000, tz=timezone.utc)
            items.append(
                NewsItem(
                    source_id=source.id,
                    source_name=source.name,
                    url=url,
                    title=title,
                    raw_excerpt=brief,
                    content_text=brief or title,
                    published_at=published_at,
                    fetched_at=utc_now(),
                    language=source.language,
                    country_or_region=source.country_or_region,
                    category=source.category,
                )
            )
            if len(items) >= 30:
                break
        return items

    def _looks_like_news(self, title: str, href: str, source: Source) -> bool:
        if len(title) < 18 or len(title) > 180:
            return False
        parsed = urlparse(href)
        if not parsed.scheme.startswith("http"):
            return False
        lower = f"{title} {href}".lower()
        if source.name.startswith("FDA"):
            if parsed.netloc != "www.fda.gov":
                return False
            if not parsed.path.startswith("/safety/recalls-market-withdrawals-safety-alerts/"):
                return False
            return any(term in lower for term in ["cosmetic", "beauty", "skin", "hair", "sunscreen"])
        if "jumeili.cn" in parsed.netloc:
            return "/News/View/" in parsed.path
        return True

    def _nearby_text(self, anchor) -> str:
        parent = anchor.find_parent(["article", "tr", "li", "div"]) or anchor.parent
        if not parent:
            return ""
        text = " ".join(parent.get_text(" ").split())
        return text[:600]

    def _published_at_from_text(self, text: str) -> datetime | None:
        now_local = datetime.now(ZoneInfo("Asia/Shanghai"))
        if "刚刚" in text:
            return now_local.astimezone(timezone.utc)
        match = re.search(r"(\d+)\s*分钟前", text)
        if match:
            return (now_local - timedelta(minutes=int(match.group(1)))).astimezone(timezone.utc)
        match = re.search(r"(\d+)\s*小时前", text)
        if match:
            return (now_local - timedelta(hours=int(match.group(1)))).astimezone(timezone.utc)
        match = re.search(r"(\d+)\s*天前", text)
        if match:
            return (now_local - timedelta(days=int(match.group(1)))).astimezone(timezone.utc)
        match = re.search(r"(20\d{2})[-/.年](\d{1,2})[-/.月](\d{1,2})", text)
        if match:
            year, month, day = (int(part) for part in match.groups())
            return datetime(year, month, day, tzinfo=ZoneInfo("Asia/Shanghai")).astimezone(timezone.utc)
        return None
