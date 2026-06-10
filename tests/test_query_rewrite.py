from src.memory.query_rewrite import rewrite_query_for_retrieval
from src.memory.write_pipeline import should_use_llm_extract
from src.utils.config import settings


def test_rewrite_short_query_unchanged():
    q = "我喜欢 Python"
    out, rew = rewrite_query_for_retrieval(q)
    assert out == q
    assert rew is False


def test_rewrite_long_query_shortens():
    long = "请帮我看一下 " + "前面废话 " * 20 + "最后真正的问题：Kotlin 协程怎么取消？"
    out, rew = rewrite_query_for_retrieval(long, max_len=80)
    assert rew is True
    assert len(out) <= 80
    assert "Kotlin" in out or "协程" in out


def test_should_use_llm_extract_threshold():
    assert should_use_llm_extract("短", "短") is False
    assert should_use_llm_extract("x" * 300, "y" * 200) is True


def test_llm_extract_respects_min_chars(monkeypatch):
    monkeypatch.setattr(settings, "MEMORY_EXTRACT_LLM_MIN_CHARS", 1000)
    assert should_use_llm_extract("x" * 200, "y" * 200) is False
    assert should_use_llm_extract("x" * 600, "y" * 600) is True
