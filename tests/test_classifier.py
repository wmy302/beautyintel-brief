from app.db.models import NewsItem
from app.intelligence.classifier import RuleBasedClassifier
from app.intelligence.risk_detector import RiskDetector


def classify(title: str, content: str = "") -> NewsItem:
    item = NewsItem(title=title, source_name="test", content_text=content)
    RuleBasedClassifier().classify(item)
    RiskDetector().detect(item)
    return item


def test_banned_ingredient_is_regulation_high_risk():
    item = classify("监管通告涉及禁用原料和化妆品抽检")
    assert item.category == "regulation"
    assert item.risk_level in {"red", "orange"}


def test_competitor_new_product():
    item = classify("竞品A推出屏障修护新品系列")
    assert item.category in {"competitor", "product_ingredient"}


def test_xiaohongshu_trend():
    item = classify("小红书出现换季屏障修护热词")
    assert item.category == "social_trend"

