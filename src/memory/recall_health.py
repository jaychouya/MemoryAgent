"""Injection health diagnostics (memory-os silent-failure guard)."""

from typing import Dict, List, Optional


def diagnose_recall(
    query: str,
    memories: List[Dict],
    *,
    user_memory_count: int = 0,
    error: Optional[str] = None,
    selection_reason: str = "",
) -> Dict:
    count = len(memories or [])
    status = "ok"
    warnings: List[str] = []

    if error:
        status = "error"
        warnings.append(f"召回异常: {error}")
    elif user_memory_count > 0 and count == 0 and (query or "").strip():
        status = "empty_unexpected"
        warnings.append(
            "用户已有记忆但本轮未召回任何条目；请检查索引/向量或 query 是否过窄。"
        )
    elif user_memory_count == 0 and count == 0:
        status = "empty_no_corpus"
    elif count == 0:
        status = "empty"

    stale = sum(1 for m in (memories or []) if m.get("is_stale"))
    low_trust = sum(
        1 for m in (memories or [])
        if float(m.get("trust_score") or 0.55) < 0.35
    )

    return {
        "status": status,
        "count": count,
        "user_memory_count": user_memory_count,
        "stale_count": stale,
        "low_trust_count": low_trust,
        "selection_reason": selection_reason or "unknown",
        "warnings": warnings,
    }
