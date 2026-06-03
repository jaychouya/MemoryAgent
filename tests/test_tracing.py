"""Tests for execution tracing system."""
import pytest
from datetime import datetime
from src.agent.tracing import (
    ExecutionTracer,
    TraceEventType,
    TraceEvent,
    Trace,
    get_tracer
)


def test_tracer_creates():
    """ExecutionTracer 应该能创建。"""
    tracer = ExecutionTracer()
    assert tracer is not None


def test_start_trace():
    """start_trace 应该创建新追踪。"""
    tracer = ExecutionTracer()
    
    trace_id = tracer.start_trace(metadata={"user_id": "test"})
    
    assert trace_id is not None
    assert trace_id.startswith("trace_")
    assert tracer.get_trace(trace_id) is not None


def test_end_trace():
    """end_trace 应该结束追踪。"""
    tracer = ExecutionTracer()
    
    trace_id = tracer.start_trace()
    tracer.end_trace(trace_id, status="success")
    
    trace = tracer.get_trace(trace_id)
    assert trace.ended_at is not None
    assert trace.duration_ms is not None


def test_trace_tool_call():
    """trace_tool_call 应该记录工具调用。"""
    tracer = ExecutionTracer()
    
    trace_id = tracer.start_trace()
    event_id = tracer.trace_tool_call(
        tool_name="memory_search",
        arguments={"query": "test"}
    )
    
    assert event_id is not None
    
    trace = tracer.get_trace(trace_id)
    assert len(trace.events) == 2  # start + tool_call


def test_trace_tool_result():
    """trace_tool_result 应该记录工具结果。"""
    tracer = ExecutionTracer()
    
    trace_id = tracer.start_trace()
    tracer.trace_tool_result(
        tool_name="memory_search",
        result="found 3 memories",
        success=True,
        duration_ms=150.5
    )
    
    trace = tracer.get_trace(trace_id)
    assert len(trace.events) == 2  # start + tool_result


def test_trace_llm_call():
    """trace_llm_call 应该记录 LLM 调用。"""
    tracer = ExecutionTracer()
    
    trace_id = tracer.start_trace()
    event_id = tracer.trace_llm_call(
        model="gpt-4o",
        messages=[{"role": "user", "content": "test"}]
    )
    
    assert event_id is not None


def test_trace_llm_response():
    """trace_llm_response 应该记录 LLM 响应。"""
    tracer = ExecutionTracer()
    
    trace_id = tracer.start_trace()
    tracer.trace_llm_response(
        model="gpt-4o",
        response="Hello",
        usage={"input_tokens": 10, "output_tokens": 5},
        duration_ms=500.0
    )
    
    trace = tracer.get_trace(trace_id)
    assert trace.token_usage["total_tokens"] == 15


def test_trace_error():
    """trace_error 应该记录错误。"""
    tracer = ExecutionTracer()
    
    trace_id = tracer.start_trace()
    tracer.trace_error(
        error="Something went wrong",
        context={"tool": "memory_search"}
    )
    
    trace = tracer.get_trace(trace_id)
    error_events = [
        e for e in trace.events
        if e.event_type == TraceEventType.ERROR
    ]
    assert len(error_events) == 1


def test_get_recent_traces():
    """get_recent_traces 应该返回最近的追踪。"""
    tracer = ExecutionTracer()
    
    # 创建多个追踪
    for i in range(5):
        tracer.start_trace()
        tracer.end_trace()
    
    recent = tracer.get_recent_traces(limit=3)
    
    assert len(recent) == 3


def test_get_stats():
    """get_stats 应该返回统计信息。"""
    tracer = ExecutionTracer()
    
    # 创建一个追踪
    trace_id = tracer.start_trace()
    tracer.trace_llm_response(
        model="gpt-4o",
        response="test",
        usage={"input_tokens": 100, "output_tokens": 50},
        duration_ms=500.0
    )
    tracer.end_trace()
    
    stats = tracer.get_stats()
    
    assert stats["total_traces"] == 1
    assert stats["completed_traces"] == 1
    assert stats["total_tokens"] == 150


def test_token_usage():
    """token_usage 应该计算 token 使用量。"""
    tracer = ExecutionTracer()
    
    trace_id = tracer.start_trace()
    
    # 添加多个 LLM 响应
    tracer.trace_llm_response(
        model="gpt-4o",
        response="test1",
        usage={"input_tokens": 100, "output_tokens": 50},
        duration_ms=500.0
    )
    tracer.trace_llm_response(
        model="gpt-4o",
        response="test2",
        usage={"input_tokens": 200, "output_tokens": 100},
        duration_ms=600.0
    )
    
    trace = tracer.get_trace(trace_id)
    usage = trace.token_usage
    
    assert usage["input_tokens"] == 300
    assert usage["output_tokens"] == 150
    assert usage["total_tokens"] == 450


def test_clear():
    """clear 应该清空所有追踪。"""
    tracer = ExecutionTracer()
    
    tracer.start_trace()
    tracer.start_trace()
    
    assert len(tracer.traces) == 2
    
    tracer.clear()
    
    assert len(tracer.traces) == 0


def test_get_tracer_singleton():
    """get_tracer 应该返回单例。"""
    tracer1 = get_tracer()
    tracer2 = get_tracer()
    
    assert tracer1 is tracer2
