from app.db.models import NewsItem


def normalize_item(item: NewsItem) -> NewsItem:
    item.title = " ".join(item.title.split())
    item.content_text = " ".join((item.content_text or item.raw_excerpt or "").split())
    return item
