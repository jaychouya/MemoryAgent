import pytest
import json
from unittest.mock import AsyncMock
from src.memory.layers.working import WorkingMemory
from src.backend.models.message import Message, MessageRole


class TestWorkingMemory:
    @pytest.fixture
    def working_memory(self, mock_redis):
        """Create working memory instance with mock Redis."""
        return WorkingMemory(redis_client=mock_redis, ttl=3600)
    
    @pytest.mark.asyncio
    async def test_get_empty_context(self, working_memory, mock_redis):
        """Test getting context when no messages exist."""
        mock_redis.get.return_value = None
        
        result = await working_memory.get_context("session123")
        
        assert result == []
        mock_redis.get.assert_called_once_with("working:session123")
    
    @pytest.mark.asyncio
    async def test_add_message(self, working_memory, mock_redis):
        """Test adding a message to working memory."""
        mock_redis.get.return_value = None
        
        message = Message(content="Hello", role=MessageRole.USER)
        await working_memory.add_message("session123", message)
        
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == "working:session123"
        assert call_args[0][1] == 3600  # TTL
        
        # Verify the stored data contains our message
        stored_data = json.loads(call_args[0][2])
        assert len(stored_data) == 1
        assert stored_data[0]["content"] == "Hello"
    
    @pytest.mark.asyncio
    async def test_context_sliding_window(self, working_memory, mock_redis):
        """Test that context maintains sliding window of 20 messages."""
        # Create 25 existing messages
        existing_messages = [
            {"content": f"msg_{i}", "role": "user", "timestamp": "2024-01-01T00:00:00"}
            for i in range(25)
        ]
        mock_redis.get.return_value = json.dumps(existing_messages)
        
        message = Message(content="new message", role=MessageRole.USER)
        await working_memory.add_message("session123", message)
        
        # Verify only 20 messages are kept
        call_args = mock_redis.setex.call_args
        stored_data = json.loads(call_args[0][2])
        assert len(stored_data) == 20
        assert stored_data[-1]["content"] == "new message"
    
    @pytest.mark.asyncio
    async def test_clear_context(self, working_memory, mock_redis):
        """Test clearing working memory for a session."""
        await working_memory.clear("session123")
        mock_redis.delete.assert_called_once_with("working:session123")
    
    @pytest.mark.asyncio
    async def test_get_message_count(self, working_memory, mock_redis):
        """Test getting message count in working memory."""
        messages = [
            {"content": "msg1", "role": "user"},
            {"content": "msg2", "role": "assistant"}
        ]
        mock_redis.get.return_value = json.dumps(messages)
        
        count = await working_memory.count("session123")
        assert count == 2
