"""Test Dreaming state - hierarchical memory folding."""
import pytest
from src.memory.folder import MemoryFolder


def test_folder_creates():
    """记忆文件夹应该能创建。"""
    folder = MemoryFolder()
    assert folder is not None


def test_folder_adds_memories():
    """记忆文件夹应该能添加记忆。"""
    folder = MemoryFolder()
    
    folder.add_memory({
        "id": "mem1",
        "type": "user",
        "content": "用户喜欢Python",
        "importance": 0.8
    })
    
    assert len(folder.memories) == 1


def test_folder_creates_hierarchy():
    """记忆文件夹应该创建层级结构。"""
    folder = MemoryFolder()
    
    folder.add_memory({"id": "mem1", "type": "user", "content": "用户喜欢Python", "importance": 0.8})
    folder.add_memory({"id": "mem2", "type": "user", "content": "用户讨厌Java", "importance": 0.7})
    folder.add_memory({"id": "mem3", "type": "feedback", "content": "不要用mock", "importance": 0.9})
    
    hierarchy = folder.get_hierarchy()
    
    assert "user" in hierarchy
    assert "feedback" in hierarchy
    assert len(hierarchy["user"]) == 2
    assert len(hierarchy["feedback"]) == 1


def test_folder_folds_old_memories():
    """记忆文件夹应该折叠旧记忆。"""
    folder = MemoryFolder(max_per_group=2)
    
    folder.add_memory({"id": "mem1", "type": "user", "content": "用户喜欢Python", "importance": 0.8})
    folder.add_memory({"id": "mem2", "type": "user", "content": "用户讨厌Java", "importance": 0.7})
    folder.add_memory({"id": "mem3", "type": "user", "content": "用户偏好简洁语法", "importance": 0.6})
    
    folded = folder.fold()
    
    # 应该有折叠后的摘要
    assert "user" in folded
    
    # 应该保留最重要的 + 摘要
    user_memories = folded["user"]
    assert len(user_memories) == 3  # 2个重要 + 1个摘要
    
    # 检查是否有摘要
    summaries = [m for m in user_memories if m.get("is_summary")]
    assert len(summaries) == 1
    assert summaries[0]["summarized_count"] == 1  # 只有1个被摘要


def test_folder_preserves_important_memories():
    """记忆文件夹应该保留重要记忆。"""
    folder = MemoryFolder(max_per_group=2)
    
    folder.add_memory({"id": "mem1", "type": "user", "content": "用户喜欢Python", "importance": 0.9})
    folder.add_memory({"id": "mem2", "type": "user", "content": "用户讨厌Java", "importance": 0.8})
    folder.add_memory({"id": "mem3", "type": "user", "content": "用户偏好简洁语法", "importance": 0.7})
    
    folded = folder.fold()
    
    # 重要记忆应该保留
    user_memories = folded["user"]
    assert any("Python" in m.get("content", "") for m in user_memories)


def test_folder_creates_summary():
    """记忆文件夹应该创建摘要。"""
    folder = MemoryFolder()
    
    folder.add_memory({"id": "mem1", "type": "user", "content": "用户喜欢Python", "importance": 0.8})
    folder.add_memory({"id": "mem2", "type": "user", "content": "用户讨厌Java", "importance": 0.7})
    
    summary = folder.get_summary()
    
    assert summary
    assert len(summary) > 0


def test_folder_get_stats():
    """记忆文件夹应该返回统计信息。"""
    folder = MemoryFolder()
    
    folder.add_memory({"id": "mem1", "type": "user", "content": "用户喜欢Python", "importance": 0.8})
    folder.add_memory({"id": "mem2", "type": "feedback", "content": "不要用mock", "importance": 0.9})
    
    stats = folder.get_stats()
    
    assert stats["total"] == 2
    assert stats["by_type"]["user"] == 1
    assert stats["by_type"]["feedback"] == 1
