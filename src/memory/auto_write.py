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

PROJECT_PATTERNS = [
    (re.compile(r"(?:本项目|这个项目|项目|我们)(?:决定|约定|要求|必须|禁止|不允许|默认|采用|使用)(.+?)(?:[，。!！?？\n]|$)"), MemoryType.PROJECT),
]

_TRANSIENT_UTTERANCE = re.compile(
    r"^(你好|您好|谢谢|感谢|好的|收到|明白了|知道了|ok|okay|hi|hello)[!！。.?？\s]*$",
    re.IGNORECASE,
)

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


def _clean_fragment(fragment: str) -> str:
    return fragment.strip().rstrip("，。!！?？")


def _is_memory_meta_question(text: str) -> bool:
    return "记住" in text and any(k in text for k in ("吗", "了吗", "没", "没有", "是不是"))


def is_transient_utterance(text: str) -> bool:
    return bool(_TRANSIENT_UTTERANCE.match(text.strip()))


def extract_candidates(user_message: str) -> List[Tuple[str, MemoryType]]:
    candidates = []
    text = user_message.strip()
    if not text:
        return candidates
    if is_transient_utterance(text) or _is_memory_meta_question(text):
        return candidates
    for pattern, mem_type in PREFERENCE_PATTERNS + PROJECT_PATTERNS:
        for match in pattern.finditer(text):
            fragment = _clean_fragment(match.group(0))
            if len(fragment) >= 6 and not should_exclude(fragment, mem_type.value):
                candidates.append((fragment, mem_type))
    if not candidates and any(k in text for k in ("喜欢", "讨厌", "偏好", "记住")):
        if len(text) >= 6 and not should_exclude(text, "user"):
            candidates.append((text, MemoryType.USER))
    return candidates
