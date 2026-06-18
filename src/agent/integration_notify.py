"""Push memory events to connected chat webhooks (Feishu / DingTalk)."""

from __future__ import annotations

import logging
from typing import List

from src.memory.write_pipeline import TurnWriteOutcome

logger = logging.getLogger(__name__)

_NOTIFY_IDS = ("feishu", "dingtalk")


def _summarize_writes(outcome: TurnWriteOutcome) -> str:
    stored = len(outcome.stored or [])
    deleted = len(outcome.deleted or [])
    parts: List[str] = []
    if stored:
        parts.append(f"沉淀 {stored} 条")
    if deleted:
        parts.append(f"删除 {deleted} 条")
    if not parts:
        return ""
    preview = ""
    if outcome.stored:
        preview = (outcome.stored[0].get("content") or "")[:80]
    msg = f"MemoryAgent：{'，'.join(parts)}"
    if preview:
        msg += f"\n{preview}"
    return msg


async def notify_memory_writes(outcome: TurnWriteOutcome) -> None:
    text = _summarize_writes(outcome)
    if not text:
        return
    try:
        from src.agent.integrations import get_integration_manager

        manager = get_integration_manager()
        for integration_id in _NOTIFY_IDS:
            provider = manager.get_provider(integration_id)
            if not provider:
                continue
            try:
                await provider.send_data({"text": text})
            except Exception as e:
                logger.warning("Notify %s failed: %s", integration_id, e)
    except Exception as e:
        logger.warning("Integration notify failed: %s", e)
