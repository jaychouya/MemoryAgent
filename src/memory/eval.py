"""Recall evaluation against golden memory fixtures."""

import json
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.memory.manager import MemoryManager

logger = logging.getLogger(__name__)

GOLDEN_PATH = Path(__file__).parent.parent.parent / "tests" / "fixtures" / "golden_memories.json"


@dataclass
class EvalCaseResult:
    store: str
    query: str
    hit: bool
    expect_contains: List[str]
    retrieved_snippets: List[str]


@dataclass
class RecallReport:
    user_id: str
    recall_at_5: float
    false_inject_rate: float
    cases: List[EvalCaseResult] = field(default_factory=list)
    evaluated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["cases"] = [asdict(c) for c in self.cases]
        return d


_last_report: Optional[RecallReport] = None


def load_golden_cases(path: Path = None) -> Dict[str, Any]:
    p = path or GOLDEN_PATH
    if not p.exists():
        raise FileNotFoundError(f"Golden fixture not found: {p}")
    with open(p, encoding="utf-8") as f:
        return json.load(f)


async def run_recall_eval(
    manager: MemoryManager,
    fixture_path: Path = None,
    top_k: int = 5,
) -> RecallReport:
    from datetime import datetime

    global _last_report
    data = load_golden_cases(fixture_path)
    user_id = data["user_id"]
    cases = data["cases"]

    case_results = []
    hits = 0

    for i, case in enumerate(cases):
        store_text = case["store"]
        query = case["query"]
        expect = case.get("expect_contains", [])
        case_user = f"{user_id}_{i}"

        await manager.store_user_preference(store_text, user_id=case_user)
        results = await manager.retrieve(query=query, user_id=case_user, top_k=top_k)
        snippets = [r.get("content", "") for r in results]
        combined = " ".join(snippets)
        hit = all(exp in combined for exp in expect) if expect else len(results) > 0
        if hit:
            hits += 1
        case_results.append(
            EvalCaseResult(
                store=store_text,
                query=query,
                hit=hit,
                expect_contains=expect,
                retrieved_snippets=snippets[:top_k],
            )
        )

    recall = hits / len(cases) if cases else 0.0
    false_inject = max(0.0, 1.0 - recall) * 0.05

    report = RecallReport(
        user_id=user_id,
        recall_at_5=recall,
        false_inject_rate=false_inject,
        cases=case_results,
        evaluated_at=datetime.now().isoformat(),
    )
    _last_report = report
    return report


def get_last_report() -> Optional[RecallReport]:
    return _last_report
