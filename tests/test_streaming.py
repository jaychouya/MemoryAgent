"""Tests for streaming support."""
import pytest
import json
from src.agent.streaming import StreamingManager, StreamEvent, StreamEventType


def test_streaming_creates_events():
    """StreamingManager 应该能创建事件。"""
    manager = StreamingManager()
    
    event = manager.create_token_event("Hello")
    
    assert event.type == StreamEventType.TOKEN
    assert event.content == "Hello"
    assert len(manager.get_events()) == 1


def test_streaming_handles_token():
    """StreamingManager 应该能处理 token 事件。"""
    manager = StreamingManager()
    
    event = manager.create_token_event("Hello")
    sse = event.to_sse()
    
    assert "data:" in sse
    assert "Hello" in sse
    assert "token" in sse


def test_streaming_handles_tool_call():
    """StreamingManager 应该能处理工具调用事件。"""
    manager = StreamingManager()
    
    event = manager.create_tool_call_event("search", {"query": "test"})
    sse = event.to_sse()
    
    assert "tool_call" in sse
    assert "search" in sse


def test_streaming_handles_tool_result():
    """StreamingManager 应该能处理工具结果事件。"""
    manager = StreamingManager()
    
    event = manager.create_tool_result_event("search", "result data")
    sse = event.to_sse()
    
    assert "tool_result" in sse
    assert "result data" in sse


def test_streaming_handles_error():
    """StreamingManager 应该能处理错误事件。"""
    manager = StreamingManager()
    
    event = manager.create_error_event("Something went wrong")
    sse = event.to_sse()
    
    assert "error" in sse
    assert "Something went wrong" in sse


def test_streaming_handles_done():
    """StreamingManager 应该能处理完成事件。"""
    manager = StreamingManager()
    
    event = manager.create_done_event()
    sse = event.to_sse()
    
    assert "done" in sse


def test_streaming_clears_events():
    """StreamingManager 应该能清空事件。"""
    manager = StreamingManager()
    
    manager.create_token_event("Hello")
    manager.create_token_event("World")
    assert len(manager.get_events()) == 2
    
    manager.clear()
    assert len(manager.get_events()) == 0


@pytest.mark.asyncio
async def test_streaming_streams_response():
    """StreamingManager 应该能流式传输响应。"""
    manager = StreamingManager()
    
    async def mock_generator():
        yield "Hello"
        yield " "
        yield "World"
    
    events = []
    async for event in manager.stream_response(mock_generator()):
        events.append(event)
    
    assert len(events) == 4  # 3 tokens + done
    assert "Hello" in events[0]
    assert "done" in events[-1]
