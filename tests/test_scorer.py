from app.db.models import NewsItem, Source
from app.intelligence.classifier import RuleBasedClassifier
from app.intelligence.risk_detector import RiskDetector
from app.intelligence.scorer import ScoringEngine


def process(title: str, source: Source) -> NewsItem:
    item = NewsItem(title=title, source_name=source.name, content_text=title)
    RuleBasedClassifier().classify(item)
    RiskDetector().detect(item)
    ScoringEngine().score(item, source)
    return item


def test_official_credibility_score():
    source = Source(name="国家药监局 - 化妆品抽检通告", source_type="manual_csv", credibility_level="official")
    item = process("国家监管部门发布化妆品抽检相关通告", source)
    assert item.credibility_score == 100


def test_banned_ingredient_score_floor():
    source = Source(name="国家药监局", source_type="manual_csv", credibility_level="official")
    item = process("通告涉及禁用原料", source)
    assert item.final_score >= 90


def test_core_competitor_new_product_score_floor():
    source = Source(name="竞品监测", source_type="manual_csv", credibility_level="manual")
    item = process("竞品A推出屏障修护新品系列", source)
    assert item.final_score >= 75

