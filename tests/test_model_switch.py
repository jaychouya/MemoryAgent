"""Tests for per-request chat model override."""

import pytest
from httpx import AsyncClient, ASGITransport

from src.backend.api.chat import ChatRequest, _resolve_llm, _resolve_memory_llm
from src.backend.main import app

_FAKE_KEY = "tp-c4c6vadl3zoct12deob7z67a3kv9em487ch7sus3u5kx0rg9"


def test_resolve_llm_model_override(monkeypatch):
    import src.backend.api.chat as chat_mod

    monkeypatch.setattr(chat_mod, "_apply_persisted_model_config", lambda: None)
    monkeypatch.setattr(
        chat_mod,
        "global_model_config",
        {
            "api_key": _FAKE_KEY,
            "base_url": "https://example.com/v1",
            "model": "mimo-v2.5-pro",
            "memory_model": "auto",
        },
    )
    req = ChatRequest(message="hi", model_override="mimo-v2.5")
    llm = _resolve_llm(req)
    assert llm.model == "mimo-v2.5"


def test_resolve_memory_llm_auto_lite(monkeypatch):
    import src.backend.api.chat as chat_mod
    from src.backend.services import LLMService

    monkeypatch.setattr(chat_mod, "_apply_persisted_model_config", lambda: None)
    monkeypatch.setattr(
        chat_mod,
        "global_model_config",
        {
            "api_key": _FAKE_KEY,
            "base_url": "https://example.com/v1",
            "model": "mimo-v2.5-pro",
        },
    )
    chat_llm = LLMService(
        api_key=_FAKE_KEY,
        model="mimo-v2.5-pro",
        base_url="https://example.com/v1",
    )
    mem = _resolve_memory_llm(chat_llm)
    assert mem.model != "mimo-v2.5-pro"
    assert "mimo" in mem.model


@pytest.mark.asyncio
async def test_config_returns_memory_model(monkeypatch):
    import src.backend.api.chat as chat_mod

    monkeypatch.setattr(chat_mod, "_apply_persisted_model_config", lambda: None)
    monkeypatch.setattr(
        chat_mod,
        "global_model_config",
        {
            "api_key": _FAKE_KEY,
            "base_url": "https://example.com/v1",
            "model": "mimo-v2.5-pro",
            "memory_model": "mimo-v2.5",
        },
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/config")
    assert r.status_code == 200
    data = r.json()
    assert data["configured"] is True
    assert data["memory_model"] == "mimo-v2.5"
