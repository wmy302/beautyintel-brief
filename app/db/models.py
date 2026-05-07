from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.core.time import utc_now


class Base(DeclarativeBase):
    pass


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    source_type: Mapped[str] = mapped_column(String(40), index=True)
    url: Mapped[str] = mapped_column(Text, default="")
    homepage_url: Mapped[str] = mapped_column(Text, default="")
    language: Mapped[str] = mapped_column(String(20), default="zh")
    country_or_region: Mapped[str] = mapped_column(String(40), default="CN")
    category: Mapped[str] = mapped_column(String(80), default="other")
    credibility_level: Mapped[str] = mapped_column(String(40), default="manual")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    fetch_interval_minutes: Mapped[int] = mapped_column(Integer, default=1440)
    tags: Mapped[str] = mapped_column(Text, default="[]")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class NewsItem(Base):
    __tablename__ = "news_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    source_name: Mapped[str] = mapped_column(String(255), index=True)
    url: Mapped[str] = mapped_column(Text, default="")
    canonical_url: Mapped[str] = mapped_column(Text, default="")
    title: Mapped[str] = mapped_column(Text)
    subtitle: Mapped[str] = mapped_column(Text, default="")
    author: Mapped[str] = mapped_column(String(255), default="")
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    language: Mapped[str] = mapped_column(String(20), default="zh")
    country_or_region: Mapped[str] = mapped_column(String(40), default="CN")
    raw_excerpt: Mapped[str] = mapped_column(Text, default="")
    raw_content: Mapped[str] = mapped_column(Text, default="")
    content_text: Mapped[str] = mapped_column(Text, default="")
    summary_zh: Mapped[str] = mapped_column(Text, default="")
    key_points_json: Mapped[str] = mapped_column(Text, default="[]")
    category: Mapped[str] = mapped_column(String(80), default="other", index=True)
    subcategory: Mapped[str] = mapped_column(String(120), default="")
    tags_json: Mapped[str] = mapped_column(Text, default="[]")
    related_brands_json: Mapped[str] = mapped_column(Text, default="[]")
    related_products_json: Mapped[str] = mapped_column(Text, default="[]")
    related_ingredients_json: Mapped[str] = mapped_column(Text, default="[]")
    related_platforms_json: Mapped[str] = mapped_column(Text, default="[]")
    related_people_json: Mapped[str] = mapped_column(Text, default="[]")
    sentiment: Mapped[str] = mapped_column(String(20), default="unknown")
    risk_level: Mapped[str] = mapped_column(String(20), default="none", index=True)
    risk_reason: Mapped[str] = mapped_column(Text, default="")
    affected_team_json: Mapped[str] = mapped_column(Text, default="[]")
    importance_level: Mapped[str] = mapped_column(String(5), default="C", index=True)
    relevance_score: Mapped[float] = mapped_column(Float, default=0)
    impact_score: Mapped[float] = mapped_column(Float, default=0)
    urgency_score: Mapped[float] = mapped_column(Float, default=0)
    credibility_score: Mapped[float] = mapped_column(Float, default=0)
    final_score: Mapped[float] = mapped_column(Float, default=0, index=True)
    action_recommendation: Mapped[str] = mapped_column(Text, default="")
    why_it_matters: Mapped[str] = mapped_column(Text, default="")
    evidence: Mapped[str] = mapped_column(Text, default="")
    content_hash: Mapped[str] = mapped_column(String(64), default="", index=True)
    title_hash: Mapped[str] = mapped_column(String(64), default="", index=True)
    duplicate_group_id: Mapped[str] = mapped_column(String(64), default="")
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    status: Mapped[str] = mapped_column(String(40), default="new", index=True)
    error_message: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class DailyReport(Base):
    __tablename__ = "daily_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_date: Mapped[date] = mapped_column(Date, index=True)
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Shanghai")
    title: Mapped[str] = mapped_column(String(255))
    markdown_content: Mapped[str] = mapped_column(Text)
    html_content: Mapped[str] = mapped_column(Text)
    top_items_json: Mapped[str] = mapped_column(Text, default="[]")
    risk_items_json: Mapped[str] = mapped_column(Text, default="[]")
    opportunity_items_json: Mapped[str] = mapped_column(Text, default="[]")
    stats_json: Mapped[str] = mapped_column(Text, default="{}")
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivery_status: Mapped[str] = mapped_column(String(40), default="not_delivered")
    delivery_channels_json: Mapped[str] = mapped_column(Text, default="[]")

