"""Lightweight local conflict detection for memory supersession."""

from typing import Dict, Iterable, List, Optional

from src.memory.recall_judge import _tokens

_REPLACEMENT_SIGNALS = (
    "现在",
    "改成",
    "不再",
    "以后",
    "主要使用",
    "now",
    "instead",
    "no longer",
    "prefer",
    "mainly use",
)


def has_replacement_signal(text: str) -> bool:
    raw = (text or "").lower()
    return any(signal in raw for signal in _REPLACEMENT_SIGNALS)


def find_conflicts(
    new_content: str,
    existing: Iterable[Dict],
    user_id: Optional[str],
    project_id: Optional[str],
    memory_type: str,
) -> List[Dict]:
    if not has_replacement_signal(new_content):
        return []

    new_tokens = _tokens(new_content)
    conflicts = []
    for row in existing:
        if row.get("superseded_by"):
            continue
        if row.get("memory_type") != memory_type:
            continue
        if user_id and row.get("user_id") and row.get("user_id") != user_id:
            continue
        row_project = row.get("project_id")
        if row_project != project_id:
            continue
        old_tokens = _tokens(row.get("content", ""))
        overlap = new_tokens & old_tokens
        if len(overlap) >= 2:
            conflict = dict(row)
            conflict["conflict_reason"] = f"replacement_signal_overlap:{','.join(sorted(overlap)[:5])}"
            conflicts.append(conflict)
    return conflicts
