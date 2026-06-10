"""Embeddings: optional API (OpenAI-compatible) with local fallback."""

import hashlib
import logging
import math
from typing import List, Optional

from src.utils.config import settings

logger = logging.getLogger(__name__)

_DEFAULT_DIM = 384


def local_embed(text: str, dimension: int = _DEFAULT_DIM) -> List[float]:
    if not text or not text.strip():
        raise ValueError("Text cannot be empty")

    vec = [0.0] * dimension
    tokens = text.lower().split()
    if not tokens:
        tokens = [text.lower()]

    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        for i, byte in enumerate(digest):
            idx = (i * 17 + byte) % dimension
            vec[idx] += (byte / 255.0) - 0.5

    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0:
        return vec
    return [v / norm for v in vec]


def _api_key() -> Optional[str]:
    return settings.EMBEDDING_API_KEY or settings.OPENAI_API_KEY


def embed_text(text: str, dimension: Optional[int] = None) -> List[float]:
    """Sync embed for store/index paths."""
    dim = dimension or settings.EMBEDDING_DIMENSIONS or _DEFAULT_DIM
    key = _api_key()
    if not key or not text.strip():
        return local_embed(text, dimension=dim)

    try:
        from openai import OpenAI

        kwargs_client = {"api_key": key}
        if settings.EMBEDDING_BASE_URL:
            kwargs_client["base_url"] = settings.EMBEDDING_BASE_URL
        client = OpenAI(**kwargs_client)

        req = {"model": settings.EMBEDDING_MODEL, "input": text.strip()}
        if "text-embedding-3" in settings.EMBEDDING_MODEL:
            req["dimensions"] = dim
        resp = client.embeddings.create(**req)
        emb = resp.data[0].embedding
        if len(emb) != dim:
            return local_embed(text, dimension=dim)
        return emb
    except Exception as e:
        logger.warning(f"API embedding failed, using local: {e}")
        return local_embed(text, dimension=dim)


def embed_texts(texts: List[str], dimension: Optional[int] = None) -> List[List[float]]:
    """Batch embed; one API round-trip when key is configured."""
    dim = dimension or settings.EMBEDDING_DIMENSIONS or _DEFAULT_DIM
    cleaned = [t.strip() for t in texts if t and t.strip()]
    if not cleaned:
        return []
    key = _api_key()
    if not key:
        return [local_embed(t, dimension=dim) for t in cleaned]

    try:
        from openai import OpenAI

        kwargs_client = {"api_key": key}
        if settings.EMBEDDING_BASE_URL:
            kwargs_client["base_url"] = settings.EMBEDDING_BASE_URL
        client = OpenAI(**kwargs_client)
        req = {"model": settings.EMBEDDING_MODEL, "input": cleaned}
        if "text-embedding-3" in settings.EMBEDDING_MODEL:
            req["dimensions"] = dim
        resp = client.embeddings.create(**req)
        out = []
        for item in resp.data:
            emb = item.embedding
            if len(emb) != dim:
                out.append(local_embed(cleaned[item.index], dimension=dim))
            else:
                out.append(emb)
        return out
    except Exception as e:
        logger.warning(f"Batch API embedding failed, using local: {e}")
        return [local_embed(t, dimension=dim) for t in cleaned]


def cosine_similarity(a: List[float], b: List[float]) -> float:
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)
