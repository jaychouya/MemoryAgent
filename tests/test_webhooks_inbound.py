"""Tests for inbound webhooks."""

import pytest
from httpx import AsyncClient, ASGITransport

from src.backend.main import app
from src.utils.config import settings


@pytest.mark.asyncio
async def test_feishu_challenge():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(
            "/api/webhooks/feishu",
            json={"type": "url_verification", "challenge": "xyz"},
        )
    assert r.status_code == 200
    assert r.json()["challenge"] == "xyz"


@pytest.mark.asyncio
async def test_feishu_ignores_non_message():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(
            "/api/webhooks/feishu",
            json={"header": {"event_type": "app.open"}, "event": {}},
        )
    assert r.status_code == 200
    assert r.json().get("code") == 0


@pytest.mark.asyncio
async def test_inbound_token_required_when_configured(monkeypatch):
    monkeypatch.setattr(settings, "MEMORYAGENT_WEBHOOK_INBOUND_TOKEN", "secret123")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(
            "/api/webhooks/dingtalk",
            json={"msgtype": "text", "text": {"content": "hi"}, "senderId": "a", "conversationId": "b"},
        )
        assert r.status_code == 401
        r2 = await client.post(
            "/api/webhooks/dingtalk?token=secret123",
            json={"msgtype": "text", "text": {"content": "hi"}, "senderId": "a", "conversationId": "b"},
        )
        assert r2.status_code == 200
