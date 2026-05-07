import html
import json
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session
from zoneinfo import ZoneInfo

from app.core.config import root_path
from app.core.time import to_local, utc_now
from app.db.models import DailyReport, NewsItem, Source
from app.util import dumps, loads_list


class ReportGenerator:
    def __init__(self) -> None:
        template_dir = root_path("app", "reports", "templates")
        self.env = Environment(loader=FileSystemLoader(template_dir), autoescape=select_autoescape())

    def generate(self, db: Session, report_date: date, dry_run: bool = False, since: datetime | None = None) -> DailyReport:
        query = db.query(NewsItem).filter(
            NewsItem.is_duplicate.is_(False),
            NewsItem.status.in_(["processed", "included_in_report"]),
        )
        if since is not None:
            query = query.filter(NewsItem.fetched_at >= since)
            window_start, window_end = self._brief_window(report_date)
            query = query.filter(
                or_(
                    and_(NewsItem.published_at.is_not(None), NewsItem.published_at >= window_start, NewsItem.published_at < window_end),
                    and_(NewsItem.published_at.is_(None), NewsItem.fetched_at >= since),
                )
            )
        items = query.order_by(NewsItem.final_score.desc(), NewsItem.published_at.desc().nullslast()).all()
        context = self._context(db, items, report_date)
        md = self.env.get_template("daily_brief.md.j2").render(**context)
        html_content = self.env.get_template("daily_brief.html.j2").render(**context)
        report = DailyReport(
            report_date=report_date,
            timezone=context["timezone"],
            title=context["title"],
            markdown_content=md,
            html_content=html_content,
            top_items_json=dumps([i["id"] for i in context["top_items"]]),
            risk_items_json=dumps([i["id"] for i in context["risk_items"]]),
            opportunity_items_json=dumps([i["id"] for i in context["opportunity_items"]]),
            stats_json=dumps(context["stats"]),
        )
        if not dry_run:
            report_dir = root_path("data", "reports")
            report_dir.mkdir(parents=True, exist_ok=True)
            Path(report_dir, f"beautyintel_brief_{report_date}.md").write_text(md, encoding="utf-8")
            Path(report_dir, f"beautyintel_brief_{report_date}.html").write_text(html_content, encoding="utf-8")
            db.add(report)
            for item in items:
                item.status = "included_in_report"
            db.commit()
            db.refresh(report)
        return report

    def _brief_window(self, report_date: date) -> tuple[datetime, datetime]:
        tz = ZoneInfo("Asia/Shanghai")
        start_local = datetime.combine(report_date - timedelta(days=1), time.min, tzinfo=tz)
        end_local = datetime.combine(report_date, time.min, tzinfo=tz)
        return start_local.astimezone(ZoneInfo("UTC")), end_local.astimezone(ZoneInfo("UTC"))

    def _context(self, db: Session, items: list[NewsItem], report_date: date) -> dict[str, Any]:
        view = [self._view(item) for item in items]
        risk = [i for i in view if i["risk_level"] in {"red", "orange", "yellow"}]
        opportunities = [i for i in view if i["category"] in {"social_trend", "competitor", "product_ingredient", "ecommerce_channel"}][:6]
        actions = self._actions(view)
        stats = {
            "source_count": db.query(Source).filter(Source.enabled.is_(True)).count(),
            "new_item_count": len(view),
            "included_item_count": len(view),
            "red_risk_count": len([i for i in view if i["risk_level"] == "red"]),
        }
        return {
            "title": f"美妆早报｜{report_date}",
            "report_date": report_date.isoformat(),
            "timezone": "Asia/Shanghai",
            "generated_at": to_local(utc_now()),
            "stats": stats,
            "top_items": view[:3],
            "risk_items": risk,
            "opportunity_items": opportunities,
            "competitor_items": [i for i in view if i["category"] == "competitor"],
            "regulation_items": [i for i in view if i["category"] == "regulation"],
            "product_ingredient_items": [i for i in view if i["category"] == "product_ingredient"],
            "ecommerce_channel_items": [i for i in view if i["category"] == "ecommerce_channel"],
            "social_trend_items": [i for i in view if i["category"] == "social_trend"],
            "other_items": [i for i in view if i["category"] not in {"competitor", "regulation", "product_ingredient", "ecommerce_channel", "social_trend"}],
            "recommended_actions": actions,
        }

    def _view(self, item: NewsItem) -> dict[str, Any]:
        return {
            "id": item.id,
            "title": item.title,
            "source_name": item.source_name,
            "published_at": to_local(item.published_at),
            "importance_level": item.importance_level,
            "summary_zh": item.summary_zh,
            "why_it_matters": item.why_it_matters,
            "action_recommendation": item.action_recommendation,
            "url": item.url,
            "risk_level": item.risk_level,
            "risk_reason": item.risk_reason,
            "affected_team": "、".join(loads_list(item.affected_team_json)),
            "tags": "、".join(loads_list(item.tags_json)),
            "related_brands": "、".join(loads_list(item.related_brands_json)),
            "related_ingredients": "、".join(loads_list(item.related_ingredients_json)),
            "related_platforms": "、".join(loads_list(item.related_platforms_json)),
            "category": item.category,
            "final_score": item.final_score,
        }

    def _actions(self, items: list[dict[str, Any]]) -> list[str]:
        actions = []
        if any(i["category"] == "social_trend" for i in items):
            actions.append("【市场】围绕高频社媒热词整理 3 条小红书内容选题，并观察互动反馈。")
        if any(i["category"] == "regulation" for i in items):
            actions.append("【合规】复核防晒、美白、修护等功效宣称和页面标签表达。")
        if any(i["category"] == "competitor" for i in items):
            actions.append("【电商】复盘核心竞品的价格机制、赠品组合和渠道节奏。")
        if any(i["category"] == "product_ingredient" for i in items):
            actions.append("【产品】将 PDRN、重组胶原蛋白等成分加入下周趋势讨论池。")
        return actions[:5] or ["【市场】将今日信息加入周会趋势观察池，并指定责任人跟进。"]

    def _markdownish_to_html(self, md: str) -> str:
        lines = []
        for raw in md.splitlines():
            line = html.escape(raw)
            if line.startswith("# "):
                lines.append(f"<h1>{line[2:]}</h1>")
            elif line.startswith("## "):
                lines.append(f"<h2>{line[3:]}</h2>")
            elif line.startswith("### "):
                lines.append(f"<h3>{line[4:]}</h3>")
            elif line.startswith("- "):
                lines.append(f"<li>{line[2:]}</li>")
            elif line.startswith("&gt;"):
                lines.append(f"<p class='meta'>{line}</p>")
            elif line.strip() == "---":
                lines.append("<hr>")
            elif line.strip():
                lines.append(f"<p>{line}</p>")
        return "\n".join(lines)
