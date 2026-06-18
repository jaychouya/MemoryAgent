from src.memory.trust import (
    initial_trust,
    boost_on_recall,
    apply_trust_to_results,
    effective_rank_score,
)
from src.memory.recall_health import diagnose_recall
from src.memory.inject import format_mandatory_memory_block
from src.memory.authority import AUTHORITY_PREAMBLE
from src.memory.write_pipeline import persist_turn_memories
from unittest.mock import AsyncMock, MagicMock

import pytest


def test_initial_trust_by_type():
    assert initial_trust("feedback") > initial_trust("reference")


def test_boost_on_recall_caps_at_one():
    assert boost_on_recall(0.98) == 1.0


def test_apply_trust_reorders_results():
    rows = [
        {"memory_id": "a", "score": 0.55, "trust_score": 0.15, "memory_type": "reference"},
        {"memory_id": "b", "score": 0.5, "trust_score": 0.95, "memory_type": "feedback"},
    ]
    out = apply_trust_to_results(rows)
    assert out[0]["memory_id"] == "b"


def test_effective_rank_score_decays_old():
    young = effective_rank_score(0.8, 0.8, age_days=10)
    old = effective_rank_score(0.8, 0.8, age_days=120)
    assert young > old


def test_diagnose_empty_unexpected():
    health = diagnose_recall("偏好", [], user_memory_count=5)
    assert health["status"] == "empty_unexpected"
    assert health["warnings"]


def test_diagnose_error():
    health = diagnose_recall("x", [], error="boom")
    assert health["status"] == "error"


def test_inject_includes_authority_and_dedupes():
    block = format_mandatory_memory_block([
        {"memory_id": "u1", "memory_type": "user", "content": "A", "trust_score": 0.7},
        {"memory_id": "u1", "memory_type": "user", "content": "A dup"},
    ])
    assert AUTHORITY_PREAMBLE.splitlines()[0] in block
    assert block.count("id=u1") == 1
    assert "置信: 0.70" in block


async def test_transient_turn_skips_write():
    memory = MagicMock()
    memory.llm = None
    out = await persist_turn_memories(
        memory, "谢谢", "不客气", "u1", session_id="s1",
    )
    assert out.stored == []
    memory.store.assert_not_called()


def test_index_count_filters_user(tmp_path):
    from src.memory.index import MemoryIndex

    db = tmp_path / "idx.db"
    idx = MemoryIndex(str(db))
    idx.add("m1", "喜欢 Python", "user", "u1")
    idx.add("m2", "喜欢 Java", "user", "u2")
    assert idx.count(user_id="u1") == 1
    assert idx.count() == 2


@pytest.mark.asyncio
async def test_recall_bundle_returns_health(tmp_path):
    from src.memory.manager import MemoryManager
    from src.memory.recall_bundle import recall_for_prompt
    from src.memory.types import MemoryType

    manager = MemoryManager(storage_dir=str(tmp_path / "memories"))
    await manager.store(
        content="我喜欢 TypeScript",
        memory_type=MemoryType.USER,
        user_id="u1",
    )
    memories, citations, health = await recall_for_prompt(
        manager, "TypeScript", "u1",
    )
    assert health["status"] in ("ok", "empty")
    assert health["user_memory_count"] >= 1
    assert len(memories) >= 1
    assert len(citations) >= 1
