from app.db.models import NewsItem
from app.util import dumps


class RiskDetector:
    def detect(self, item: NewsItem) -> NewsItem:
        text = f"{item.title} {item.raw_excerpt} {item.content_text}"
        level = "none"
        reason = ""
        teams: list[str] = []

        red_terms = ["禁用原料", "不符合规定", "立案调查", "停售", "召回", "严重质量问题"]
        orange_terms = ["处罚", "虚假宣传", "夸大宣传", "投诉", "过敏", "平台规则", "抽检"]
        if any(term in text for term in red_terms):
            level = "red"
            reason = "命中监管或严重质量安全高风险词。"
            teams = ["合规", "法务", "PR", "电商", "管理层"]
        elif any(term in text for term in orange_terms):
            level = "orange"
            reason = "命中合规、舆情或平台规则关注词。"
            teams = ["合规", "PR", "电商"]
        elif item.category in {"competitor", "social_trend", "product_ingredient", "ecommerce_channel"}:
            level = "yellow"
            reason = "与竞品、趋势或渠道变化相关，建议持续观察。"
            teams = ["市场", "电商", "产品"]

        if "我们的品牌" in text and item.sentiment == "negative" and level not in {"red", "orange"}:
            level = "orange"
            reason = "涉及自身品牌负面反馈。"
            teams = ["PR", "客服", "合规"]

        item.risk_level = level
        item.risk_reason = reason
        item.affected_team_json = dumps(teams)
        return item

