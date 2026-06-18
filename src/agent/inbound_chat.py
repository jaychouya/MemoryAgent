"""Handle inbound IM messages: chat + optional outbound reply."""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


async def run_inbound_chat(
    text: str,
    *,
    user_id: str,
    session_id: str,
    project_id: Optional[str] = None,
) -> str:
    from src.backend.api.chat import ChatRequest, _execute_chat

    request = ChatRequest(
        message=text,
        session_id=session_id,
        user_id=user_id,
        project_id=project_id,
        cross_session_memory=False,
    )
    try:
        result = await _execute_chat(request)
        return (result.content or "").strip() or "（无回复内容）"
    except Exception as e:
        logger.error("Inbound chat failed: %s", e, exc_info=True)
        return f"处理失败：{e}"


async def reply_via_integration(channel: str, text: str) -> bool:
    from src.agent.integrations import get_integration_manager

    manager = get_integration_manager()
    provider = manager.get_provider(channel)
    if not provider:
        logger.warning("Inbound reply skipped: %s not connected", channel)
        return False
    try:
        return await provider.send_data({"text": text})
    except Exception as e:
        logger.warning("Inbound reply via %s failed: %s", channel, e)
        return False


async def process_inbound_and_reply(
    channel: str,
    text: str,
    *,
    user_id: str,
    session_id: str,
    project_id: Optional[str] = None,
) -> str:
    reply = await run_inbound_chat(
        text,
        user_id=user_id,
        session_id=session_id,
        project_id=project_id,
    )
    await reply_via_integration(channel, reply[:3500])
    return reply
