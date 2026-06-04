"""Post-turn memory write: LLM extract (primary) + regex (supplement)."""

import logging
from typing import List, Tuple

from src.memory.manager import MemoryManager
from src.memory.types import MemoryType
from src.memory.exclusions import should_exclude
from src.memory.llm_extractor import extract_memories_from_turn
from src.memory.auto_write import extract_candidates, is_duplicate, TYPE_MAP
from src.utils.config import settings
from src.memory.provenance import append_l0_turn, l0_path, pick_source_quote
from pathlib import Path

logger = logging.getLogger(__name__)


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
        key = content.strip().lower()
        if key in seen or len(key) < 6:
            continue
        if should_exclude(content, mem_type.value):
            continue
        seen.add(key)
        out.append((content.strip(), mem_type))
    return out


async def persist_turn_memories(
    memory: MemoryManager,
    user_message: str,
    assistant_message: str,
    user_id: str,
    session_id: str = None,
    project_id: str = None,
) -> List[str]:
    candidates: List[Tuple[str, MemoryType]] = []

    if memory.llm and should_use_llm_extract(user_message, assistant_message):
        for item in await extract_memories_from_turn(
            memory.llm, user_message, assistant_message
        ):
            t = TYPE_MAP.get(item["type"], MemoryType.USER)
            candidates.append((item["content"], t))

    for content, mem_type in extract_candidates(user_message):
        candidates.append((content, mem_type))

    candidates = _dedupe_candidates(candidates)
    stored_ids = []

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
            stored_ids.append(item.id)
            logger.info(f"Write pipeline stored {item.id} for {user_id}")

    return stored_ids
