from app.db.models import NewsItem
from app.util import dumps, load_yaml, loads_list


class RuleBasedClassifier:
    def __init__(self) -> None:
        self.brands = load_yaml("config/brands.yaml")
        self.keywords = load_yaml("config/keywords.yaml")

    def classify(self, item: NewsItem) -> NewsItem:
        text = f"{item.title} {item.raw_excerpt} {item.content_text}"
        tags = set(loads_list(item.tags_json))
        brands = set(loads_list(item.related_brands_json))
        platforms = set(loads_list(item.related_platforms_json))
        ingredients: set[str] = set()

        for word in self.keywords.get("risk_high", []):
            if word in text:
                tags.add(word)
        for word in self.keywords.get("categories", []):
            if word in text:
                tags.add(word)
        for word in self.keywords.get("claims", []):
            if word in text:
                tags.add(word)
        for word in self.keywords.get("ingredients", []):
            if word in text:
                ingredients.add(word)
                tags.add(word)
        for word in self.keywords.get("channels", []):
            if word in text:
                platforms.add(word)
                tags.add(word)

        own = self.brands.get("own_brand", {})
        for brand in [own.get("name", ""), *own.get("aliases", [])]:
            if brand and brand in text:
                brands.add(own.get("name", brand))
        for group in ("core_competitors", "watchlist_brands"):
            for brand_cfg in self.brands.get(group, []):
                aliases = [brand_cfg.get("name", ""), *brand_cfg.get("aliases", [])]
                if any(alias and alias in text for alias in aliases):
                    brands.add(brand_cfg["name"])

        platform_names = set(self.brands.get("platforms", [])) | set(self.keywords.get("channels", []))
        brands -= platform_names

        item.category = self._category(text, item.category, brands)
        item.subcategory = self._subcategory(text)
        item.sentiment = self._sentiment(text)
        item.tags_json = dumps(sorted(tags))
        item.related_brands_json = dumps(sorted(brands))
        item.related_platforms_json = dumps(sorted(platforms))
        item.related_ingredients_json = dumps(sorted(ingredients))
        if not item.why_it_matters:
            item.why_it_matters = self._why(item)
        if not item.action_recommendation:
            item.action_recommendation = self._action(item)
        return item

    def _category(self, text: str, current: str, brands: set[str]) -> str:
        text_lower = text.lower()
        if any(w in text for w in ["监管", "抽检", "不符合规定", "禁用原料", "处罚", "广告法", "备案", "标签"]):
            return "regulation"
        if current == "competitor" or any(b.startswith("竞品") for b in brands):
            if any(w in text for w in ["新品", "代言", "联名", "大促", "官宣", "快闪", "首发"]):
                return "competitor"
        if any(w in text for w in ["小红书", "种草", "测评", "热词", "话题", "避雷"]):
            return "social_trend"
        if any(w in text for w in ["天猫", "京东", "抖音", "直播间", "赠品", "价格", "大促", "电商"]):
            return "ecommerce_channel"
        if any(w in text_lower for w in ["launch", "introduces", "collection", "serum", "skincare", "skin care", "cosmetic", "beauty", "lip", "grooming"]):
            return "product_ingredient"
        if any(w in text for w in ["新品", "成分", "功效", "PDRN", "修护", "防晒", "精华"]):
            return "competitor" if any(b.startswith("竞品") for b in brands) else "product_ingredient"
        if any(b.startswith("竞品") for b in brands):
            return "competitor"
        if any(w in text for w in ["代言", "明星", "达人", "KOL", "KOC"]):
            return "kol_celebrity"
        if any(w in text for w in ["吐槽", "投诉", "口碑", "争议"]):
            return "consumer_sentiment"
        return "market_overview" if current == "industry_trend" else current if current else "other"

    def _subcategory(self, text: str) -> str:
        for word in ["抽检", "平台规则", "新品发布", "成分趋势", "社媒热词", "直播玩法", "消费者反馈"]:
            if word in text:
                return word
        return "常规观察"

    def _sentiment(self, text: str) -> str:
        if any(w in text for w in ["吐槽", "投诉", "处罚", "不符合规定", "召回", "停售", "翻车", "负面"]):
            return "negative"
        if any(w in text for w in ["增长", "升温", "机会", "新品", "官宣"]):
            return "positive"
        return "neutral"

    def _why(self, item: NewsItem) -> str:
        if item.category == "regulation":
            return "涉及合规和宣称边界，可能影响产品页面、广告素材和客服口径。"
        if item.category == "competitor":
            return "竞品动作会影响品类声量、投放节奏和内容差异化。"
        if item.category == "social_trend":
            return "社媒热词可转化为内容选题、达人沟通方向和搜索关键词。"
        if item.category == "ecommerce_channel":
            return "渠道规则或价格变化会影响直播间转化、赠品机制和货盘节奏。"
        return "该信息可作为品牌市场部的趋势观察和周会讨论素材。"

    def _action(self, item: NewsItem) -> str:
        if item.category == "regulation":
            return "请合规团队复核相关产品页面、广告素材和功效宣称。"
        if item.category == "competitor":
            return "请市场和电商团队整理竞品卖点、价格和渠道动作，纳入本周复盘。"
        if item.category == "social_trend":
            return "请内容团队围绕该热词产出 3 条小红书选题并验证互动反馈。"
        if item.category == "ecommerce_channel":
            return "请电商团队检查直播间展示、赠品和价格机制是否需要调整。"
        return "请相关团队加入趋势观察池，并在周会判断是否跟进。"
