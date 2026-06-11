"""Trust scoring for durable facts (memory-os fact-store inspired)."""

from typing import Dict, List, Optional

DEFAULT_TRUST = 0.55
RECALL_BOOST = 0.06
STORE_BOOST = 0.03
TRUST_MIN = 0.1
TRUST_MAX = 1.0

_TYPE_BASE = {
    "feedback": 0.75,
    "user": 0.65,
    "project": 0.6,
    "reference": 0.5,
}


def initial_trust(memory_type: str) -> float:
    return _TYPE_BASE.get((memory_type or "user").lower(), DEFAULT_TRUST)


def clamp_trust(value: float) -> float:
    return max(TRUST_MIN, min(TRUST_MAX, value))


def boost_on_recall(trust: Optional[float]) -> float:
    base = trust if trust is not None else DEFAULT_TRUST
    return clamp_trust(base + RECALL_BOOST)


def boost_on_store(trust: Optional[float]) -> float:
    base = trust if trust is not None else DEFAULT_TRUST
    return clamp_trust(base + STORE_BOOST)


def decay_for_age(trust: float, age_days: int) -> float:
    if age_days <= 30:
        return trust
    if age_days <= 90:
        return clamp_trust(trust - 0.05)
    return clamp_trust(trust - 0.12)


def effective_rank_score(base_score: float, trust: float, age_days: int = 0) -> float:
    adjusted = decay_for_age(trust, age_days)
    return float(base_score or 0) * (0.5 + 0.5 * adjusted)


def apply_trust_to_results(results: List[Dict]) -> List[Dict]:
    for row in results:
        trust = row.get("trust_score")
        if trust is None:
            trust = initial_trust(row.get("memory_type") or row.get("type") or "user")
            row["trust_score"] = trust
        age = int(row.get("age_days") or 0)
        base = float(row.get("score") or row.get("rerank_score") or 0.5)
        row["effective_score"] = effective_rank_score(base, trust, age)
    return sorted(results, key=lambda r: r.get("effective_score", 0), reverse=True)
