"""Test memory storage saves complete content."""
import pytest
from src.memory.types import MemoryItem, MemoryType


def test_memory_saves_complete_content():
    """记忆应该保存完整内容，不只是描述。"""
    # 创建一个记忆
    memory = MemoryItem.create(
        memory_type=MemoryType.USER,
        content="用户喜欢Python，讨厌Java，因为Python语法简洁",
        description="用户编程语言偏好"
    )
    
    # 转换为 markdown
    md = memory.to_markdown()
    
    # 从 markdown 解析回来
    parsed = MemoryItem.from_markdown(md)
    
    # 验证：content 应该是完整内容，不是 description
    assert parsed.content == "用户喜欢Python，讨厌Java，因为Python语法简洁"
    assert parsed.description == "用户编程语言偏好"


def test_memory_preserves_metadata():
    """记忆应该保留元数据。"""
    memory = MemoryItem.create(
        memory_type=MemoryType.USER,
        content="测试内容",
        description="测试描述",
        metadata={"user_id": "user1", "importance": 0.8}
    )
    
    md = memory.to_markdown()
    parsed = MemoryItem.from_markdown(md)
    
    assert parsed.metadata.get("user_id") == "user1"
    assert parsed.metadata.get("importance") == 0.8
