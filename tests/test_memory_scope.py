"""Tests for per-session vs cross-session memory scope."""
from src.backend.api.chat import ChatRequest, _memory_user_id


def test_memory_scope_is_session_local_by_default():
    req = ChatRequest(message="hello", user_id="u1", session_id="s1")
    assert req.cross_session_memory is False
    assert _memory_user_id("u1", "s1", req.cross_session_memory) == "u1:s1"


def test_memory_scope_is_global_when_cross_session_enabled():
    req = ChatRequest(
        message="hello",
        user_id="u1",
        session_id="s1",
        cross_session_memory=True,
    )
    assert _memory_user_id("u1", "s1", req.cross_session_memory) == "u1"
