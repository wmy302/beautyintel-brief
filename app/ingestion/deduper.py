import hashlib
import re
from difflib import SequenceMatcher
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from app.db.models import NewsItem


TRACKING_PREFIXES = ("utm_",)
DROP_PARAMS = {"spm", "from", "fbclid", "gclid"}


def canonicalize_url(url: str) -> str:
    if not url:
        return ""
    parsed = urlparse(url.strip())
    scheme = "https" if parsed.scheme in {"http", "https", ""} else parsed.scheme
    netloc = parsed.netloc.lower()
    query = []
    for key, val in parse_qsl(parsed.query, keep_blank_values=True):
        if key in DROP_PARAMS or any(key.startswith(prefix) for prefix in TRACKING_PREFIXES):
            continue
        query.append((key, val))
    path = parsed.path.rstrip("/") or parsed.path
    return urlunparse((scheme, netloc, path, "", urlencode(query), ""))


def normalized_title(title: str) -> str:
    title = re.sub(r"^(快讯|独家|重磅|突发)[:：\s]+", "", title.strip())
    return re.sub(r"[\s\W_]+", "", title, flags=re.UNICODE).lower()


def title_hash(title: str) -> str:
    return hashlib.sha256(normalized_title(title).encode("utf-8")).hexdigest()


def content_hash(content: str) -> str:
    return hashlib.sha256((content or "")[:1000].encode("utf-8")).hexdigest()


def is_similar_title(left: str, right: str, threshold: float = 0.88) -> bool:
    return SequenceMatcher(None, normalized_title(left), normalized_title(right)).ratio() >= threshold


class Deduper:
    def enrich_hashes(self, item: NewsItem) -> NewsItem:
        item.canonical_url = canonicalize_url(item.url)
        item.title_hash = title_hash(item.title)
        item.content_hash = content_hash(item.content_text or item.raw_excerpt or item.title)
        return item

    def dedupe_batch(self, items: list[NewsItem]) -> list[NewsItem]:
        kept: list[NewsItem] = []
        for item in items:
            self.enrich_hashes(item)
            duplicate = next(
                (
                    existing
                    for existing in kept
                    if (item.canonical_url and item.canonical_url == existing.canonical_url)
                    or item.title_hash == existing.title_hash
                    or is_similar_title(item.title, existing.title)
                ),
                None,
            )
            if duplicate:
                item.is_duplicate = True
                item.duplicate_group_id = duplicate.title_hash
            else:
                item.duplicate_group_id = item.title_hash
                kept.append(item)
        return kept

