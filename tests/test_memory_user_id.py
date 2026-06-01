"""Test memory store receives correct user_id."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.agent.tools.builtin import MemoryStoreTool


@pytest.mark.asyncio
async def test_memory_store_receives_user_id():
    """memory_store 工具应该接收到正确的 user_id。"""
    # 创建 mock memory manager
    mock_memory = AsyncMock()
    mock_memory.store = AsyncMock(return_value=True)
    
    # 创建工具
    tool = MemoryStoreTool(mock_memory)
    
    # 执行工具，传入 user_id
    result = await tool.execute(
        content="用户喜欢Python",
        memory_type="user",
        user_id="user123",
        session_id="session456"
    )
    
    # 验证 memory.store 被调用时包含了正确的 user_id
    mock_memory.store.assert_called_once()
    call_kwargs = mock_memory.store.call_args[1]
    assert call_kwargs.get("user_id") == "user123"
