"""Test retrieval upgrade with SQLite index."""
import pytest
import tempfile
import asyncio
from pathlib import Path
from src.memory.storage import MemoryStorage
from src.memory.retrieval import MemoryRetrieval
from src.memory.types import MemoryItem, MemoryType


def test_retrieval_uses_index():
    """检索应该使用 SQLite 索引。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = MemoryStorage(tmpdir)
        retrieval = MemoryRetrieval(storage)
        
        # 存储记忆
        memory = MemoryItem.create(
            memory_type=MemoryType.USER,
            content="用户喜欢Python",
            description="用户偏好"
        )
        
        asyncio.run(storage.store(memory))
        
        # 检索
        results = asyncio.run(retrieval.retrieve("Python"))
        
        assert len(results) > 0
        assert any("Python" in r.get("content", "") for r in results)


def test_retrieval_filters_by_user():
    """检索应该按用户过滤。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = MemoryStorage(tmpdir)
        retrieval = MemoryRetrieval(storage)
        
        # 存储两个用户的记忆
        mem1 = MemoryItem.create(
            memory_type=MemoryType.USER,
            content="用户A喜欢Python",
            description="用户A偏好",
            metadata={"user_id": "user_a"}
        )
        mem2 = MemoryItem.create(
            memory_type=MemoryType.USER,
            content="用户B喜欢Java",
            description="用户B偏好",
            metadata={"user_id": "user_b"}
        )
        
        asyncio.run(storage.store(mem1))
        asyncio.run(storage.store(mem2))
        
        # 检索 user_a 的记忆
        results = asyncio.run(retrieval.retrieve("喜欢", user_id="user_a"))
        
        # 应该只返回 user_a 的记忆
        for result in results:
            assert "用户A" in result.get("content", "")


def test_retrieval_returns_staleness_info():
    """检索应该返回过时信息。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = MemoryStorage(tmpdir)
        retrieval = MemoryRetrieval(storage)
        
        # 存储记忆
        memory = MemoryItem.create(
            memory_type=MemoryType.USER,
            content="用户喜欢Python",
            description="用户偏好"
        )
        
        asyncio.run(storage.store(memory))
        
        # 检索
        results = asyncio.run(retrieval.retrieve("Python"))
        
        assert len(results) > 0
        assert "age_days" in results[0]
        assert "is_stale" in results[0]
