import json

from app.db.models import DailyReport, NewsItem, Source


def source_to_dict(source: Source) -> dict:
    return {
        "id": source.id,
        "name": source.name,
        "source_type": source.source_type,
        "url": source.url,
        "homepage_url": source.homepage_url,
        "language": source.language,
        "country_or_region": source.country_or_region,
        "category": source.category,
        "credibility_level": source.credibility_level,
        "enabled": source.enabled,
        "fetch_interval_minutes": source.fetch_interval_minutes,
        "tags": _json(source.tags),
        "notes": source.notes,
    }


def item_to_dict(item: NewsItem) -> dict:
    return {
        "id": item.id,
        "title": item.title,
        "source_name": item.source_name,
        "url": item.url,
        "published_at": item.published_at.isoformat() if item.published_at else None,
        "summary_zh": item.summary_zh,
        "category": item.category,
        "tags": _json(item.tags_json),
        "related_brands": _json(item.related_brands_json),
        "related_platforms": _json(item.related_platforms_json),
        "risk_level": item.risk_level,
        "risk_reason": item.risk_reason,
        "importance_level": item.importance_level,
        "final_score": item.final_score,
        "why_it_matters": item.why_it_matters,
        "action_recommendation": item.action_recommendation,
        "status": item.status,
    }


def report_to_dict(report: DailyReport, include_content: bool = False) -> dict:
    data = {
        "id": report.id,
        "report_date": report.report_date.isoformat(),
        "title": report.title,
        "generated_at": report.generated_at.isoformat(),
        "delivery_status": report.delivery_status,
        "stats": _json(report.stats_json),
    }
    if include_content:
        data["markdown_content"] = report.markdown_content
        data["html_content"] = report.html_content
    return data


def _json(value: str):
    try:
        return json.loads(value or "[]")
    except json.JSONDecodeError:
        return []

