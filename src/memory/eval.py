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
    positive_cases = [c for c in cases if not c.get("decoy")]
    decoy_cases = [c for c in cases if c.get("decoy")]
    false_hits = 0
    decoy_evaluated = 0

    for i, case in enumerate(cases):
        store_text = case.get("store") or case.get("store_signal", "")
        query = case["query"]
        expect = case.get("expect_contains", [])
        expect_excludes = case.get("expect_excludes", [])
        is_decoy = case.get("decoy", False)
        case_user = f"{user_id}_{i}"

        if is_decoy:
            await manager.store_user_preference(case["store_noise"], user_id=case_user)
            await manager.store_user_preference(case["store_signal"], user_id=case_user)
        else:
            await manager.store_user_preference(store_text, user_id=case_user)
        results = await manager.retrieve(query=query, user_id=case_user, top_k=top_k)
        snippets = [r.get("content", "") for r in results]
        combined = " ".join(snippets)
        if is_decoy:
            markers = case.get("signal_markers", [])
            has_signal = any(
                any(m in snippet for m in markers) for snippet in snippets
            )
            has_noise = any(
                any(ex in snippet for ex in expect_excludes) for snippet in snippets
            )
            decoy_evaluated += 1
            noise_outranks = False
            if has_signal and has_noise:
                first_signal_idx = next(
                    (
                        i for i, snippet in enumerate(snippets)
                        if any(m in snippet for m in markers)
                    ),
                    len(snippets),
                )
                noise_outranks = any(
                    i < first_signal_idx
                    and any(ex in snippets[i] for ex in expect_excludes)
                    for i in range(len(snippets))
                )
            if noise_outranks:
                false_hits += 1
            hit = not noise_outranks and has_signal
        else:
            hit = all(exp in combined for exp in expect) if expect else len(results) > 0
            if hit:
                hits += 1
        label = (
            f"{case.get('store_noise', '')} | {case.get('store_signal', '')}"
            if is_decoy
            else store_text
        )
        case_results.append(
            EvalCaseResult(
                store=label,
                query=query,
                hit=hit,
                expect_contains=expect if not is_decoy else expect_excludes,
                retrieved_snippets=snippets[:top_k],
            )
        )

    recall = hits / len(positive_cases) if positive_cases else 0.0
    false_inject = false_hits / decoy_evaluated if decoy_evaluated else 0.0

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
