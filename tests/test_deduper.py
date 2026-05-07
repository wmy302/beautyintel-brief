from app.ingestion.deduper import canonicalize_url, content_hash, is_similar_title


def test_url_canonicalization_removes_tracking():
    assert canonicalize_url("http://Example.com/a/?utm_source=x&b=1").startswith("https://example.com/a?b=1")


def test_similar_title_detection():
    assert is_similar_title("重磅：竞品A推出屏障修护新品", "竞品A 推出 屏障修护 新品")


def test_content_hash_stable():
    assert content_hash("abc") == content_hash("abc")
    assert content_hash("abc") != content_hash("abcd")

