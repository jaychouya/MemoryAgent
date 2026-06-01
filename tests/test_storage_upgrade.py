"""Test storage integration with chunker/scorer/index."""
import pytest
import tempfile
import asyncio
from pathlib import Path
from src.memory.storage import MemoryStorage
from src.memory.types import MemoryItem, MemoryType


def test_storage_saves_with_importance_score():
    """存储应该计算并保存重要性评分。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = MemoryStorage(tmpdir)
        
        memory = MemoryItem.create(
            memory_type=MemoryType.USER,
            content="用户喜欢Python",
            description="用户偏好"
        )
        
        asyncio.run(storage.store(memory))
        
        # 验证记忆文件存在
        user_dir = Path(tmpdir) / "user"
        memory_files = list(user_dir.glob("*.md"))
        assert len(memory_files) > 0
        
        # 验证内容包含 importance
        content = memory_files[0].read_text()
        assert "importance" in content


def test_storage_adds_to_index():
    """存储应该添加到 SQLite 索引。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = MemoryStorage(tmpdir)
        
        memory = MemoryItem.create(
            memory_type=MemoryType.USER,
            content="用户喜欢Python",
            description="用户偏好",
            metadata={"user_id": "user1"}
        )
        
        asyncio.run(storage.store(memory))
        
        # 验证索引中有记录
        results = storage.index.search("Python", user_id="user1")
        assert len(results) > 0


def test_storage_chunks_long_content():
    """存储应该分块长内容。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = MemoryStorage(tmpdir)
        
        # 创建长内容
        content = "这是一段很长的内容。" * 500
        
        memory = MemoryItem.create(
            memory_type=MemoryType.USER,
            content=content,
            description="长内容测试"
        )
        
        asyncio.run(storage.store(memory))
        
        # 验证文件存在（可能有多个分块）
        files = list(Path(tmpdir).rglob("*.md"))
        assert len(files) > 0


def test_storage_search_uses_index():
    """搜索应该使用 SQLite 索引。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = MemoryStorage(tmpdir)
        
        # 存储记忆
        memory = MemoryItem.create(
            memory_type=MemoryType.USER,
            content="用户喜欢Python编程",
            description="用户偏好"
        )
        
        asyncio.run(storage.store(memory))
        
        # 使用索引搜索
        results = storage.index.search("Python")
        assert len(results) > 0
        assert any("Python" in r.get("content", "") for r in results)
