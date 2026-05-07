from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import get_settings
from app.jobs.daily_brief_job import run_daily_brief


def _cron(expr: str) -> CronTrigger:
    minute, hour, day, month, day_of_week = expr.split()
    return CronTrigger(minute=minute, hour=hour, day=day, month=month, day_of_week=day_of_week, timezone=get_settings().brief_timezone)


def run_scheduler() -> None:
    settings = get_settings()
    scheduler = BlockingScheduler(timezone=settings.brief_timezone)
    scheduler.add_job(lambda: run_daily_brief(dry_run=True), _cron(settings.deliver_cron), id="daily_brief")
    scheduler.start()


def start_background_scheduler() -> BackgroundScheduler:
    settings = get_settings()
    scheduler = BackgroundScheduler(timezone=settings.brief_timezone)
    scheduler.add_job(lambda: run_daily_brief(dry_run=True), _cron(settings.deliver_cron), id="daily_brief", replace_existing=True)
    scheduler.start()
    return scheduler
