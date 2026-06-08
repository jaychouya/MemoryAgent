"""Local recall judge for final memory filtering and explanation."""

import re
from typing import Dict, List, Optional, Tuple

_CJK = re.compile(r"[\u4e00-\u9fff]")
_WORD = re.compile(r"[a-zA-Z0-9_]{2,}")
_PREFERENCE_HINTS = ("喜欢", "偏好", "主要", "使用", "不要", "习惯", "prefer", "like", "use")
_REFERENCE_HINTS = ("哪里", "地址", "链接", "文档", "路径", "where", "link", "docs", "path")


def _tokens(text: str) -> set:
    raw = (text or "").lower()
    out = set(_WORD.findall(raw))
    chars = [c for c in raw if _CJK.match(c)]
    out.update(chars)
    out.update(chars[i] + chars[i + 1] for i in range(len(chars) - 1))
    return {t for t in out if len(t.strip()) >= 1}


def _overlap(query: str, content: str) -> Tuple[int, int]:
    q = _tokens(query)
    c = _tokens(content)
    if not q:
        return 0, 0
    return len(q & c), len(q)


def judge_memories(
    query: str,
    memories: List[Dict],
    user_id: Optional[str] = None,
    project_id: Optional[str] = None,
    limit: Optional[int] = None,
) -> List[Dict]:
    judged = []
    q = query or ""
    wants_reference = any(h in q.lower() for h in _REFERENCE_HINTS)
    wants_preference = any(h in q.lower() for h in _PREFERENCE_HINTS)

    for mem in memories:
        mid = mem.get("memory_id") or mem.get("id") or ""
        if mem.get("superseded_by"):
            continue
        mem_user = mem.get("user_id")
        if user_id and mem_user != user_id:
            continue
        mem_project = mem.get("project_id")
        if project_id and mem_project and mem_project != project_id:
            continue

        content = mem.get("content") or mem.get("text") or ""
        overlap, total = _overlap(q, content)
        base = float(mem.get("score") or 0.0)
        score = base + (overlap / max(total, 1))
        reasons = [f"overlap={overlap}/{total}"]

        mtype = mem.get("memory_type") or mem.get("type") or "user"
        if wants_preference and mtype in ("user", "feedback"):
            score += 0.25
            reasons.append("preference_type")
        if wants_reference and mtype == "reference":
            score += 0.35
            reasons.append("reference_type")
        if mem.get("is_stale") and overlap == 0 and mtype not in ("reference", "project"):
            score -= 0.5
            reasons.append("stale_low_overlap")

        kept = dict(mem)
        kept["judge_score"] = round(score, 4)
        kept["judge_reason"] = ", ".join(reasons)
        kept.pop("dropped_reason", None)
        judged.append(kept)

    judged.sort(key=lambda m: float(m.get("judge_score") or 0.0), reverse=True)
    return judged[:limit] if limit else judged
