"""Structured memory citations for explainable recall."""

from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional


@dataclass
class MemoryCitation:
    memory_id: str
    memory_type: str
    description: str
    content_snippet: str
    score: float
    age_days: int
    is_stale: bool
    selection_reason: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def build_citations(
    results: List[Dict],
    selection_reason: str = "keyword+vector",
) -> List[MemoryCitation]:
    citations = []
    for item in results:
        content = item.get("content", "") or ""
        citations.append(
            MemoryCitation(
                memory_id=item.get("memory_id") or item.get("id", ""),
                memory_type=item.get("memory_type") or item.get("type", "user"),
                description=item.get("description") or content[:80],
                content_snippet=content[:200],
                score=float(item.get("score", 0.0)),
                age_days=int(item.get("age_days", 0)),
                is_stale=bool(item.get("is_stale", False)),
                selection_reason=item.get("selection_reason") or selection_reason,
            )
        )
    return citations


def citations_to_legacy_strings(citations: List[MemoryCitation]) -> List[str]:
    return [c.content_snippet for c in citations]
