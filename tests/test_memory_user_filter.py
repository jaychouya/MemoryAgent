"""Test memory retrieval with user_id filtering."""
import pytest
from src.memory.types import MemoryItem, MemoryType
from src.memory.storage import MemoryStorage


@pytest.mark.asyncio
async def test_retrieve_filters_by_user_id():
    """记忆检索应该按 user_id 过滤。"""
    storage = MemoryStorage()
    
    # 创建两个不同用户的记忆，使用 user_id_ 前缀
    mem1 = MemoryItem.create(
        memory_type=MemoryType.USER,
        content="用户A喜欢Python",
        description="用户A的偏好",
        metadata={"user_id": "user_a"},
    )
    mem1.id = "user_a_mem1"

    mem2 = MemoryItem.create(
        memory_type=MemoryType.USER,
        content="用户B喜欢Java",
        description="用户B的偏好",
        metadata={"user_id": "user_b"},
    )
    mem2.id = "user_b_mem1"
    
    # 存储记忆
    await storage.store(mem1)
    await storage.store(mem2)
    
    # 搜索 user_a 的记忆（文件名以 user_a 开头）
    results_a = await storage.search(user_id="user_a")
    assert len(results_a) >= 1
    # 验证只返回 user_a 的记忆
    for mem in results_a:
        assert mem.metadata.get("user_id") == "user_a"
    
    # 搜索 user_b 的记忆（文件名以 user_b 开头）
    results_b = await storage.search(user_id="user_b")
    assert len(results_b) >= 1
    # 验证只返回 user_b 的记忆
    for mem in results_b:
        assert mem.metadata.get("user_id") == "user_b"


@pytest.mark.asyncio
async def test_retrieve_returns_all_without_user_id():
    """不指定 user_id 时应该返回所有记忆。"""
    storage = MemoryStorage()
    
    # 搜索所有记忆
    results = await storage.search()
    assert len(results) >= 2
