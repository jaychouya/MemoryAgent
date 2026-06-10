"""Per-type extract thresholds and conflict strategies."""

from src.memory.types import MemoryType
from src.utils.config import settings

EXTRACT_MIN_CHARS: dict[str, int] = {
    MemoryType.USER.value: 120,
    MemoryType.FEEDBACK.value: 150,
    MemoryType.PROJECT.value: 280,
    MemoryType.REFERENCE.value: 200,
}

CONFLICT_STRATEGY: dict[str, str] = {
    MemoryType.USER.value: "user_prompt",
    MemoryType.FEEDBACK.value: "user_prompt",
    MemoryType.PROJECT.value: "user_prompt",
    MemoryType.REFERENCE.value: "keep_both",
}


def extract_threshold(memory_type: MemoryType) -> int:
    if settings.MEMORY_EXTRACT_LLM_MIN_CHARS == 0:
        return 0
    return EXTRACT_MIN_CHARS.get(
        memory_type.value,
        settings.MEMORY_EXTRACT_LLM_MIN_CHARS,
    )


def should_llm_extract_for_type(
    memory_type: MemoryType,
    user_message: str,
    assistant_message: str,
) -> bool:
    if not settings.MEMORY_EXTRACT_ENABLED:
        return False
    total = len(user_message or "") + len(assistant_message or "")
    t = extract_threshold(memory_type)
    g = settings.MEMORY_EXTRACT_LLM_MIN_CHARS
    threshold = max(t, g) if g > t else t
    return total >= threshold


def conflict_strategy(memory_type: MemoryType) -> str:
    return CONFLICT_STRATEGY.get(memory_type.value, "user_prompt")
