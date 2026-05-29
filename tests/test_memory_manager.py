import pytest
from unittest.mock import AsyncMock, MagicMock
from src.memory.manager import MemoryManager
from src.backend.models.memory import (
    ShortTermMemoryItem,
    LongTermMemoryItem,
    EpisodicMemoryItem,
    MemorySearchResult
)
from src.backend.models.message import Message, MessageRole


class TestMemoryManager:
    @pytest.fixture
    def mock_layers(self):
        """Mock all memory layers."""
        return {
            "working": AsyncMock(),
            "short_term": AsyncMock(),
            "long_term": AsyncMock(),
            "episodic": AsyncMock()
        }
    
    @pytest.fixture
    def memory_manager(self, mock_layers):
        """Create memory manager with mocked layers."""
        return MemoryManager(
            working_memory=mock_layers["working"],
            short_term_memory=mock_layers["short_term"],
            long_term_memory=mock_layers["long_term"],
            episodic_memory=mock_layers["episodic"]
        )
    
    @pytest.mark.asyncio
    async def test_process_message_stores_in_working_memory(self, memory_manager, mock_layers):
        """Test that processing a message stores it in working memory."""
        message = Message(content="I like coffee", role=MessageRole.USER)
        
        await memory_manager.process_message("session1", "user1", message)
        
        mock_layers["working"].add_message.assert_called_once_with("session1", message)
    
    @pytest.mark.asyncio
    async def test_process_message_extracts_preference(self, memory_manager, mock_layers):
        """Test that preferences are extracted and stored."""
        message = Message(content="I like coffee", role=MessageRole.USER)
        
        result = await memory_manager.process_message("session1", "user1", message)
        
        assert result["working"] == True
        assert len(result["extracted_memories"]) > 0
    
    @pytest.mark.asyncio
    async def test_retrieve_searches_all_layers(self, memory_manager, mock_layers):
        """Test that retrieval searches across all memory layers."""
        # Mock search results from each layer
        mock_layers["working"].get_context.return_value = [
            {"content": "Recent message"}
        ]
        mock_layers["short_term"].search.return_value = [
            MemorySearchResult(
                memory=ShortTermMemoryItem(
                    user_id="user1",
                    content="Short-term memory"
                ),
                score=0.8
            )
        ]
        mock_layers["long_term"].retrieve.return_value = [
            MemorySearchResult(
                memory=LongTermMemoryItem(
                    user_id="user1",
                    content="Long-term memory"
                ),
                score=0.9
            )
        ]
        mock_layers["episodic"].search.return_value = []
        
        results = await memory_manager.retrieve("user1", "coffee preference")
        
        assert len(results) >= 2  # At least short-term and long-term results
    
    @pytest.mark.asyncio
    async def test_consolidation_moves_to_long_term(self, memory_manager, mock_layers):
        """Test that consolidation moves important memories to long-term."""
        # Mock expired short-term memory with high importance
        mock_memory = ShortTermMemoryItem(
            user_id="user1",
            content="Important preference",
            importance_score=0.9
        )
        mock_layers["short_term"].get_expired.return_value = [mock_memory]
        
        await memory_manager.consolidate("user1")
        
        # Should store in long-term memory
        mock_layers["long_term"].store.assert_called_once()
        
        # Should delete from short-term
        mock_layers["short_term"].delete.assert_called_once()
