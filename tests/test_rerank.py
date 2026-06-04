import pytest

from src.memory.rerank import rerank_candidates


@pytest.mark.asyncio
async def test_rerank_prefers_matching_content():
    candidates = [
        {"content": "用户喜欢猫", "score": 0.9},
        {"content": "用户常用 Python asyncio 开发", "score": 0.3},
        {"content": "周末打高尔夫", "score": 0.8},
    ]
    out = await rerank_candidates("Python 异步", candidates, top_k=1)
    assert len(out) == 1
    assert "Python" in out[0]["content"]
