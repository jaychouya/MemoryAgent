import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.memory.manager import MemoryManager
from src.memory.types import MemoryType


class TestMemoryManager:
    @pytest.fixture
    def memory_manager(self, tmp_path):
        """Create memory manager with temp storage."""
        return MemoryManager(
            storage_dir=str(tmp_path / "memories"),
            llm_service=None
        )
    
    @pytest.mark.asyncio
    async def test_store_user_preference(self, memory_manager):
        """Test storing a user preference."""
        result = await memory_manager.store(
            content="I like coffee",
            memory_type=MemoryType.USER,
            description="User preference",
            user_id="user1"
        )
        
        assert result is not None
        assert result.content == "I like coffee"
        assert result.type == MemoryType.USER
    
    @pytest.mark.asyncio
    async def test_store_feedback(self, memory_manager):
        """Test storing behavioral feedback."""
        result = await memory_manager.store_feedback(
            rule="Always use type hints",
            reason="Improves code readability",
            user_id="user1"
        )
        
        assert result is not None
        assert "type hints" in result.content
    
    @pytest.mark.asyncio
    async def test_retrieve_returns_list(self, memory_manager):
        """Test that retrieval returns a list."""
        await memory_manager.store(
            content="Test memory",
            memory_type=MemoryType.USER,
            user_id="user1"
        )
        
        results = await memory_manager.retrieve(
            query="test",
            user_id="user1"
        )
        
        assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_get_stats(self, memory_manager):
        """Test getting memory statistics."""
        stats = await memory_manager.get_stats()
        
        assert "total" in stats
        assert isinstance(stats["total"], int)

    @pytest.mark.asyncio
    async def test_store_supersedes_old_memory(self, memory_manager):
        old = await memory_manager.store(
            content="我现在主要使用 Python",
            memory_type=MemoryType.USER,
            user_id="user1",
        )
        new = await memory_manager.store(
            content="我现在主要使用 Rust",
            memory_type=MemoryType.USER,
            user_id="user1",
            metadata={"supersedes": old.id},
        )

        old_after = await memory_manager.storage.retrieve(old.id)
        results = await memory_manager.retrieve("主要使用", user_id="user1")

        assert old_after.metadata["superseded_by"] == new.id
        assert old_after.metadata["valid_until"]
        assert all(r["memory_id"] != old.id for r in results)
        assert any(r["memory_id"] == new.id for r in results)
