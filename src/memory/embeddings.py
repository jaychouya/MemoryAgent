"""Local embedding fallback when API embeddings are unavailable."""

import hashlib
import math
from typing import List


def local_embed(text: str, dimension: int = 384) -> List[float]:
    """Deterministic bag-of-hashes embedding for semantic-ish search offline."""
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
