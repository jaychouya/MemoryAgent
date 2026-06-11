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
