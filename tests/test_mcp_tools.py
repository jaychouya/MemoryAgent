import tempfile
import shutil
from pathlib import Path

import pytest

from src.mcp_server.tools import recall_memories, store_memory, export_memories


@pytest.mark.asyncio
async def test_mcp_store_and_recall():
    tmp = tempfile.mkdtemp()
    try:
        storage = str(Path(tmp) / "memories")
        stored = await store_memory(
            "user_mcp",
            "用户喜欢 Rust",
            memory_type="user",
            storage_dir=storage,
        )
        assert stored["stored"] is True
        recalled = await recall_memories("user_mcp", "Rust 项目", limit=5, storage_dir=storage)
        assert recalled["count"] >= 1
        assert any("Rust" in (m.get("content") or "") for m in recalled["memories"])
        exported = await export_memories("user_mcp", query="Rust", storage_dir=storage)
        assert exported["format"] == "memoryagent-sidecar-v2"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
