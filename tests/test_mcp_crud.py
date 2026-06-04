import tempfile
import shutil
from pathlib import Path

import pytest

from src.mcp_server.tools import (
    store_memory,
    list_memories,
    update_memory,
    delete_memory,
    recall_memories,
    export_memories,
)


@pytest.mark.asyncio
async def test_mcp_crud_lifecycle():
    tmp = tempfile.mkdtemp()
    try:
        storage = str(Path(tmp) / "memories")
        stored = await store_memory(
            "u1", "喜欢用 FastAPI", memory_type="user", storage_dir=storage, project_id="repo-a"
        )
        assert stored["stored"]
        mid = stored["memory_id"]

        listed = await list_memories("u1", storage_dir=storage, project_id="repo-a")
        assert listed["count"] >= 1

        updated = await update_memory(mid, "u1", content="喜欢用 FastAPI 和 Pydantic v2", storage_dir=storage)
        assert updated["updated"]

        recalled = await recall_memories("u1", "FastAPI", storage_dir=storage, project_id="repo-a")
        assert recalled["format"] == "memoryagent-sidecar-v2"
        assert "Pydantic" in recalled["prompt_block"] or recalled["count"] >= 1

        exported = await export_memories("u1", storage_dir=storage, project_id="repo-a")
        assert exported["format"] == "memoryagent-sidecar-v2"

        deleted = await delete_memory(mid, "u1", storage_dir=storage)
        assert deleted["deleted"]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
