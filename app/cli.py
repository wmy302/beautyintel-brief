import argparse
from datetime import date, datetime

from app.core.logging import configure_logging
from app.db.base import init_db
from app.db.models import DailyReport
from app.db.session import SessionLocal
from app.delivery import get_delivery_services
from app.ingestion.pipeline import IngestionPipeline
from app.jobs.daily_brief_job import run_daily_brief
from app.jobs.scheduler import run_scheduler
from app.reports.generator import ReportGenerator


def main() -> None:
    configure_logging()
    parser = argparse.ArgumentParser(prog="beautyintel-brief")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init-db")
    ingest = sub.add_parser("ingest")
    ingest.add_argument("--dry-run", action="store_true")
    brief = sub.add_parser("generate-report")
    brief.add_argument("--date")
    brief.add_argument("--today", action="store_true")
    deliver = sub.add_parser("deliver")
    deliver.add_argument("--latest", action="store_true")
    deliver.add_argument("--dry-run", action="store_true")
    sub.add_parser("run-scheduler")
    refresh = sub.add_parser("refresh-today")
    refresh.add_argument("--dry-run-delivery", action="store_true")
    args = parser.parse_args()

    if args.command == "init-db":
        init_db()
        print("database initialized")
        return
    if args.command == "run-scheduler":
        run_scheduler()
        return
    if args.command == "refresh-today":
        print(run_daily_brief(dry_run=args.dry_run_delivery))
        return

    init_db()
    db = SessionLocal()
    try:
        if args.command == "ingest":
            print(IngestionPipeline().run(db, dry_run=args.dry_run))
        elif args.command == "generate-report":
            report_date = date.today() if args.today or not args.date else datetime.strptime(args.date, "%Y-%m-%d").date()
            report = ReportGenerator().generate(db, report_date, dry_run=False)
            print(f"generated report {report.id}: data/reports/beautyintel_brief_{report_date}.md")
        elif args.command == "deliver":
            report = db.query(DailyReport).order_by(DailyReport.generated_at.desc()).first()
            if not report:
                raise SystemExit("no report found")
            results = [s.send(report.markdown_content, report.html_content, report.title, dry_run=args.dry_run).__dict__ for s in get_delivery_services()]
            print(results)
    finally:
        db.close()


if __name__ == "__main__":
    main()
