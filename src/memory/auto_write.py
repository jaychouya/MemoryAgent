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

_REMEMBER_EXPLICIT = re.compile(r"记住[：:]?\s*(.+?)(?:[，。!！?？\n]|$)")

PREFERENCE_PATTERNS = [
    (re.compile(r"我喜欢(.+?)(?:[，。!！?？\n]|$)"), MemoryType.USER, "我喜欢"),
    (re.compile(r"我偏好(.+?)(?:[，。!！?？\n]|$)"), MemoryType.USER, "我偏好"),
    (re.compile(r"我讨厌(.+?)(?:[，。!！?？\n]|$)"), MemoryType.USER, "我讨厌"),
    (re.compile(r"不要用\s*(.+?)(?:[，。!！?？\n]|$)"), MemoryType.FEEDBACK, "不要用"),
    (re.compile(r"不要\s*使用\s*(.+?)(?:[，。!！?？\n]|$)"), MemoryType.FEEDBACK, "不要使用"),
]

PROJECT_PATTERNS = [
    (re.compile(r"(?:本项目|这个项目|项目|我们)(?:决定|约定|要求|必须|禁止|不允许|默认|采用|使用)(.+?)(?:[，。!！?？\n]|$)"), MemoryType.PROJECT),
]

_TRANSIENT_UTTERANCE = re.compile(
    r"^(你好|您好|谢谢|感谢|好的|收到|明白了|知道了|ok|okay|hi|hello)[!！。.?？\s]*$",
    re.IGNORECASE,
)

_FORGET_INTENT = re.compile(
    r"(忘掉|忘记|删除|移除|清除|不要再记住|别再记住|forget|delete|remove)",
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


def normalize_memory_content(content: str) -> str:
    text = content.strip()
    text = re.sub(r"^记住[：:]?\s*", "", text)
    text = re.sub(r"^用户偏好", "我偏好", text)
    return text.strip()


def memory_fingerprint(content: str) -> str:
    text = normalize_memory_content(content).lower()
    text = re.sub(r"^我", "", text)
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[，。!！?？、；;：:]", "", text)
    return text


def texts_similar(a: str, b: str, threshold: float = 0.55) -> bool:
    if not a or not b:
        return False
    if memory_fingerprint(a) == memory_fingerprint(b):
        return True

    def tokenize(text: str) -> set:
        chinese = re.findall(r"[\u4e00-\u9fff]", text)
        english = re.findall(r"[a-zA-Z]+", text.lower())
        return set(chinese + english)

    words1, words2 = tokenize(a), tokenize(b)
    if not words1 or not words2:
        return False
    return len(words1 & words2) / len(words1 | words2) >= threshold


def content_hash(user_id: str, content: str) -> str:
    return hashlib.md5(f"{user_id}:{memory_fingerprint(content)}".encode()).hexdigest()


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


def extract_forget_query(user_message: str) -> str:
    text = user_message.strip()
    if not _FORGET_INTENT.search(text):
        return ""
    query = _FORGET_INTENT.sub(" ", text)
    for word in (
        "我之前",
        "之前",
        "关于",
        "有关",
        "这个",
        "这条",
        "那条",
        "的偏好",
        "偏好",
        "记忆",
        "内容",
        "我",
        "please",
    ):
        query = query.replace(word, " ")
    query = re.sub(r"[，。!！?？:：\s]+", " ", query).strip()
    return query


def has_explicit_memory_intent(user_message: str) -> bool:
    text = user_message.strip()
    if not text or extract_forget_query(text) or is_transient_utterance(text):
        return False
    if _is_memory_meta_question(text):
        return False
    if _REMEMBER_EXPLICIT.search(text):
        return True
    for pattern, _, _ in PREFERENCE_PATTERNS:
        if pattern.search(text):
            return True
    for pattern, _ in PROJECT_PATTERNS:
        if pattern.search(text):
            return True
    return False


def extract_candidates(user_message: str) -> List[Tuple[str, MemoryType]]:
    candidates: List[Tuple[str, MemoryType]] = []
    seen: set = set()
    text = user_message.strip()
    if not text:
        return candidates
    if extract_forget_query(text) or is_transient_utterance(text) or _is_memory_meta_question(text):
        return candidates

    def add(raw: str, mem_type: MemoryType) -> None:
        fragment = normalize_memory_content(_clean_fragment(raw))
        fp = memory_fingerprint(fragment)
        if len(fragment) < 6 or fp in seen or should_exclude(fragment, mem_type.value):
            return
        seen.add(fp)
        candidates.append((fragment, mem_type))

    remember = _REMEMBER_EXPLICIT.search(text)
    if remember:
        add(remember.group(1), MemoryType.USER)
        return candidates

    for pattern, mem_type, prefix in PREFERENCE_PATTERNS:
        for match in pattern.finditer(text):
            add(f"{prefix}{match.group(1)}", mem_type)

    for pattern, mem_type in PROJECT_PATTERNS:
        for match in pattern.finditer(text):
            add(match.group(0), mem_type)

    if not candidates and any(k in text for k in ("喜欢", "讨厌", "偏好")):
        add(text, MemoryType.USER)
    return candidates
