"""Explicit cross-turn state for the query loop (Claude Code State pattern)."""

from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Any, Dict, List, Optional

from src.memory.citations import MemoryCitation


class LoopExitReason(str, Enum):
    COMPLETED = "completed"
    MAX_TURNS = "max_turns"
    ERROR = "error"
    PROMPT_TOO_LONG = "prompt_too_long"
    OUTPUT_TRUNCATED = "max_output_tokens_recovery"
    USER_ABORT = "user_abort"


@dataclass
class LoopState:
    messages: List[Dict[str, Any]] = field(default_factory=list)
    turn_count: int = 0
    tokens_used: int = 0
    tools_called: List[str] = field(default_factory=list)
    memories_used: List[str] = field(default_factory=list)
    memory_citations: List[MemoryCitation] = field(default_factory=list)
    is_plan_mode: bool = False
    has_attempted_reactive_compact: bool = False
    output_recovery_count: int = 0
    system_prompt: str = ""
    final_content: str = ""

    def next_turn(self, **kwargs) -> "LoopState":
        return replace(self, turn_count=self.turn_count + 1, **kwargs)


def is_prompt_too_long_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    markers = (
        "prompt is too long",
        "prompt_too_long",
        "context length",
        "maximum context",
        "413",
        "too many tokens",
        "token limit",
    )
    return any(m in msg for m in markers)


def is_output_truncated(response: Dict[str, Any]) -> bool:
    reason = (response.get("stop_reason") or "").lower()
    return reason in ("length", "max_tokens", "max_output_tokens")
