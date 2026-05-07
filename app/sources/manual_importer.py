import csv
from pathlib import Path

from app.core.config import root_path
from app.core.time import utc_now
from app.db.models import NewsItem, Source
from app.util import dumps, parse_dt


class ManualCSVImporter:
    def import_file(self, source: Source) -> list[NewsItem]:
        path = Path(source.url)
        if not path.is_absolute():
            path = root_path(str(path))
        items: list[NewsItem] = []
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                source_name = row.get("source_name") or source.name
                item = NewsItem(
                    source_id=source.id,
                    source_name=source_name,
                    url=row.get("url", ""),
                    title=row.get("title", "").strip(),
                    published_at=parse_dt(row.get("published_at")),
                    fetched_at=utc_now(),
                    language=source.language,
                    country_or_region=source.country_or_region,
                    raw_excerpt=row.get("raw_excerpt", ""),
                    content_text=row.get("content_text", "") or row.get("raw_excerpt", ""),
                    category=row.get("category") or source.category,
                    tags_json=dumps(_split(row.get("tags", ""))),
                    related_brands_json=dumps(_split(row.get("related_brands", ""))),
                    related_platforms_json=dumps(_split(row.get("related_platforms", ""))),
                    status="new",
                )
                if item.title:
                    items.append(item)
        return items


def _split(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in value.replace("，", ",").split(",") if part.strip()]
