from datetime import date

from app.db.session import SessionLocal
from app.delivery import get_delivery_services
from app.ingestion.pipeline import IngestionPipeline
from app.core.time import utc_now
from app.reports.generator import ReportGenerator


def run_daily_brief(dry_run: bool = False) -> dict:
    db = SessionLocal()
    try:
        started_at = utc_now()
        ingest_result = IngestionPipeline().run(db, dry_run=False)
        report = ReportGenerator().generate(db, date.today(), dry_run=False, since=started_at, item_ids=ingest_result.get("item_ids", []))
        delivery = [s.send(report.markdown_content, report.html_content, report.title, dry_run=dry_run).__dict__ for s in get_delivery_services()]
        return {"ingest": ingest_result, "report_id": report.id, "delivery": delivery}
    finally:
        db.close()
