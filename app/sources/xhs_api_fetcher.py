import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.time import utc_now
from app.db.models import NewsItem, Source
from app.util import parse_dt

logger = logging.getLogger(__name__)


class XHSSearchAPIFetcher:
    def fetch(self, source: Source) -> list[NewsItem]:
        settings = get_settings()
        api_url = source.url or settings.xhs_search_api_url
        token = settings.xhs_search_api_token
        if not api_url or not token:
            logger.info("xhs_api_skipped reason=missing_api_url_or_token")
            return []

        keywords = [part.strip() for part in settings.xhs_search_keywords.split(",") if part.strip()]
        items: list[NewsItem] = []
        for keyword in keywords:
            try:
                response = httpx.get(
                    api_url,
                    params={
                        "token": token,
                        "keyword": keyword,
                        "page": 1,
                        "page_size": settings.xhs_search_page_size,
                        "sort": "time_descending",
                    },
                    timeout=20,
                    follow_redirects=True,
                    headers={"User-Agent": "BeautyIntelBrief/0.1 (+authorized xhs api client)"},
                )
                response.raise_for_status()
                items.extend(self._items_from_payload(response.json(), source, keyword))
            except Exception as exc:  # noqa: BLE001
                logger.warning("xhs_api_fetch_failed keyword=%s error=%s", keyword, exc)
        return items[: settings.xhs_search_page_size]

    def _items_from_payload(self, payload: Any, source: Source, keyword: str) -> list[NewsItem]:
        rows = [row for row in _walk_dicts(payload) if _title(row)]
        items: list[NewsItem] = []
        for row in rows:
            title = _title(row)
            if not title:
                continue
            url = _first(row, ["url", "link", "note_url", "share_url", "web_url"]) or ""
            note_id = _first(row, ["note_id", "id", "noteId"])
            if not url and note_id:
                url = f"https://www.xiaohongshu.com/explore/{note_id}"
            excerpt = _first(row, ["desc", "description", "content", "summary", "display_title"]) or title
            items.append(
                NewsItem(
                    source_id=source.id,
                    source_name=source.name,
                    url=url,
                    title=title,
                    raw_excerpt=excerpt,
                    content_text=excerpt,
                    published_at=_published_at(row),
                    fetched_at=utc_now(),
                    language=source.language,
                    country_or_region=source.country_or_region,
                    category=source.category,
                    related_platforms_json='["小红书"]',
                    tags_json=f'["小红书", "{keyword}"]',
                )
            )
        return items


def _walk_dicts(value: Any) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    if isinstance(value, dict):
        found.append(value)
        for child in value.values():
            found.extend(_walk_dicts(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(_walk_dicts(child))
    return found


def _first(row: dict[str, Any], keys: list[str]) -> str | None:
    for key in keys:
        value = row.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return None


def _title(row: dict[str, Any]) -> str:
    return _first(row, ["title", "display_title", "note_title", "name"]) or ""


def _published_at(row: dict[str, Any]) -> datetime | None:
    value = row.get("publish_time") or row.get("published_at") or row.get("time") or row.get("create_time") or row.get("created_at")
    if value is None:
        return None
    if isinstance(value, int | float):
        timestamp = value / 1000 if value > 10_000_000_000 else value
        return datetime.fromtimestamp(timestamp, tz=timezone.utc)
    try:
        return parse_dt(str(value))
    except ValueError:
        return None
