"""Test memory index."""
import pytest
import tempfile
import os
from src.memory.index import MemoryIndex


def test_index_stores_and_retrieves():
    """索引应该能存储和检索记忆。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        index = MemoryIndex(os.path.join(tmpdir, "test.db"))
        
        # 存储记忆
        index.add(
            memory_id="test_1",
            content="用户喜欢Python",
            memory_type="user",
            user_id="user1",
            importance=0.8
        )
        
        # 检索记忆
        results = index.search("Python", user_id="user1")
        
        assert len(results) == 1
        assert results[0]["memory_id"] == "test_1"


def test_index_filters_by_user():
    """索引应该按用户过滤。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        index = MemoryIndex(os.path.join(tmpdir, "test.db"))
        
        # 存储两个用户的记忆
        index.add("test_1", "用户A喜欢Python", "user", "user_a", 0.8)
        index.add("test_2", "用户B喜欢Java", "user", "user_b", 0.8)
        
        # 搜索 user_a 的记忆
        results = index.search("喜欢", user_id="user_a")
        
        assert len(results) == 1
        assert results[0]["memory_id"] == "test_1"


def test_index_full_text_search():
    """索引应该支持全文搜索。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        index = MemoryIndex(os.path.join(tmpdir, "test.db"))
        
        # 存储记忆
        index.add("test_1", "用户喜欢Python编程语言", "user", "user1", 0.8)
        index.add("test_2", "用户讨厌Java", "user", "user1", 0.8)
        
        # 全文搜索（使用单个关键词）
        results = index.search("Python")
        
        assert len(results) >= 1
        assert any("Python" in r["content"] for r in results)
