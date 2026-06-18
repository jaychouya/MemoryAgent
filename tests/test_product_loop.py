"""Tests for recall health hints and integration notify."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.memory.recall_health import diagnose_recall
from src.agent.integration_notify import _summarize_writes, notify_memory_writes
from src.memory.write_pipeline import TurnWriteOutcome


def test_recall_health_hints_empty_unexpected():
    h = diagnose_recall("long query", [], user_memory_count=5)
    assert h["status"] == "empty_unexpected"
    assert len(h["hints"]) >= 2


def test_recall_health_hints_no_corpus():
    h = diagnose_recall("", [], user_memory_count=0)
    assert h["status"] == "empty_no_corpus"
    assert h["hints"]


def test_summarize_writes_empty():
    assert _summarize_writes(TurnWriteOutcome()) == ""


def test_summarize_writes_stored():
    text = _summarize_writes(
        TurnWriteOutcome(stored=[{"content": "喜欢 Python", "memory_id": "m1"}])
    )
    assert "沉淀" in text
    assert "Python" in text


@pytest.mark.asyncio
async def test_notify_skips_when_no_writes():
    await notify_memory_writes(TurnWriteOutcome())


@pytest.mark.asyncio
async def test_notify_sends_to_connected_provider():
    outcome = TurnWriteOutcome(stored=[{"content": "test", "memory_id": "x"}])
    provider = MagicMock()
    provider.send_data = AsyncMock(return_value=True)
    manager = MagicMock()
    manager.get_provider = MagicMock(side_effect=lambda i: provider if i == "feishu" else None)
    with patch("src.agent.integrations.get_integration_manager", return_value=manager):
        await notify_memory_writes(outcome)
    provider.send_data.assert_awaited_once()
