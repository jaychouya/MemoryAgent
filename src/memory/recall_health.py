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
        "hints": _recall_hints(status, user_memory_count, count),
    }


def _recall_hints(status: str, user_memory_count: int, recalled: int) -> List[str]:
    if status == "empty_unexpected":
        return [
            "用更短、更具体的关键词重试（如「Python 偏好」）",
            "打开右侧记忆面板，确认相关条目存在且未废弃",
            "若刚写入记忆，等待几秒让索引更新后再问",
        ]
    if status == "empty_no_corpus":
        return [
            "还没有长期记忆，可在对话中明确说出偏好或项目规则",
            "也可在记忆面板手动新增一条",
        ]
    if status == "error":
        return ["检查后端是否在运行（http://localhost:8000/health）"]
    if recalled == 0 and user_memory_count > 0:
        return ["本轮问题可能与已有记忆无关，属正常情况"]
    return []
