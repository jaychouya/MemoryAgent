"""Shared recall + health + trust bump for chat loop and MCP."""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple

from src.memory.citations import build_citations
from src.memory.recall_health import diagnose_recall
from src.memory.recall_judge import filter_relevant_memories

logger = logging.getLogger(__name__)


async def recall_for_prompt(
    memory_manager,
    query: str,
    user_id: str,
    *,
    project_id: Optional[str] = None,
    session_id: Optional[str] = None,
    top_k: int = 5,
    fast: bool = True,
    filter_judge: bool = True,
) -> Tuple[List[Dict], List, Dict]:
    if not memory_manager or not user_id:
        return [], [], diagnose_recall(query, [], user_memory_count=0)

    try:
        user_count = await memory_manager.count_memories(user_id, project_id)
        raw = await memory_manager.retrieve(
            user_id=user_id,
            query=query,
            session_id=session_id,
            project_id=project_id,
            top_k=top_k,
            fast=fast,
        )
        memories = filter_relevant_memories(query, raw) if filter_judge else raw
        citations = build_citations(memories)
        reason = (raw[0].get("selection_reason") if raw else "") or ""
        health = diagnose_recall(
            query,
            memories,
            user_memory_count=user_count,
            selection_reason=reason,
        )
        ids = [
            m.get("memory_id") or m.get("id")
            for m in memories
            if m.get("memory_id") or m.get("id")
        ]
        if ids:
            asyncio.create_task(memory_manager.record_recall_usage(ids))
        return memories, citations, health
    except Exception as e:
        logger.warning(f"Memory retrieval failed: {e}")
        return [], [], diagnose_recall(query, [], user_memory_count=0, error=str(e))
