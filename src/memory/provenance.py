"""L0 evidence archive and L1 provenance metadata (Tencent-inspired traceability)."""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def _sanitize_path_part(value: str) -> str:
    return re.sub(r"[^\w\-.]", "_", (value or "default"))[:64]


def l0_path(storage_dir: str, user_id: str, session_id: str) -> Path:
    base = Path(storage_dir) / "l0" / _sanitize_path_part(user_id)
    base.mkdir(parents=True, exist_ok=True)
    return base / f"{_sanitize_path_part(session_id)}.jsonl"


def append_l0_turn(
    storage_dir: str,
    user_id: str,
    session_id: str,
    user_message: str,
    assistant_message: str,
) -> int:
    """Append one turn to L0 log. Returns 1-based turn index."""
    path = l0_path(storage_dir, user_id, session_id)
    turn_index = 1
    if path.exists():
        turn_index = sum(1 for _ in path.open(encoding="utf-8")) + 1
    record = {
        "turn": turn_index,
        "user": (user_message or "")[:4000],
        "assistant": (assistant_message or "")[:4000],
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return turn_index


def pick_source_quote(user_message: str, fact_content: str, max_len: int = 240) -> str:
    user = (user_message or "").strip()
    if not user:
        return ""
    fact = (fact_content or "").strip().lower()
    if fact and len(fact) >= 4:
        for sentence in re.split(r"[。！？!?\n]+", user):
            s = sentence.strip()
            if len(s) >= 4 and any(
                tok in s.lower() for tok in fact.split()[:3] if len(tok) >= 2
            ):
                return s[:max_len]
    return user[:max_len]


def build_l1_provenance(
    storage_dir: str,
    user_id: str,
    session_id: str,
    user_message: str,
    assistant_message: str,
    fact_content: str,
) -> Dict[str, Any]:
    turn_index = append_l0_turn(
        storage_dir, user_id, session_id, user_message, assistant_message
    )
    rel_l0 = str(
        l0_path(storage_dir, user_id, session_id).relative_to(Path(storage_dir))
    )
    return {
        "evidence_level": "L1",
        "source_session_id": session_id,
        "source_turn": turn_index,
        "source_quote": pick_source_quote(user_message, fact_content),
        "l0_path": rel_l0,
    }


def load_l0_turn(storage_dir: str, rel_l0_path: str, turn: int) -> Optional[Dict[str, Any]]:
    path = Path(storage_dir) / rel_l0_path
    if not path.exists():
        return None
    for line in path.open(encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
            if int(rec.get("turn", 0)) == int(turn):
                return rec
        except json.JSONDecodeError:
            continue
    return None
