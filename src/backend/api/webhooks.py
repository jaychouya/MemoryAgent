"""Inbound webhooks: Feishu / DingTalk → MemoryAgent chat → outbound reply."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request
from pydantic import BaseModel, Field

from src.agent.im_inbound import (
    feishu_url_verification_challenge,
    parse_dingtalk_inbound,
    parse_feishu_inbound,
)
from src.agent.inbound_chat import process_inbound_and_reply
from src.agent.integrations import get_integration_manager
from src.utils.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


class InboundTestRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
    user_id: str = "test-user"
    session_id: str = "test-session"


def _inbound_token_ok(channel: str, token: Optional[str]) -> bool:
    expected = (settings.MEMORYAGENT_WEBHOOK_INBOUND_TOKEN or "").strip()
    if expected:
        return (token or "").strip() == expected
    manager = get_integration_manager()
    creds = manager.credentials.get(channel)
    if creds:
        stored = (creds.credentials.get("inbound_token") or "").strip()
        if stored:
            return (token or "").strip() == stored
    return True


def _feishu_verification_token_ok(body: Dict[str, Any]) -> bool:
    header = body.get("header") or {}
    token = header.get("token") or body.get("token") or ""
    manager = get_integration_manager()
    creds = manager.credentials.get("feishu")
    if not creds:
        return True
    expected = (creds.credentials.get("verification_token") or "").strip()
    if not expected:
        return True
    return token == expected


@router.post("/webhooks/feishu")
async def feishu_inbound(
    request: Request,
    background_tasks: BackgroundTasks,
    token: Optional[str] = Query(default=None),
):
    if not _inbound_token_ok("feishu", token):
        raise HTTPException(status_code=401, detail="Invalid inbound token")

    body = await request.json()
    challenge = feishu_url_verification_challenge(body)
    if challenge:
        return {"challenge": challenge}

    if not _feishu_verification_token_ok(body):
        raise HTTPException(status_code=401, detail="Invalid Feishu verification token")

    parsed = parse_feishu_inbound(body)
    if not parsed:
        return {"code": 0, "msg": "ignored"}

    text, user_id, session_id = parsed
    background_tasks.add_task(
        process_inbound_and_reply,
        "feishu",
        text,
        user_id=user_id,
        session_id=session_id,
    )
    return {"code": 0}


@router.post("/webhooks/dingtalk")
async def dingtalk_inbound(
    request: Request,
    background_tasks: BackgroundTasks,
    token: Optional[str] = Query(default=None),
):
    if not _inbound_token_ok("dingtalk", token):
        raise HTTPException(status_code=401, detail="Invalid inbound token")

    body = await request.json()
    parsed = parse_dingtalk_inbound(body)
    if not parsed:
        return {"errcode": 0, "errmsg": "ignored"}

    text, user_id, session_id = parsed
    background_tasks.add_task(
        process_inbound_and_reply,
        "dingtalk",
        text,
        user_id=user_id,
        session_id=session_id,
    )
    return {"errcode": 0, "errmsg": "ok"}


@router.post("/webhooks/{channel}/test-inbound")
async def test_inbound(
    channel: str,
    body: InboundTestRequest,
    token: Optional[str] = Query(default=None),
):
    if channel not in ("feishu", "dingtalk"):
        raise HTTPException(status_code=400, detail="channel must be feishu or dingtalk")
    if not _inbound_token_ok(channel, token):
        raise HTTPException(status_code=401, detail="Invalid inbound token")

    reply = await process_inbound_and_reply(
        channel,
        body.text,
        user_id=body.user_id,
        session_id=body.session_id,
    )
    return {"status": "ok", "reply": reply}
