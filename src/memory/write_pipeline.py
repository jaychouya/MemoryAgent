"""Post-turn memory write: LLM extract (primary) + regex (supplement)."""

import logging
from dataclasses import dataclass, field
from typing import List, Tuple

from src.memory.manager import MemoryManager
from src.memory.types import MemoryType
from src.memory.exclusions import should_exclude
from src.memory.llm_extractor import extract_memories_from_turn
from src.memory.auto_write import (
    extract_candidates,
    extract_forget_query,
    is_duplicate,
    memory_fingerprint,
    texts_similar,
    TYPE_MAP,
)
from src.utils.config import settings
from src.memory.provenance import append_l0_turn, l0_path, pick_source_quote
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class TurnWriteOutcome:
    stored: List[dict] = field(default_factory=list)
    deleted: List[dict] = field(default_factory=list)

    @property
    def stored_ids(self) -> List[str]:
        return [x["memory_id"] for x in self.stored if x.get("memory_id")]


def should_use_llm_extract(user_message: str, assistant_message: str) -> bool:
    if not settings.MEMORY_EXTRACT_ENABLED:
        return False
    total = len(user_message or "") + len(assistant_message or "")
    return total >= settings.MEMORY_EXTRACT_LLM_MIN_CHARS


def _dedupe_candidates(
    items: List[Tuple[str, MemoryType]],
) -> List[Tuple[str, MemoryType]]:
    seen = set()
    out = []
    for content, mem_type in items:
        fragment = content.strip()
        fp = memory_fingerprint(fragment)
        if fp in seen or len(fragment) < 6:
            continue
        if should_exclude(fragment, mem_type.value):
            continue
        seen.add(fp)
        out.append((fragment, mem_type))
    return out


async def _is_duplicate_in_storage(
    memory: MemoryManager,
    content: str,
    user_id: str,
    project_id: str = None,
) -> bool:
    rows = await memory.list_memories(user_id=user_id, project_id=project_id, limit=200)
    for row in rows:
        existing = row.get("content") or ""
        if memory_fingerprint(existing) == memory_fingerprint(content):
            return True
        if texts_similar(existing, content):
            return True
    return False


def _memory_matches_forget_query(content: str, query: str) -> bool:
    haystack = content.lower()
    tokens = [t.lower() for t in query.split() if len(t.strip()) >= 2]
    if not tokens:
        return False
    return all(token in haystack for token in tokens)


async def _delete_matching_memories(
    memory: MemoryManager,
    query: str,
    user_id: str,
    project_id: str = None,
) -> List[Tuple[str, str]]:
    rows = await memory.list_memories(user_id=user_id, project_id=project_id, limit=200)
    deleted = []
    for row in rows:
        content = row.get("content") or ""
        memory_id = row.get("memory_id") or row.get("id")
        if memory_id and _memory_matches_forget_query(content, query):
            if await memory.delete_memory(memory_id):
                deleted.append((memory_id, content[:200]))
    return deleted


async def persist_turn_memories(
    memory: MemoryManager,
    user_message: str,
    assistant_message: str,
    user_id: str,
    session_id: str = None,
    project_id: str = None,
) -> TurnWriteOutcome:
    forget_query = extract_forget_query(user_message)
    if forget_query:
        removed = await _delete_matching_memories(memory, forget_query, user_id, project_id)
        return TurnWriteOutcome(
            deleted=[
                {"memory_id": mid, "content": content}
                for mid, content in removed
            ]
        )

    candidates: List[Tuple[str, MemoryType]] = []
    regex_candidates = extract_candidates(user_message)

    if regex_candidates:
        candidates = regex_candidates
    elif memory.llm and should_use_llm_extract(user_message, assistant_message):
        for item in await extract_memories_from_turn(
            memory.llm, user_message, assistant_message
        ):
            t = TYPE_MAP.get(item["type"], MemoryType.USER)
            candidates.append((item["content"], t))

    candidates = _dedupe_candidates(candidates)
    stored = []

    provenance_base = {}
    if settings.PROVENANCE_ENABLED and session_id:
        turn_index = append_l0_turn(
            memory.storage_dir,
            user_id,
            session_id,
            user_message,
            assistant_message,
        )
        rel_l0 = str(
            l0_path(memory.storage_dir, user_id, session_id).relative_to(
                Path(memory.storage_dir)
            )
        )
        provenance_base = {
            "evidence_level": "L1",
            "source_session_id": session_id,
            "source_turn": turn_index,
            "l0_path": rel_l0,
        }

    for content, mem_type in candidates:
        if is_duplicate(user_id, content):
            continue
        if await _is_duplicate_in_storage(memory, content, user_id, project_id):
            continue
        meta = {
            "user_id": user_id,
            "source": "write_pipeline",
            "session_id": session_id,
        }
        if project_id:
            meta["project_id"] = project_id
        if provenance_base:
            meta = {
                **meta,
                **provenance_base,
                "source_quote": pick_source_quote(user_message, content),
            }
        item = await memory.store(
            content=content,
            memory_type=mem_type,
            description=f"自动沉淀: {content[:30]}",
            user_id=user_id,
            metadata=meta,
        )
        if item:
            stored.append({
                "memory_id": item.id,
                "content": content[:200],
                "type": mem_type.value,
            })
            logger.info(f"Write pipeline stored {item.id} for {user_id}")

    return TurnWriteOutcome(stored=stored)
