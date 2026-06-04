"""Regex + dedup helpers for automatic memory write-back."""

import hashlib
import json
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

from src.memory.types import MemoryType
from src.memory.exclusions import should_exclude

logger = logging.getLogger(__name__)

TYPE_MAP = {
    "user": MemoryType.USER,
    "feedback": MemoryType.FEEDBACK,
    "project": MemoryType.PROJECT,
    "reference": MemoryType.REFERENCE,
}

PREFERENCE_PATTERNS = [
    (re.compile(r"我喜欢(.+?)(?:[，。!！?？\n]|$)"), MemoryType.USER),
    (re.compile(r"我偏好(.+?)(?:[，。!！?？\n]|$)"), MemoryType.USER),
    (re.compile(r"我讨厌(.+?)(?:[，。!！?？\n]|$)"), MemoryType.USER),
    (re.compile(r"记住[：:]?\s*(.+?)(?:[，。!！?？\n]|$)"), MemoryType.USER),
    (re.compile(r"不要用\s*(.+?)(?:[，。!！?？\n]|$)"), MemoryType.FEEDBACK),
    (re.compile(r"不要\s*使用\s*(.+?)(?:[，。!！?？\n]|$)"), MemoryType.FEEDBACK),
]

_DEDUP_PATH = Path(".memoryai/observer_dedup.json")
_recent_hashes: Dict[str, datetime] = {}


def _load_dedup() -> None:
    global _recent_hashes
    if not _DEDUP_PATH.exists():
        return
    try:
        data = json.loads(_DEDUP_PATH.read_text(encoding="utf-8"))
        _recent_hashes = {k: datetime.fromisoformat(v) for k, v in data.items()}
    except Exception as e:
        logger.warning(f"Dedup load failed: {e}")


def _save_dedup() -> None:
    _DEDUP_PATH.parent.mkdir(parents=True, exist_ok=True)
    _DEDUP_PATH.write_text(
        json.dumps({k: v.isoformat() for k, v in _recent_hashes.items()}),
        encoding="utf-8",
    )


def content_hash(user_id: str, content: str) -> str:
    return hashlib.md5(f"{user_id}:{content}".encode()).hexdigest()


def is_duplicate(user_id: str, content: str, hours: int = 24) -> bool:
    if not _recent_hashes:
        _load_dedup()
    key = content_hash(user_id, content)
    if key in _recent_hashes:
        if datetime.now() - _recent_hashes[key] < timedelta(hours=hours):
            return True
    _recent_hashes[key] = datetime.now()
    _save_dedup()
    return False


def extract_candidates(user_message: str) -> List[Tuple[str, MemoryType]]:
    candidates = []
    text = user_message.strip()
    if not text:
        return candidates
    for pattern, mem_type in PREFERENCE_PATTERNS:
        for match in pattern.finditer(text):
            fragment = match.group(0).strip()
            if len(fragment) >= 6 and not should_exclude(fragment, mem_type.value):
                candidates.append((fragment, mem_type))
    if not candidates and any(k in text for k in ("喜欢", "讨厌", "偏好", "记住")):
        if len(text) >= 6 and not should_exclude(text, "user"):
            candidates.append((text, MemoryType.USER))
    return candidates
