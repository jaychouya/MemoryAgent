"""Tests for Feishu / DingTalk webhook helpers."""

import base64
import hashlib
import hmac
from unittest.mock import AsyncMock, patch

import pytest

from src.agent.chat_webhooks import (
    build_dingtalk_payload,
    build_feishu_payload,
    dingtalk_sign,
    dingtalk_webhook_url,
    feishu_sign,
    send_dingtalk,
    send_feishu,
)


def test_feishu_sign_matches_spec():
    secret = "test-secret"
    ts = "1599360473"
    string_to_sign = f"{ts}\n{secret}"
    expected = base64.b64encode(
        hmac.new(string_to_sign.encode(), b"", hashlib.sha256).digest()
    ).decode()
    assert feishu_sign(secret, ts) == expected


def test_dingtalk_sign_non_empty():
    assert dingtalk_sign("sec", "1234567890000")


def test_build_feishu_payload_without_secret():
    body = build_feishu_payload("hello")
    assert body["msg_type"] == "text"
    assert body["content"]["text"] == "hello"
    assert "sign" not in body


def test_build_feishu_payload_with_secret():
    body = build_feishu_payload("hi", "sec")
    assert body["sign"]
    assert body["timestamp"]


def test_build_dingtalk_payload():
    body = build_dingtalk_payload("ping")
    assert body["text"]["content"] == "ping"


def test_dingtalk_webhook_url_appends_sign():
    url = dingtalk_webhook_url("https://oapi.dingtalk.com/robot/send?access_token=abc", "sec")
    assert "timestamp=" in url
    assert "sign=" in url


@pytest.mark.asyncio
async def test_send_feishu_calls_post():
    with patch("src.agent.chat_webhooks.post_webhook", new_callable=AsyncMock) as mock:
        mock.return_value = {"code": 0}
        await send_feishu("https://example.com/hook", "msg", "sec")
        mock.assert_awaited_once()
        args = mock.await_args
        assert args[0][0] == "https://example.com/hook"
        assert args[0][1]["content"]["text"] == "msg"


@pytest.mark.asyncio
async def test_send_dingtalk_calls_post():
    with patch("src.agent.chat_webhooks.post_webhook", new_callable=AsyncMock) as mock:
        mock.return_value = {"errcode": 0}
        await send_dingtalk("https://oapi.dingtalk.com/robot/send?access_token=x", "msg")
        mock.assert_awaited_once()
