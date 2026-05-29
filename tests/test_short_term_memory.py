import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from src.memory.layers.short_term import ShortTermMemory
from src.backend.models.memory import ShortTermMemoryItem


class TestShortTermMemory:
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        session = AsyncMock()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.execute = AsyncMock()
        return session
    
    @pytest.fixture
    def short_term_memory(self, mock_db_session, mock_embedding_service):
        """Create short-term memory instance."""
        return ShortTermMemory(
            db_session=mock_db_session,
            embedding_service=mock_embedding_service
        )
    
    @pytest.mark.asyncio
    async def test_store_memory(self, short_term_memory, mock_db_session, mock_embedding_service):
        """Test storing a memory in short-term storage."""
        item = ShortTermMemoryItem(
            user_id="user1",
            content="User likes coffee",
            importance_score=0.8
        )
        
        await short_term_memory.store(item)
        
        mock_embedding_service.embed.assert_called_once_with("User likes coffee")
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_memory(self, short_term_memory, mock_db_session):
        """Test deleting a memory."""
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_db_session.execute.return_value = mock_result
        
        result = await short_term_memory.delete("mem1")
        
        assert result == True
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_returns_empty_when_no_results(self, short_term_memory, mock_db_session):
        """Test search returns empty list when no results found."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value = mock_result
        
        results = await short_term_memory.search("user1", "test query")
        
        assert results == []
