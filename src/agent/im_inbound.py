"""Parse inbound IM webhook payloads (Feishu / DingTalk)."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional, Tuple


def parse_feishu_inbound(body: Dict[str, Any]) -> Optional[Tuple[str, str, str]]:
    if body.get("type") == "url_verification":
        return None
    if body.get("challenge") and not body.get("header"):
        return None

    header = body.get("header") or {}
    event_type = header.get("event_type") or body.get("event_type") or ""
    if event_type and event_type != "im.message.receive_v1":
        return None

    event = body.get("event") or body
    message = event.get("message") or {}
    if message.get("message_type") not in (None, "text"):
        return None

    raw = message.get("content") or ""
    text = _extract_text_content(raw)
    if not text:
        return None

    sender = event.get("sender") or {}
    sender_id = sender.get("sender_id") or {}
    user_id = (
        sender_id.get("user_id")
        or sender_id.get("open_id")
        or sender.get("user_id")
        or "feishu-user"
    )
    chat_id = message.get("chat_id") or event.get("chat_id") or user_id
    return text.strip(), str(user_id), str(chat_id)


def parse_dingtalk_inbound(body: Dict[str, Any]) -> Optional[Tuple[str, str, str]]:
    msgtype = body.get("msgtype") or body.get("MsgType")
    if msgtype and str(msgtype).lower() != "text":
        return None

    text_block = body.get("text") or body.get("Text") or {}
    if isinstance(text_block, str):
        text = text_block
    else:
        text = text_block.get("content") or text_block.get("Content") or ""

    if not str(text).strip():
        return None

    user_id = str(body.get("senderId") or body.get("senderStaffId") or "dingtalk-user")
    session_id = str(
        body.get("conversationId")
        or body.get("chatbotUserId")
        or body.get("sessionWebhook")
        or user_id
    )
    return str(text).strip(), user_id, session_id


def feishu_url_verification_challenge(body: Dict[str, Any]) -> Optional[str]:
    if body.get("type") == "url_verification":
        return body.get("challenge")
    if body.get("challenge") and not body.get("header") and not body.get("event"):
        return body.get("challenge")
    return None


def _extract_text_content(raw: Any) -> str:
    if isinstance(raw, dict):
        return str(raw.get("text") or raw.get("content") or "").strip()
    if not isinstance(raw, str):
        return ""
    raw = raw.strip()
    if not raw:
        return ""
    if raw.startswith("{"):
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                return str(data.get("text") or data.get("content") or "").strip()
        except json.JSONDecodeError:
            pass
    return raw
