import pytest

from src.memory.manager import MemoryManager
from src.memory.types import MemoryType


@pytest.mark.asyncio
async def test_store_auto_supersedes_old_preference(tmp_path):
    manager = MemoryManager(storage_dir=str(tmp_path / "memories"))
    old = await manager.store(
        content="我主要使用 Python 编程",
        memory_type=MemoryType.USER,
        user_id="u1",
    )

    new = await manager.store(
        content="我现在主要使用 Rust 编程",
        memory_type=MemoryType.USER,
        user_id="u1",
    )

    old_after = await manager.storage.retrieve(old.id)
    results = await manager.retrieve("主要使用 编程", user_id="u1")

    assert old_after.metadata["superseded_by"] == new.id
    assert old_after.metadata["valid_until"]
    assert old_after.metadata["conflict_reason"]
    assert all(r["memory_id"] != old.id for r in results)
    assert any(r["memory_id"] == new.id for r in results)
    assert await manager.count_memories("u1") == 1


@pytest.mark.asyncio
async def test_store_does_not_supersede_different_user(tmp_path):
    manager = MemoryManager(storage_dir=str(tmp_path / "memories"))
    old = await manager.store(
        content="我主要使用 Python 编程",
        memory_type=MemoryType.USER,
        user_id="u1",
    )

    await manager.store(
        content="我现在主要使用 Rust 编程",
        memory_type=MemoryType.USER,
        user_id="u2",
    )

    old_after = await manager.storage.retrieve(old.id)
    assert "superseded_by" not in old_after.metadata
