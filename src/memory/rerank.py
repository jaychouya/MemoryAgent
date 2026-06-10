"""Lightweight rerank: embedding cosine (top-N → top-K), optional LLM refine."""

import json
import logging
import re
from typing import Any, Dict, List, Optional

from src.memory.embeddings import embed_text, cosine_similarity
from src.utils.config import settings

logger = logging.getLogger(__name__)


def _lexical_score(query: str, content: str) -> float:
    q = set(query.lower().split())
    c = set(content.lower().split())
    if not q:
        return 0.0
    return len(q & c) / len(q)


async def rerank_candidates(
    query: str,
    candidates: List[Dict[str, Any]],
    top_k: int = 5,
    llm_service=None,
    use_llm: Optional[bool] = None,
) -> List[Dict[str, Any]]:
    if not candidates:
        return []
    if not settings.RERANK_ENABLED or len(candidates) <= top_k:
        return candidates[:top_k]

    cap = min(len(candidates), settings.RERANK_EMBED_CAP, settings.RERANK_CANDIDATE_POOL)
    pre_sorted = sorted(
        candidates,
        key=lambda c: float(c.get("score") or c.get("importance") or 0.0),
        reverse=True,
    )[:cap]

    q_emb = None
    content_embs: List[List[float]] = []
    try:
        from src.memory.embeddings import embed_texts

        texts = [query] + [(c.get("content") or "") for c in pre_sorted]
        embs = embed_texts(texts)
        if embs:
            q_emb = embs[0]
            content_embs = embs[1:]
    except Exception:
        try:
            q_emb = embed_text(query)
        except Exception:
            q_emb = None

    scored = []
    for i, c in enumerate(pre_sorted):
        content = c.get("content") or ""
        base = float(c.get("score") or c.get("importance") or 0.5)
        vec_score = 0.0
        if q_emb and content and i < len(content_embs):
            vec_score = cosine_similarity(q_emb, content_embs[i])
        lex = _lexical_score(query, content)
        final = 0.45 * vec_score + 0.35 * base + 0.20 * lex
        row = dict(c)
        row["rerank_score"] = final
        scored.append(row)

    scored.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)
    pool = scored[: settings.RERANK_CANDIDATE_POOL]

    llm_on = settings.RERANK_USE_LLM if use_llm is None else use_llm
    if llm_on and llm_service and getattr(llm_service, "client", None):
        pool = await _llm_rerank(query, pool, top_k, llm_service)
    else:
        pool = pool[:top_k]

    for r in pool:
        r["selection_reason"] = "keyword+vector+rerank"
    return pool


async def _llm_rerank(
    query: str,
    candidates: List[Dict[str, Any]],
    top_k: int,
    llm_service,
) -> List[Dict[str, Any]]:
    if len(candidates) <= top_k:
        return candidates
    lines = []
    for i, c in enumerate(candidates[: settings.RERANK_CANDIDATE_POOL]):
        lines.append(f"{i}: {(c.get('content') or '')[:180]}")
    prompt = (
        f"用户问题: {query}\n\n"
        f"候选记忆:\n" + "\n".join(lines) + "\n\n"
        f"选出最相关的最多 {top_k} 条，只输出 JSON 数组 of index 整数，如 [0,2,1]。无关则 []。"
    )
    try:
        resp = await llm_service.generate_response(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="你是记忆检索排序器，只输出 JSON 数组。",
        )
        raw = (resp.get("content") if isinstance(resp, dict) else str(resp)) or "[]"
        match = re.search(r"\[[\s\S]*?\]", raw)
        if not match:
            return candidates[:top_k]
        indices = json.loads(match.group())
        out = []
        for idx in indices:
            if isinstance(idx, int) and 0 <= idx < len(candidates):
                out.append(candidates[idx])
            if len(out) >= top_k:
                break
        return out if out else candidates[:top_k]
    except Exception as e:
        logger.warning(f"LLM rerank failed: {e}")
        return candidates[:top_k]
