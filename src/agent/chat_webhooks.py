"""Feishu (Lark) and DingTalk custom bot webhooks."""

from __future__ import annotations

import base64
import hashlib
import hmac
import time
from typing import Any, Dict, Optional
from urllib.parse import quote_plus


def feishu_sign(secret: str, timestamp: str) -> str:
    string_to_sign = f"{timestamp}\n{secret}"
    digest = hmac.new(string_to_sign.encode("utf-8"), b"", hashlib.sha256).digest()
    return base64.b64encode(digest).decode("utf-8")


def dingtalk_sign(secret: str, timestamp: str) -> str:
    string_to_sign = f"{timestamp}\n{secret}"
    digest = hmac.new(
        secret.encode("utf-8"),
        string_to_sign.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return quote_plus(base64.b64encode(digest).decode("utf-8"))


def build_feishu_payload(text: str, secret: Optional[str] = None) -> Dict[str, Any]:
    body: Dict[str, Any] = {
        "msg_type": "text",
        "content": {"text": text},
    }
    if secret:
        ts = str(int(time.time()))
        body["timestamp"] = ts
        body["sign"] = feishu_sign(secret, ts)
    return body


def build_dingtalk_payload(text: str) -> Dict[str, Any]:
    return {"msg_type": "text", "text": {"content": text}}


def dingtalk_webhook_url(webhook_url: str, secret: Optional[str] = None) -> str:
    if not secret:
        return webhook_url
    ts = str(round(time.time() * 1000))
    sign = dingtalk_sign(secret, ts)
    sep = "&" if "?" in webhook_url else "?"
    return f"{webhook_url}{sep}timestamp={ts}&sign={sign}"


async def post_webhook(url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    import httpx

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict):
            err = data.get("errcode") or data.get("code")
            if err not in (None, 0, "0"):
                msg = data.get("errmsg") or data.get("msg") or str(data)
                raise RuntimeError(msg)
        return data if isinstance(data, dict) else {"ok": True}


async def send_feishu(
    webhook_url: str,
    text: str,
    secret: Optional[str] = None,
) -> Dict[str, Any]:
    return await post_webhook(
        webhook_url,
        build_feishu_payload(text, secret),
    )


async def send_dingtalk(
    webhook_url: str,
    text: str,
    secret: Optional[str] = None,
) -> Dict[str, Any]:
    return await post_webhook(
        dingtalk_webhook_url(webhook_url, secret),
        build_dingtalk_payload(text),
    )
