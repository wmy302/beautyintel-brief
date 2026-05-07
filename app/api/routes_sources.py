from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.serializers import source_to_dict
from app.db.models import Source
from app.db.session import get_db
from app.sources.manager import SourceManager

router = APIRouter()


@router.get("/sources")
def list_sources(db: Session = Depends(get_db)) -> list[dict]:
    SourceManager().sync_to_db(db)
    return [source_to_dict(s) for s in db.query(Source).order_by(Source.name).all()]


@router.post("/sources/reload")
def reload_sources(db: Session = Depends(get_db)) -> dict:
    sources = SourceManager().sync_to_db(db)
    return {"count": len(sources), "sources": [source_to_dict(s) for s in sources]}
