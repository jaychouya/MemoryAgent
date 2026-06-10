"""Sidecar export protocol v1/v2."""

from datetime import datetime
from typing import Any, Dict, List, Optional

SIDECAR_V2 = "memoryagent-sidecar-v2"


def _priority(memory_type: str) -> int:
    order = {"feedback": 4, "user": 3, "project": 2, "reference": 1}
    return order.get(memory_type or "user", 0)


def build_export_payload(
    user_id: str,
    memories: List[Dict[str, Any]],
    query: Optional[str] = None,
    project_id: Optional[str] = None,
    scope: str = "user",
    version: str = SIDECAR_V2,
) -> Dict[str, Any]:
    enriched = []
    for m in memories:
        item = {
            "memory_id": m.get("memory_id") or m.get("id", ""),
            "content": m.get("content", ""),
            "memory_type": m.get("memory_type", "user"),
            "user_id": m.get("user_id", user_id),
            "project_id": m.get("project_id") or project_id,
            "score": m.get("score", 0.0),
            "is_stale": m.get("is_stale", False),
            "selection_reason": m.get("selection_reason", ""),
            "priority": _priority(m.get("memory_type", "user")),
        }
        for key in (
            "evidence_level",
            "source_session_id",
            "source_turn",
            "source_quote",
            "l0_path",
            "supersedes",
            "superseded_by",
            "valid_until",
            "conflict_reason",
            "judge_score",
            "judge_reason",
            "dropped_reason",
        ):
            if m.get(key) is not None:
                item[key] = m.get(key)
        enriched.append(item)
    enriched.sort(key=lambda x: (-x["priority"], -float(x.get("score") or 0)))

    lines = []
    for item in enriched:
        tag = item["memory_type"]
        lines.append(f"[{tag}] {item['content']}")

    cursor_rules = build_cursor_rules_block(enriched, user_id, project_id)

    return {
        "format": version,
        "user_id": user_id,
        "project_id": project_id,
        "scope": scope,
        "query": query or "",
        "count": len(enriched),
        "memories": enriched,
        "prompt_block": "\n".join(lines),
        "cursor_rules_block": cursor_rules,
        "generated_at": datetime.now().isoformat(),
    }


def build_cursor_rules_block(
    memories: List[Dict[str, Any]],
    user_id: str,
    project_id: Optional[str] = None,
) -> str:
    scope = project_id or user_id
    lines = [
        "---",
        f"description: MemoryAgent 用户记忆 ({scope})",
        "alwaysApply: true",
        "---",
        "",
        "# MemoryAgent 注入记忆",
        "",
        "回答时遵守以下记忆（来自 memory_export）：",
        "",
    ]
    for item in memories:
        tag = item.get("memory_type", "user")
        lines.append(f"- **[{tag}]** {item.get('content', '')}")
    if not memories:
        lines.append("- （当前无记忆）")
    lines.extend([
        "",
        "每轮对话前可调用 `memory_recall` 刷新；用户更正偏好时调用 `memory_store`。",
    ])
    return "\n".join(lines)
