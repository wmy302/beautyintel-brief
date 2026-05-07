from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.serializers import report_to_dict
from app.db.session import get_db
from app.ingestion.pipeline import IngestionPipeline
from app.reports.generator import ReportGenerator

router = APIRouter()


class GenerateReportRequest(BaseModel):
    report_date: date | None = None
    dry_run: bool = False


@router.post("/jobs/ingest")
def ingest(dry_run: bool = False, db: Session = Depends(get_db)) -> dict:
    return IngestionPipeline().run(db, dry_run=dry_run)


@router.post("/jobs/generate-report")
def generate_report(req: GenerateReportRequest, db: Session = Depends(get_db)) -> dict:
    report = ReportGenerator().generate(db, req.report_date or date.today(), dry_run=req.dry_run)
    return report_to_dict(report, include_content=True)

