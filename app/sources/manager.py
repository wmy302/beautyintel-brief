import logging

from sqlalchemy.orm import Session

from app.db.models import Source
from app.util import dumps, load_yaml

logger = logging.getLogger(__name__)


class SourceManager:
    def __init__(self, config_path: str = "config/sources.yaml") -> None:
        self.config_path = config_path

    def load_sources(self) -> list[dict]:
        return load_yaml(self.config_path).get("sources", [])

    def sync_to_db(self, db: Session) -> list[Source]:
        records: list[Source] = []
        for cfg in self.load_sources():
            source = db.query(Source).filter(Source.name == cfg["name"]).one_or_none()
            if source is None:
                source = Source(name=cfg["name"], source_type=cfg["source_type"])
                db.add(source)
            for key in [
                "source_type",
                "url",
                "homepage_url",
                "language",
                "country_or_region",
                "category",
                "credibility_level",
                "enabled",
                "fetch_interval_minutes",
                "notes",
            ]:
                setattr(source, key, cfg.get(key, getattr(source, key, "")))
            source.tags = dumps(cfg.get("tags", []))
            records.append(source)
        db.commit()
        logger.info("sources_synced count=%s", len(records))
        return records

    def enabled_sources(self, db: Session) -> list[Source]:
        return db.query(Source).filter(Source.enabled.is_(True)).all()

