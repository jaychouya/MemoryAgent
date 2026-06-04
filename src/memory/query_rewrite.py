"""Lightweight query rewrite for retrieval (no LLM)."""

import re
from typing import Tuple

_FILLER_PREFIX = re.compile(
    r"^(请|帮我|能不能|我想知道|我想|那个|就是|其实|嗯+|啊+|呃+)\s*",
    re.IGNORECASE,
)
_WHITESPACE = re.compile(r"\s+")


def rewrite_query_for_retrieval(query: str, max_len: int = 120) -> Tuple[str, bool]:
    """
    Shorten noisy user messages for FTS/vector search.
    Returns (search_query, was_rewritten).
    """
    raw = (query or "").strip()
    if not raw:
        return raw, False
    if len(raw) <= max_len:
        return raw, False

    candidate = raw
    if "：" in raw or ":" in raw:
        tail = re.split(r"[：:]", raw)[-1].strip()
        if len(tail) >= 6:
            candidate = tail
    else:
        parts = re.split(r"[。！？!?\n]+", raw)
        parts = [p.strip() for p in parts if len(p.strip()) >= 6]
        if parts:
            intent = [p for p in parts if re.search(r"(怎么|什么|哪|为何|是否|吗|？|\?)", p)]
            pick = intent[-1] if intent else parts[-1]
            if 6 <= len(pick) <= len(raw):
                candidate = pick

    candidate = _FILLER_PREFIX.sub("", candidate).strip()
    candidate = _WHITESPACE.sub(" ", candidate)
    if len(candidate) > max_len:
        candidate = candidate[:max_len].rstrip()

    if not candidate:
        candidate = raw[:max_len]
    return candidate, candidate != raw
