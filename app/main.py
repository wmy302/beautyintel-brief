from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.api.routes_health import router as health_router
from app.api.routes_items import router as items_router
from app.api.routes_jobs import router as jobs_router
from app.api.routes_reports import router as reports_router
from app.api.routes_sources import router as sources_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.base import init_db
from app.jobs.daily_brief_job import run_daily_brief
from app.jobs.scheduler import start_background_scheduler

configure_logging()
app = FastAPI(title="BeautyIntel Brief", version="0.1.0")
background_scheduler = None
app.include_router(health_router)
app.include_router(sources_router)
app.include_router(items_router)
app.include_router(reports_router)
app.include_router(jobs_router)


@app.on_event("startup")
def startup() -> None:
    global background_scheduler
    init_db()
    settings = get_settings()
    if settings.refresh_on_startup:
        run_daily_brief(dry_run=True)
    if settings.enable_background_scheduler and background_scheduler is None:
        background_scheduler = start_background_scheduler()


@app.on_event("shutdown")
def shutdown() -> None:
    global background_scheduler
    if background_scheduler is not None:
        background_scheduler.shutdown(wait=False)
        background_scheduler = None


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/reports/latest/view")
