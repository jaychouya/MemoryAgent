import pytest
from src.utils.config import Settings


def test_settings_default_values():
    """Test that settings have correct default values."""
    settings = Settings()
    assert settings.APP_NAME == "MemoMind"
    assert settings.DEBUG == False
    assert settings.REDIS_URL == "redis://localhost:6379"
    assert settings.WORKING_MEMORY_TTL == 3600
    assert settings.SHORT_TERM_MEMORY_DAYS == 30
    assert settings.MAX_CONTEXT_MESSAGES == 20


def test_settings_from_env(monkeypatch):
    """Test that settings can be loaded from environment."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")
    monkeypatch.setenv("DEBUG", "true")
    
    settings = Settings()
    assert settings.OPENAI_API_KEY == "test-key-123"
    assert settings.DEBUG == True


def test_autonomous_actions_list():
    """Test that autonomous actions are configured."""
    settings = Settings()
    assert "memory_search" in settings.AUTONOMOUS_ACTIONS
    assert "response_generation" in settings.AUTONOMOUS_ACTIONS


def test_forbidden_actions_list():
    """Test that forbidden actions are configured."""
    settings = Settings()
    assert "financial_transaction" in settings.FORBIDDEN_ACTIONS
