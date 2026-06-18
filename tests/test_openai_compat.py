"""Tests for OpenAI-compatible /v1 endpoints."""

import pytest
from httpx import AsyncClient, ASGITransport

from src.backend.main import app


@pytest.mark.asyncio
async def test_list_models():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/v1/models")
    assert r.status_code == 200
    data = r.json()
    assert data["object"] == "list"
    assert any(m["id"] == "memoryagent" for m in data["data"])


@pytest.mark.asyncio
async def test_chat_completions_shape():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(
            "/v1/chat/completions",
            json={
                "model": "memoryagent",
                "messages": [{"role": "user", "content": "hi"}],
                "user": "openai-test-user",
            },
        )
    assert r.status_code == 200
    data = r.json()
    assert data["object"] == "chat.completion"
    assert data["choices"][0]["message"]["role"] == "assistant"
    assert "content" in data["choices"][0]["message"]


@pytest.mark.asyncio
async def test_chat_completions_requires_user_message():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(
            "/v1/chat/completions",
            json={
                "model": "memoryagent",
                "messages": [{"role": "assistant", "content": "only assistant"}],
            },
        )
    assert r.status_code == 400
