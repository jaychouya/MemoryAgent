"""Chat tier and memory-model routing."""

from __future__ import annotations

from typing import List, Optional

FAST_HINTS = ("flash", "lite", "mini", "turbo", "nano", "haiku", "8b", "14b", "air")
DEEP_HINTS = ("pro", "max", "ultra", "r1", "opus", "235b", "thinking", "seed-1-8", "sonnet")

MEMORY_DOWNGRADE_RULES = (
    ("-v2.5-pro", "-v2.5"),
    ("-2.5-pro", "-2.5"),
    (".0-pro", ".0-lite"),
    ("-pro-256k", "-lite-32k"),
    ("-pro-32k", "-lite-32k"),
    ("-pro", "-flash"),
    ("-max", "-turbo"),
    ("-plus", "-turbo"),
    ("-v4-pro", "-v4-flash"),
    ("-r1", "-v4-flash"),
)


def _pick_by_hints(models: List[str], default: str, hints: tuple) -> str:
    pool = models if models else [default]
    lower_pool = [(m, m.lower()) for m in pool]
    for hint in hints:
        for original, lower in lower_pool:
            if hint in lower:
                return original
    return default


def pick_model_for_tier(
    default_model: str,
    tier: Optional[str],
    models: Optional[List[str]] = None,
) -> str:
    if not tier or tier == "balanced":
        return default_model
    pool = list(models or [])
    if default_model and default_model not in pool:
        pool.insert(0, default_model)
    if tier == "fast":
        return _pick_by_hints(pool, default_model, FAST_HINTS)
    if tier == "deep":
        return _pick_by_hints(pool, default_model, DEEP_HINTS)
    return default_model


def pick_memory_model(chat_model: str) -> str:
    for src, dst in MEMORY_DOWNGRADE_RULES:
        if src in chat_model:
            return chat_model.replace(src, dst, 1)
    lower = chat_model.lower()
    for hint in FAST_HINTS:
        if hint in lower:
            return chat_model
    return pick_model_for_tier(chat_model, "fast", [chat_model])
