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
        enriched.append({
            "memory_id": m.get("memory_id") or m.get("id", ""),
            "content": m.get("content", ""),
            "memory_type": m.get("memory_type", "user"),
            "user_id": m.get("user_id", user_id),
            "project_id": m.get("project_id") or project_id,
            "score": m.get("score", 0.0),
            "is_stale": m.get("is_stale", False),
            "selection_reason": m.get("selection_reason", ""),
            "priority": _priority(m.get("memory_type", "user")),
        })
    enriched.sort(key=lambda x: (-x["priority"], -float(x.get("score") or 0)))

    lines = []
    for item in enriched:
        tag = item["memory_type"]
        lines.append(f"[{tag}] {item['content']}")

    return {
        "format": version,
        "user_id": user_id,
        "project_id": project_id,
        "scope": scope,
        "query": query or "",
        "count": len(enriched),
        "memories": enriched,
        "prompt_block": "\n".join(lines),
        "generated_at": datetime.now().isoformat(),
    }
