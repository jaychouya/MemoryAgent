"""Mandatory memory injection block for system prompt."""

from typing import Dict, List

from src.memory.authority import AUTHORITY_PREAMBLE


def _dedupe_by_id(memories: List[Dict]) -> List[Dict]:
    seen = set()
    out = []
    for mem in memories:
        mid = mem.get("memory_id") or mem.get("id")
        if mid and mid in seen:
            continue
        if mid:
            seen.add(mid)
        out.append(mem)
    return out


def format_mandatory_memory_block(memories: List[Dict]) -> str:
    if not memories:
        return (
            f"{AUTHORITY_PREAMBLE}\n\n"
            "【强制记忆注入】本轮未召回任何记忆。\n"
            "禁止引用、猜测或套用用户历史偏好与项目决策；仅依据本轮对话作答。"
        )

    memories = _dedupe_by_id(memories)
    lines = [
        AUTHORITY_PREAMBLE,
        "",
        "【强制记忆注入】以下记忆已写入 system，本轮回复必须遵守；"
        "与本轮用户消息冲突时，以本轮明确指令为准，并说明取舍。",
        "",
    ]
    for i, mem in enumerate(memories, 1):
        mid = mem.get("memory_id") or mem.get("id") or f"m{i}"
        mtype = mem.get("memory_type") or mem.get("type") or "user"
        content = (mem.get("content") or "").strip()
        lines.append(f"M{i} [{mtype}] id={mid}")
        if mem.get("description"):
            lines.append(f"摘要: {mem['description']}")
        lines.append(content)
        if mem.get("is_stale"):
            days = mem.get("age_days", "?")
            lines.append(f"⚠ 陈旧记忆（{days} 天），引用前请先核实是否仍成立。")
        if mem.get("judge_reason"):
            lines.append(f"召回: {mem['judge_reason']}")
        trust = mem.get("trust_score")
        if trust is not None:
            lines.append(f"置信: {float(trust):.2f}")
        lines.append("")

    lines.append("不得与上述记忆矛盾；无需在文末复述全部记忆。")
    return "\n".join(lines)
