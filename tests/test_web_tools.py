import pytest

from src.agent.tools.base import ToolResult
from src.agent.tools import builtin
from src.agent.tools.builtin import WebFetchTool


@pytest.mark.asyncio
async def test_web_fetch_403_returns_fallback_content(monkeypatch):
    class Response:
        status_code = 403

        def raise_for_status(self):
            raise AssertionError("raise_for_status should not be called for 403")

    class Client:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def get(self, *args, **kwargs):
            return Response()

    async def fake_search(self, query, top_k=5, **kwargs):
        return ToolResult(success=True, content="联网搜索结果：\n\n1. fallback")

    monkeypatch.setattr(builtin.httpx, "AsyncClient", Client)
    monkeypatch.setattr(builtin.WebSearchTool, "execute", fake_search)

    result = await WebFetchTool().execute("https://wenku.baidu.com/view/x.html")

    assert result.success is True
    assert result.error is None
    assert "403 Forbidden" in result.content
    assert "联网搜索结果" in result.content
    assert result.metadata["fallback"] == "web_search"
