from src.memory.type_policy import extract_threshold, conflict_strategy, should_llm_extract_for_type
from src.memory.types import MemoryType


def test_extract_threshold_by_type():
    assert extract_threshold(MemoryType.USER) < extract_threshold(MemoryType.PROJECT)


def test_conflict_strategy_reference_keep_both():
    assert conflict_strategy(MemoryType.REFERENCE) == "keep_both"


def test_should_llm_extract_short_turn_user_type():
    assert not should_llm_extract_for_type(MemoryType.USER, "hi", "ok")
