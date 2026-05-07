from app.db.models import NewsItem
from app.util import dumps


class RuleBasedSummarizer:
    def summarize(self, item: NewsItem) -> NewsItem:
        text = item.content_text or item.raw_excerpt or item.title
        compact = " ".join(text.split())
        if not item.summary_zh:
            item.summary_zh = _clip(compact, 115)
        if not item.key_points_json or item.key_points_json == "[]":
            points = [p for p in [item.title, item.risk_reason, item.why_it_matters] if p][:3]
            item.key_points_json = dumps(points)
        if not item.evidence:
            item.evidence = f"依据标题、来源和正文摘要判断：{_clip(compact, 80)}"
        return item


def _clip(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"
