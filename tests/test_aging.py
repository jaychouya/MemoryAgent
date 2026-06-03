"""Tests for memory aging system."""
import pytest
from datetime import datetime, timedelta
from src.memory.aging import MemoryAging


@pytest.fixture
def aging():
    """Create a memory aging instance."""
    return MemoryAging()


def test_aging_creates():
    """MemoryAging 应该能创建。"""
    aging = MemoryAging()
    assert aging is not None


def test_aging_has_stale_threshold(aging):
    """应该有老化阈值。"""
    assert aging.STALE_THRESHOLD_DAYS == 2


def test_calculate_age(aging):
    """calculate_age 应该计算年龄。"""
    memory = {"created_at": datetime.now().isoformat()}
    
    age = aging.calculate_age(memory)
    
    assert age == 0


def test_calculate_age_old(aging):
    """calculate_age 应该计算旧记忆年龄。"""
    memory = {"created_at": (datetime.now() - timedelta(days=5)).isoformat()}
    
    age = aging.calculate_age(memory)
    
    assert age == 5


def test_calculate_age_none(aging):
    """calculate_age 应该处理无时间戳。"""
    memory = {}
    
    age = aging.calculate_age(memory)
    
    assert age is None


def test_is_stale(aging):
    """is_stale 应该检查是否过期。"""
    # 新记忆
    new_memory = {"created_at": datetime.now().isoformat()}
    assert aging.is_stale(new_memory) is False
    
    # 旧记忆
    old_memory = {"created_at": (datetime.now() - timedelta(days=5)).isoformat()}
    assert aging.is_stale(old_memory) is True


def test_get_stale_warning(aging):
    """get_stale_warning 应该返回老化警告。"""
    # 新记忆
    new_memory = {"created_at": datetime.now().isoformat()}
    assert aging.get_stale_warning(new_memory) is None
    
    # 旧记忆
    old_memory = {"created_at": (datetime.now() - timedelta(days=5)).isoformat()}
    warning = aging.get_stale_warning(old_memory)
    
    assert warning is not None
    assert "5 天" in warning


def test_wrap_with_system_reminder(aging):
    """wrap_with_system_reminder 应该包装内容。"""
    memory = {"created_at": datetime.now().isoformat()}
    content = "用户喜欢 Python"
    
    wrapped = aging.wrap_with_system_reminder(memory, content)
    
    assert "<system-reminder>" in wrapped
    assert "</system-reminder>" in wrapped
    assert "用户喜欢 Python" in wrapped


def test_wrap_with_stale_warning(aging):
    """wrap_with_system_reminder 应该添加老化警告。"""
    memory = {"created_at": (datetime.now() - timedelta(days=5)).isoformat()}
    content = "用户喜欢 Python"
    
    wrapped = aging.wrap_with_system_reminder(memory, content)
    
    assert "5 days ago" in wrapped
    assert "Verify" in wrapped


def test_get_verification_prompt(aging):
    """get_verification_prompt 应该返回验证提示。"""
    prompt = aging.get_verification_prompt()
    
    assert "验证" in prompt
    assert "文件路径" in prompt
    assert "grep" in prompt


def test_inject_memories(aging):
    """inject_memories 应该注入记忆。"""
    memories = [
        {
            "content": "用户喜欢 Python",
            "description": "用户偏好",
            "type": "user",
            "created_at": datetime.now().isoformat()
        }
    ]
    
    result = aging.inject_memories(memories)
    
    assert "相关记忆" in result
    assert "用户喜欢 Python" in result


def test_inject_memories_with_stale(aging):
    """inject_memories 应该添加老化警告。"""
    memories = [
        {
            "content": "用户喜欢 Python",
            "description": "用户偏好",
            "type": "user",
            "created_at": (datetime.now() - timedelta(days=5)).isoformat()
        }
    ]
    
    result = aging.inject_memories(memories)
    
    # 老化警告在 system-reminder 中
    assert "5 days ago" in result
    assert "Verify" in result
    # 验证提示也会出现
    assert "验证" in result


def test_get_stats(aging):
    """get_stats 应该返回统计信息。"""
    memories = [
        {"created_at": datetime.now().isoformat()},
        {"created_at": (datetime.now() - timedelta(days=5)).isoformat()},
    ]
    
    stats = aging.get_stats(memories)
    
    assert stats["total_memories"] == 2
    assert stats["stale_memories"] == 1
    assert stats["stale_percentage"] == 50.0
