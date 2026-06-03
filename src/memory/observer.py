"""Auto write-back observer after conversations."""

import hashlib
import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple

from src.memory.manager import MemoryManager
from src.memory.types import MemoryType
from src.memory.exclusions import should_exclude

logger = logging.getLogger(__name__)

PREFERENCE_PATTERNS = [
    (re.compile(r"我喜欢(.+?)(?:[，。!！?？\n]|$)"), MemoryType.USER),
    (re.compile(r"我偏好(.+?)(?:[，。!！?？\n]|$)"), MemoryType.USER),
    (re.compile(r"我讨厌(.+?)(?:[，。!！?？\n]|$)"), MemoryType.USER),
    (re.compile(r"记住[：:]?\s*(.+?)(?:[，。!！?？\n]|$)"), MemoryType.USER),
    (re.compile(r"不要用\s*(.+?)(?:[，。!！?？\n]|$)"), MemoryType.FEEDBACK),
    (re.compile(r"不要\s*使用\s*(.+?)(?:[，。!！?？\n]|$)"), MemoryType.FEEDBACK),
]

_recent_hashes: Dict[str, datetime] = {}


def _content_hash(user_id: str, content: str) -> str:
    return hashlib.md5(f"{user_id}:{content}".encode()).hexdigest()


def _is_duplicate(user_id: str, content: str, hours: int = 24) -> bool:
    key = _content_hash(user_id, content)
    if key in _recent_hashes:
        if datetime.now() - _recent_hashes[key] < timedelta(hours=hours):
            return True
    _recent_hashes[key] = datetime.now()
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


class MemoryObserver:
    def __init__(self, memory_manager: MemoryManager):
        self.memory = memory_manager

    async def observe_turn(
        self,
        user_message: str,
        assistant_message: str,
        user_id: str,
        session_id: str = None,
    ) -> List[str]:
        stored_ids = []
        for content, mem_type in extract_candidates(user_message):
            if _is_duplicate(user_id, content):
                continue
            meta = {
                "user_id": user_id,
                "source": "auto_observer",
                "session_id": session_id,
            }
            item = await self.memory.store(
                content=content,
                memory_type=mem_type,
                description=f"自动沉淀: {content[:30]}",
                user_id=user_id,
                metadata=meta,
            )
            if item:
                stored_ids.append(item.id)
                logger.info(f"Observer stored {item.id} for {user_id}")
        return stored_ids
