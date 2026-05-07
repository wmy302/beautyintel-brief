from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, NewsItem, Source
from app.reports.generator import ReportGenerator


def test_report_generator_markdown_contains_sections():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    db.add(Source(name="demo", source_type="manual_csv", credibility_level="manual"))
    for idx, category in enumerate(["regulation", "competitor", "social_trend"], start=1):
        db.add(
            NewsItem(
                source_name="demo",
                title=f"测试新闻{idx}",
                url="https://example.com",
                category=category,
                summary_zh="这是一条用于测试报告生成的摘要。",
                why_it_matters="用于验证报告结构完整。",
                action_recommendation="请相关团队复核并跟进。",
                risk_level="red" if category == "regulation" else "yellow",
                risk_reason="测试风险",
                importance_level="S",
                final_score=90 - idx,
                status="processed",
            )
        )
    db.commit()
    report = ReportGenerator().generate(db, date(2026, 4, 30), dry_run=True)
    assert "今日 3 条必读" in report.markdown_content
    assert "今日风险预警" in report.markdown_content
    assert "今日建议动作" in report.markdown_content
