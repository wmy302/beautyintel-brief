from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.serializers import item_to_dict
from app.db.models import NewsItem
from app.db.session import get_db

router = APIRouter()


@router.get("/items")
def list_items(
    category: str | None = None,
    risk_level: str | None = None,
    importance_level: str | None = None,
    source_name: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    q: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[dict]:
    query = db.query(NewsItem)
    if category:
        query = query.filter(NewsItem.category == category)
    if risk_level:
        query = query.filter(NewsItem.risk_level == risk_level)
    if importance_level:
        query = query.filter(NewsItem.importance_level == importance_level)
    if source_name:
        query = query.filter(NewsItem.source_name == source_name)
    if date_from:
        query = query.filter(NewsItem.published_at >= date_from)
    if date_to:
        query = query.filter(NewsItem.published_at <= date_to)
    if q:
        query = query.filter(NewsItem.title.contains(q) | NewsItem.content_text.contains(q))
    return [item_to_dict(i) for i in query.order_by(NewsItem.final_score.desc()).limit(200)]


@router.get("/items/{item_id}")
def get_item(item_id: int, db: Session = Depends(get_db)) -> dict:
    item = db.get(NewsItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="item not found")
    return item_to_dict(item)

