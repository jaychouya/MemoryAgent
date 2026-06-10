"""Tests for Claude Code-style query loop primitives."""
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.agent.loop_state import is_prompt_too_long_error, LoopState, LoopExitReason
from src.agent.tool_executor import build_tool_result_messages, parse_tool_calls
from src.agent.query_loop import execute_query_loop


def test_is_prompt_too_long_error():
    assert is_prompt_too_long_error(Exception("maximum context length exceeded"))
    assert not is_prompt_too_long_error(Exception("network timeout"))


def test_build_tool_result_messages_fills_missing():
    tool_calls = [{"id": "call_1", "function": {"name": "Read", "arguments": "{}"}}]
    results = []
    msgs = build_tool_result_messages(tool_calls, results)
    assert len(msgs) == 1
    assert msgs[0]["tool_call_id"] == "call_1"
    assert "未执行" in msgs[0]["content"] or "错误" in msgs[0]["content"]


def test_parse_tool_calls_json_args():
    raw = [{
        "id": "x",
        "function": {"name": "memory_search", "arguments": '{"query": "python"}'},
    }]
    calls = parse_tool_calls(raw)
    assert calls[0]["params"]["query"] == "python"


@pytest.mark.asyncio
async def test_execute_query_loop_completed_no_tools():
    llm = AsyncMock()
    llm.generate_response = AsyncMock(return_value={
        "content": "你好",
        "stop_reason": "end_turn",
    })
    state = LoopState(messages=[{"role": "user", "content": "hi"}], system_prompt="sys")
    state, reason, content = await execute_query_loop(
        llm, state, tool_registry=None, max_turns=5
    )
    assert reason == LoopExitReason.COMPLETED
    assert content == "你好"
    assert any(m.get("role") == "assistant" for m in state.messages)


@pytest.mark.asyncio
async def test_execute_query_loop_tool_round():
    llm = AsyncMock()
    llm.generate_response = AsyncMock(side_effect=[
        {
            "content": "",
            "stop_reason": "tool_calls",
            "tool_calls": [{
                "id": "c1",
                "type": "function",
                "function": {"name": "memory_search", "arguments": '{"query": "x"}'},
            }],
        },
        {"content": "完成", "stop_reason": "end_turn"},
    ])
    registry = MagicMock()
    registry.get_function_schemas.return_value = []
    from src.agent.tools.base import ToolResult
    registry.execute_parallel = AsyncMock(return_value=[
        ToolResult(success=True, content="found")
    ])
    state = LoopState(messages=[{"role": "user", "content": "搜记忆"}], system_prompt="s")
    state, reason, content = await execute_query_loop(
        llm, state, tool_registry=registry, max_turns=5
    )
    assert reason == LoopExitReason.COMPLETED
    assert "memory_search" in state.tools_called or state.turn_count >= 1
    roles = [m.get("role") for m in state.messages]
    assert "tool" in roles


@pytest.mark.asyncio
async def test_execute_query_loop_allows_web_fetch_after_web_search():
    llm = AsyncMock()
    llm.generate_response = AsyncMock(side_effect=[
        {
            "content": "",
            "stop_reason": "tool_calls",
            "tool_calls": [{
                "id": "c1",
                "type": "function",
                "function": {"name": "web_search", "arguments": '{"query": "2024 数一"}'},
            }],
        },
        {
            "content": "",
            "stop_reason": "tool_calls",
            "tool_calls": [{
                "id": "c2",
                "type": "function",
                "function": {"name": "web_fetch", "arguments": '{"url": "https://example.com"}'},
            }],
        },
        {"content": "正常讲解", "stop_reason": "end_turn"},
    ])

    class Tool:
        def __init__(self, name):
            self.name = name

    registry = MagicMock()
    registry.get_all.return_value = [
        Tool("memory_search"),
        Tool("web_search"),
        Tool("web_fetch"),
    ]
    registry.get_function_schemas.return_value = [{"type": "function"}]
    from src.agent.tools.base import ToolResult
    registry.execute_parallel = AsyncMock(return_value=[
        ToolResult(success=True, content="ok")
    ])

    state = LoopState(messages=[{"role": "user", "content": "查真题"}], system_prompt="s")
    state, reason, content = await execute_query_loop(
        llm, state, tool_registry=registry, max_turns=5
    )

    assert reason == LoopExitReason.COMPLETED
    assert content == "正常讲解"
    assert state.tools_called == ["web_search", "web_fetch"]


@pytest.mark.asyncio
async def test_execute_query_loop_does_not_stream_final_after_tool_call():
    llm = AsyncMock()
    llm.generate_response = AsyncMock(side_effect=[
        {
            "content": "",
            "stop_reason": "tool_calls",
            "tool_calls": [{
                "id": "c1",
                "type": "function",
                "function": {"name": "web_fetch", "arguments": '{"url": "https://example.com"}'},
            }],
        },
        {"content": "最终回复", "stop_reason": "end_turn"},
    ])
    streamed = []

    async def stream_gen(**kwargs):
        cb = kwargs.get("on_token")
        if cb:
            await cb("<tool_call>")
        return {"content": "<tool_call>", "stop_reason": "end_turn", "streamed": True}

    llm.generate_response_stream = stream_gen

    class Tool:
        def __init__(self, name):
            self.name = name

    registry = MagicMock()
    registry.get_all.return_value = [Tool("web_fetch")]
    registry.get_function_schemas.return_value = [{"type": "function"}]
    from src.agent.tools.base import ToolResult
    registry.execute_parallel = AsyncMock(return_value=[
        ToolResult(success=True, content="page")
    ])

    def collect(event):
        if event.type.value == "token":
            streamed.append(event.content)

    state = LoopState(messages=[{"role": "user", "content": "抓网页"}], system_prompt="s")
    _, reason, content = await execute_query_loop(
        llm,
        state,
        tool_registry=registry,
        max_turns=5,
        on_event=collect,
    )

    assert reason == LoopExitReason.COMPLETED
    assert content == "最终回复"
    assert "<tool_call>" not in streamed


@pytest.mark.asyncio
async def test_execute_query_loop_recovers_empty_response_after_tools():
    llm = AsyncMock()
    llm.generate_response = AsyncMock(side_effect=[
        {
            "content": "",
            "stop_reason": "tool_calls",
            "tool_calls": [{
                "id": "c1",
                "type": "function",
                "function": {"name": "web_search", "arguments": '{"query": "test"}'},
            }],
        },
        {"content": "", "stop_reason": "end_turn"},
        {"content": "", "stop_reason": "end_turn"},
    ])

    class Tool:
        def __init__(self, name):
            self.name = name

    registry = MagicMock()
    registry.get_all.return_value = [Tool("web_search"), Tool("web_fetch")]
    registry.get_function_schemas.return_value = [{"type": "function"}]
    from src.agent.tools.base import ToolResult
    registry.execute_parallel = AsyncMock(return_value=[
        ToolResult(success=True, content="搜索结果：2024考研数一真题链接")
    ])

    streamed = []

    def collect(event):
        if event.type.value == "token":
            streamed.append(event.content)

    state = LoopState(messages=[{"role": "user", "content": "查真题"}], system_prompt="s")
    state, reason, content = await execute_query_loop(
        llm,
        state,
        tool_registry=registry,
        max_turns=6,
        on_event=collect,
    )

    assert reason == LoopExitReason.COMPLETED
    assert content.strip()
    assert "工具结果" in content or "搜索结果" in content
    assert any("2024考研" in s for s in streamed)


@pytest.mark.asyncio
async def test_reactive_compact_on_prompt_too_long():
    llm = AsyncMock()
    llm.generate_response = AsyncMock(side_effect=[
        Exception("maximum context length exceeded"),
        {"content": "ok", "stop_reason": "end_turn"},
    ])
    compressor = AsyncMock()
    compressor.compress = AsyncMock(return_value=[{"role": "user", "content": "short"}])
    state = LoopState(messages=[{"role": "user", "content": "x" * 10000}], system_prompt="s")
    state, reason, _ = await execute_query_loop(
        llm, state, context_compressor=compressor, max_turns=3
    )
    assert compressor.compress.called
    assert reason == LoopExitReason.COMPLETED
    assert state.has_attempted_reactive_compact is False
