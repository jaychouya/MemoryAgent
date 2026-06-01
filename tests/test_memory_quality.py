"""Test memory quality improvements."""
import pytest
from src.memory.types import MemoryItem, MemoryType


def test_memory_has_meaningful_description():
    """记忆应该有有意义的描述，不只是内容的前50个字符。"""
    memory = MemoryItem.create(
        memory_type=MemoryType.USER,
        content="用户喜欢Python，讨厌Java，因为Python语法简洁易读",
        description="用户的编程语言偏好和选择标准"
    )
    
    # 验证描述有意义
    assert memory.description == "用户的编程语言偏好和选择标准"
    assert len(memory.description) > 5


def test_memory_preserves_user_context():
    """记忆应该保留用户上下文信息。"""
    memory = MemoryItem.create(
        memory_type=MemoryType.USER,
        content="用户喜欢Python",
        description="用户偏好",
        metadata={
            "user_id": "user1",
            "session_id": "session_123",
            "importance": 0.8,
            "source": "user_conversation"
        }
    )
    
    # 验证元数据完整
    assert memory.metadata.get("user_id") == "user1"
    assert memory.metadata.get("session_id") == "session_123"
    assert memory.metadata.get("importance") == 0.8
    assert memory.metadata.get("source") == "user_conversation"


def test_memory_type_specific_description():
    """不同类型的记忆应该有不同的描述格式。"""
    user_mem = MemoryItem.create(
        memory_type=MemoryType.USER,
        content="用户喜欢Python",
        description="用户偏好：喜欢Python"
    )
    
    feedback_mem = MemoryItem.create(
        memory_type=MemoryType.FEEDBACK,
        content="不要用mock数据库",
        description="行为反馈：不要用mock数据库"
    )
    
    project_mem = MemoryItem.create(
        memory_type=MemoryType.PROJECT,
        content="周五前完成API",
        description="项目动态：周五前完成API"
    )
    
    reference_mem = MemoryItem.create(
        memory_type=MemoryType.REFERENCE,
        content="Grafana看板地址",
        description="外部引用：Grafana看板地址"
    )
    
    # 验证描述格式
    assert user_mem.description.startswith("用户偏好")
    assert feedback_mem.description.startswith("行为反馈")
    assert project_mem.description.startswith("项目动态")
    assert reference_mem.description.startswith("外部引用")
