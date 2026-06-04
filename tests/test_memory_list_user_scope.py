import tempfile
import shutil
from pathlib import Path

import pytest

from src.memory.manager import MemoryManager
from src.memory.types import MemoryType
from src.memory.service import reset_shared_memory_manager, get_shared_memory_manager


@pytest.mark.asyncio
async def test_list_memories_scoped_by_user_id():
    tmp = tempfile.mkdtemp()
    try:
        reset_shared_memory_manager()
        storage = str(Path(tmp) / "memories")
        mgr_a = MemoryManager(storage_dir=storage)
        mgr_b = MemoryManager(storage_dir=storage)
        await mgr_a.store_user_preference("用户A喜欢Python", user_id="user_a")
        await mgr_b.store_user_preference("用户B喜欢Java", user_id="user_b")

        from httpx import ASGITransport, AsyncClient
        from src.backend.main import app

        reset_shared_memory_manager()
        import src.memory.service as svc

        svc._manager = MemoryManager(storage_dir=storage)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            ra = await client.get("/api/memories", params={"user_id": "user_a"})
            rb = await client.get("/api/memories", params={"user_id": "user_b"})

        assert ra.status_code == 200
        assert rb.status_code == 200
        ca = " ".join(m["content"] for m in ra.json())
        cb = " ".join(m["content"] for m in rb.json())
        assert "Python" in ca
        assert "Java" in cb
        assert "Java" not in ca
        assert "Python" not in cb
    finally:
        reset_shared_memory_manager()
        shutil.rmtree(tmp, ignore_errors=True)
