import calendar
from datetime import datetime, timezone

import feedparser
from bs4 import BeautifulSoup

from app.core.time import utc_now
from app.db.models import NewsItem, Source


class RSSFetcher:
    def fetch(self, source: Source) -> list[NewsItem]:
        feed = feedparser.parse(source.url, request_headers={"User-Agent": "BeautyIntelBrief/0.1 (+compliant RSS reader)"})
        items: list[NewsItem] = []
        for entry in feed.entries[:30]:
            published_at = None
            if getattr(entry, "published_parsed", None):
                published_at = datetime.fromtimestamp(calendar.timegm(entry.published_parsed), tz=timezone.utc)
            summary = _html_to_text(getattr(entry, "summary", ""))
            items.append(
                NewsItem(
                    source_id=source.id,
                    source_name=source.name,
                    url=getattr(entry, "link", ""),
                    title=getattr(entry, "title", ""),
                    raw_excerpt=summary,
                    content_text=summary,
                    published_at=published_at,
                    fetched_at=utc_now(),
                    language=source.language,
                    country_or_region=source.country_or_region,
                    category=source.category,
                )
            )
        return items


def _html_to_text(value: str) -> str:
    if not value:
        return ""
    return " ".join(BeautifulSoup(value, "html.parser").get_text(" ").split())
