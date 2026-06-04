import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.backend.auth import APIKeyMiddleware, verify_api_key
from src.utils.config import settings


@pytest.fixture
def auth_client(monkeypatch):
    monkeypatch.setattr(settings, "MEMORYAGENT_API_KEY", "test-secret-key")
    app = FastAPI()
    app.add_middleware(APIKeyMiddleware)

    @app.get("/health")
    def health():
        return {"ok": True}

    @app.get("/api/ping")
    def ping():
        return {"pong": True}

    return TestClient(app)


def test_verify_disabled_when_no_key(monkeypatch):
    monkeypatch.setattr(settings, "MEMORYAGENT_API_KEY", None)
    assert verify_api_key(None) is True
    assert verify_api_key("wrong") is True


def test_api_requires_key_when_configured(auth_client):
    r = auth_client.get("/api/ping")
    assert r.status_code == 401
    r = auth_client.get("/api/ping", headers={"X-API-Key": "test-secret-key"})
    assert r.status_code == 200
    assert r.json()["pong"] is True


def test_health_public_without_key(auth_client):
    r = auth_client.get("/health")
    assert r.status_code == 200
