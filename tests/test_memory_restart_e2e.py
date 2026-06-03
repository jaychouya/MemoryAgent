import tempfile
import shutil
from pathlib import Path

import pytest

from src.memory.manager import MemoryManager
from src.memory.persistent_vector import PersistentVectorStore


@pytest.mark.asyncio
async def test_vectors_survive_manager_restart():
    tmp = tempfile.mkdtemp()
    storage = str(Path(tmp) / "memories")
    try:
        mgr1 = MemoryManager(storage_dir=storage)
        await mgr1.store_user_preference("用户喜欢 Rust 语言", user_id="restart_user")
        assert mgr1.vector_store.size() >= 1

        mgr2 = MemoryManager(storage_dir=storage)
        assert mgr2.vector_store.size() >= 1
        results = await mgr2.retrieve(
            query="用什么语言",
            user_id="restart_user",
            top_k=5,
        )
        text = " ".join(r.get("content", "") for r in results)
        assert "Rust" in text
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
