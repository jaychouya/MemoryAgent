import pytest

from src.memory.manager import MemoryManager
from src.memory.types import MemoryType


@pytest.mark.asyncio
async def test_active_stats_exclude_superseded(tmp_path):
    manager = MemoryManager(storage_dir=str(tmp_path / "memories"))
    old = await manager.store(
        content="我主要使用 Python 编程",
        memory_type=MemoryType.USER,
        user_id="u1",
    )
    await manager.store(
        content="我现在主要使用 Rust 编程",
        memory_type=MemoryType.USER,
        user_id="u1",
    )

    stats = manager.get_active_stats(user_id="u1")
    assert stats["total"] == 1
    assert stats["user"] == 1

    old_after = await manager.storage.retrieve(old.id)
    assert old_after.metadata.get("superseded_by")


def test_counts_by_type_per_user(tmp_path):
    from src.memory.index import MemoryIndex

    idx = MemoryIndex(str(tmp_path / "idx.db"))
    idx.add("a1", "A", "user", "u1")
    idx.add("a2", "B", "user", "u2")
    idx.add("f1", "C", "feedback", "u1")

    u1 = idx.counts_by_type(user_id="u1")
    assert u1.get("user") == 1
    assert u1.get("feedback") == 1
    assert sum(u1.values()) == 2


@pytest.mark.asyncio
async def test_list_archived_after_supersede(tmp_path):
    manager = MemoryManager(storage_dir=str(tmp_path / "memories"))
    old = await manager.store(
        content="我主要使用 Python 编程",
        memory_type=MemoryType.USER,
        user_id="u1",
    )
    await manager.store(
        content="我现在主要使用 Rust 编程",
        memory_type=MemoryType.USER,
        user_id="u1",
    )
    archived = await manager.list_archived_memories("u1")
    assert len(archived) == 1
    assert archived[0]["memory_id"] == old.id
    assert archived[0]["superseded_by"]


@pytest.mark.asyncio
async def test_user_update_resets_trust(tmp_path):
    from src.memory.trust import initial_trust

    manager = MemoryManager(storage_dir=str(tmp_path / "memories"))
    item = await manager.store(
        content="我喜欢深色主题",
        memory_type=MemoryType.USER,
        user_id="u1",
        metadata={"trust_score": 0.95},
    )
    await manager.update_memory(item.id, content="我喜欢浅色主题")
    after = await manager.storage.retrieve(item.id)
    assert after.metadata.get("user_corrected_at")
    assert after.metadata.get("trust_score") == initial_trust("user")
