import json

from src.mcp_server.minimal_stdio import TOOLS, _register_handlers, _HANDLERS
import asyncio


def test_tools_registered():
    _register_handlers("/tmp/memories")
    assert "memory_recall" in _HANDLERS
    assert len(TOOLS) == 6


def test_handle_initialize():
    from src.mcp_server.minimal_stdio import _handle

    _register_handlers("/tmp/memories")
    resp = asyncio.run(
        _handle(
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            "/tmp/memories",
        )
    )
    assert resp["result"]["serverInfo"]["name"] == "memoryagent-sidecar"
