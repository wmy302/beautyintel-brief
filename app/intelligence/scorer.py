from app.db.models import NewsItem, Source
from app.util import load_yaml, loads_list


CREDIBILITY = {
    "official": 100,
    "financial_report": 95,
    "tier1_media": 85,
    "mainstream_media": 85,
    "industry_media": 75,
    "authorized_api": 70,
    "platform_data": 70,
    "manual": 60,
    "social_signal": 50,
    "rumor": 20,
}


class ScoringEngine:
    def __init__(self) -> None:
        self.brands = load_yaml("config/brands.yaml")

    def score(self, item: NewsItem, source: Source | None = None) -> NewsItem:
        text = f"{item.title} {item.raw_excerpt} {item.content_text}"
        related_brands = loads_list(item.related_brands_json)
        tags = loads_list(item.tags_json)
        platforms = loads_list(item.related_platforms_json)

        relevance = 10
        own = self.brands.get("own_brand", {})
        if own.get("name") in related_brands or any(alias in text for alias in own.get("aliases", [])):
            relevance += 40
        core_names = [b["name"] for b in self.brands.get("core_competitors", [])]
        if any(name in related_brands or name in text for name in core_names):
            relevance += 30
        if any(tag in own.get("categories", []) for tag in tags):
            relevance += 20
        if platforms:
            relevance += 15
        if any(tag in own.get("key_claims", []) for tag in tags):
            relevance += 10

        cred_level = source.credibility_level if source else "manual"
        credibility = 100 if "国家药监局" in item.source_name else CREDIBILITY.get(cred_level, 60)
        impact = self._impact(item, credibility, text)
        urgency = self._urgency(item, text)
        final = min(100, relevance) * 0.40 + impact * 0.25 + urgency * 0.20 + credibility * 0.15

        if "禁用原料" in text:
            final = max(final, 90)
        if "不符合规定" in text:
            final = max(final, 85)
        if "抽检" in text:
            final = max(final, 80)
        if any(name in text for name in core_names) and any(w in text for w in ["新品", "代言", "联名", "大促"]):
            final = max(final, 75)

        item.relevance_score = min(100, relevance)
        item.impact_score = impact
        item.urgency_score = urgency
        item.credibility_score = credibility
        item.final_score = round(min(100, final), 2)
        item.importance_level = "S" if item.final_score >= 85 else "A" if item.final_score >= 70 else "B" if item.final_score >= 50 else "C"
        return item

    def _impact(self, item: NewsItem, credibility: float, text: str) -> float:
        if item.category == "regulation" and credibility >= 90:
            return 95
        if any(w in text for w in ["财报", "并购"]):
            return 85
        if item.category == "competitor":
            return 78
        if item.category == "ecommerce_channel":
            return 75
        if item.category == "social_trend":
            return 55
        return 50

    def _urgency(self, item: NewsItem, text: str) -> float:
        if any(w in text for w in ["处罚", "抽检", "不符合规定", "禁用原料", "召回"]):
            return 95
        if item.category == "competitor" and any(w in text for w in ["当天", "新品", "代言", "联名", "大促"]):
            return 82
        if item.risk_level in {"red", "orange"}:
            return 85
        if item.category == "social_trend":
            return 60
        return 40
