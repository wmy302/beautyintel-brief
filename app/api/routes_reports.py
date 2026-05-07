from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.serializers import report_to_dict
from app.core.time import utc_now
from app.db.models import DailyReport
from app.db.session import get_db
from app.delivery import get_delivery_services
from app.ingestion.pipeline import IngestionPipeline
from app.reports.generator import ReportGenerator
from app.util import dumps

router = APIRouter()


class DeliverRequest(BaseModel):
    channels: list[str] | None = None
    dry_run: bool = True


@router.get("/reports")
def list_reports(db: Session = Depends(get_db)) -> list[dict]:
    reports = db.query(DailyReport).order_by(DailyReport.generated_at.desc()).all()
    return [report_to_dict(r) for r in reports]


@router.get("/reports/latest")
def latest_report(db: Session = Depends(get_db)) -> dict:
    report = db.query(DailyReport).order_by(DailyReport.generated_at.desc()).first()
    if not report:
        raise HTTPException(status_code=404, detail="report not found")
    return report_to_dict(report, include_content=True)


@router.get("/reports/latest/view", response_class=HTMLResponse)
def latest_report_view(db: Session = Depends(get_db)) -> HTMLResponse:
    report = db.query(DailyReport).order_by(DailyReport.generated_at.desc()).first()
    if not report:
        return _refresh_today_report(db)
    return HTMLResponse(report.html_content)


def _refresh_today_report(db: Session) -> HTMLResponse:
    started_at = utc_now()
    IngestionPipeline().run(db, dry_run=False)
    report = ReportGenerator().generate(db, date.today(), dry_run=False, since=started_at)
    return HTMLResponse(report.html_content)


@router.post("/reports/refresh-today", response_class=HTMLResponse)
def refresh_today_report(db: Session = Depends(get_db)) -> HTMLResponse:
    return _refresh_today_report(db)


@router.get("/reports/refresh-today", response_class=HTMLResponse)
def refresh_today_report_get(db: Session = Depends(get_db)) -> HTMLResponse:
    return _refresh_today_report(db)


@router.get("/reports/{report_id}")
def get_report(report_id: int, db: Session = Depends(get_db)) -> dict:
    report = db.get(DailyReport, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="report not found")
    return report_to_dict(report, include_content=True)


@router.get("/reports/{report_id}/view", response_class=HTMLResponse)
def get_report_view(report_id: int, db: Session = Depends(get_db)) -> HTMLResponse:
    report = db.get(DailyReport, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="report not found")
    return HTMLResponse(report.html_content)


@router.post("/reports/{report_id}/deliver")
def deliver_report(report_id: int, req: DeliverRequest, db: Session = Depends(get_db)) -> dict:
    report = db.get(DailyReport, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="report not found")
    results = [s.send(report.markdown_content, report.html_content, report.title, req.dry_run).__dict__ for s in get_delivery_services(req.channels)]
    report.delivery_status = "dry_run" if req.dry_run else "sent"
    report.delivered_at = utc_now()
    report.delivery_channels_json = dumps(results)
    db.commit()
    return {"results": results}


def generate_report_now(db: Session, report_date: date, dry_run: bool = False) -> DailyReport:
    return ReportGenerator().generate(db, report_date, dry_run=dry_run)
