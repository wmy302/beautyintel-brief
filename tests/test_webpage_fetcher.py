from app.db.models import Source
from app.sources.webpage_fetcher import WebpageFetcher


def test_sogou_link_is_resolved_to_article_url(monkeypatch):
    fetcher = WebpageFetcher()
    source = Source(name="搜狗新闻", source_type="webpage", url="https://news.sogou.com/news?query=美妆")

    monkeypatch.setattr(fetcher, "_resolve_sogou_link", lambda href, referer: "https://example.com/article")

    assert fetcher._article_url("https://news.sogou.com/link?url=token", source) == "https://example.com/article"


def test_sogou_unresolvable_link_is_skipped(monkeypatch):
    fetcher = WebpageFetcher()
    source = Source(name="搜狗新闻", source_type="webpage", url="https://news.sogou.com/news?query=美妆")

    monkeypatch.setattr(fetcher, "_resolve_sogou_link", lambda href, referer: None)

    assert fetcher._article_url("https://news.sogou.com/link?url=token", source) is None
