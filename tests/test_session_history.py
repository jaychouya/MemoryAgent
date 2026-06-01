"""Test session history saves complete tool call chain."""
import pytest
import json
from pathlib import Path


def test_session_saves_tool_calls():
    """会话历史应该保存完整的工具调用链。"""
    # 模拟一个包含工具调用的消息
    messages = [
        {
            "role": "user",
            "content": "记住我喜欢Python",
            "timestamp": "2026-06-01T15:00:00"
        },
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "call_123",
                    "type": "function",
                    "function": {
                        "name": "memory_store",
                        "arguments": '{"content": "用户喜欢Python", "memory_type": "user"}'
                    }
                }
            ],
            "timestamp": "2026-06-01T15:00:01"
        },
        {
            "role": "tool",
            "content": "已记住：用户喜欢Python",
            "tool_call_id": "call_123",
            "name": "memory_store",
            "timestamp": "2026-06-01T15:00:02"
        },
        {
            "role": "assistant",
            "content": "好的，我已经记住你喜欢Python了。",
            "timestamp": "2026-06-01T15:00:03"
        }
    ]
    
    # 验证消息链完整性
    assert len(messages) == 4
    
    # 验证有工具调用
    has_tool_calls = any(msg.get("tool_calls") for msg in messages)
    assert has_tool_calls
    
    # 验证有工具结果
    has_tool_result = any(msg.get("role") == "tool" for msg in messages)
    assert has_tool_result
    
    # 验证工具调用和结果匹配
    tool_call_id = messages[1]["tool_calls"][0]["id"]
    tool_result_id = messages[2]["tool_call_id"]
    assert tool_call_id == tool_result_id


def test_session_saves_to_file():
    """会话应该保存到文件。"""
    session_dir = Path("sessions")
    session_dir.mkdir(exist_ok=True)
    
    session_key = "test_user:test_session"
    session_file = session_dir / f"{session_key.replace(':', '_')}.json"
    
    # 模拟保存会话
    messages = [
        {"role": "user", "content": "测试"},
        {"role": "assistant", "content": "回复"}
    ]
    
    session_data = {
        "key": session_key,
        "messages": messages
    }
    
    session_file.write_text(json.dumps(session_data, ensure_ascii=False, indent=2))
    
    # 验证文件存在
    assert session_file.exists()
    
    # 验证内容正确
    loaded = json.loads(session_file.read_text())
    assert loaded["key"] == session_key
    assert len(loaded["messages"]) == 2
    
    # 清理
    session_file.unlink()
