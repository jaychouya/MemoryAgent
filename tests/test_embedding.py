import pytest
from unittest.mock import AsyncMock, MagicMock
from src.utils.embedding import EmbeddingService


class TestEmbeddingService:
    @pytest.fixture
    def mock_openai_client(self):
        """Mock OpenAI client."""
        mock = AsyncMock()
        mock.embeddings.create = AsyncMock(
            return_value=MagicMock(
                data=[MagicMock(embedding=[0.1] * 1536)]
            )
        )
        return mock
    
    @pytest.mark.asyncio
    async def test_embed_single_text(self, mock_openai_client):
        """Test embedding a single text."""
        service = EmbeddingService(client=mock_openai_client)
        
        result = await service.embed("Hello world")
        
        assert len(result) == 1536
        assert all(isinstance(x, float) for x in result)
        mock_openai_client.embeddings.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_embed_batch(self, mock_openai_client):
        """Test embedding multiple texts."""
        # Mock batch response
        mock_openai_client.embeddings.create.return_value = MagicMock(
            data=[
                MagicMock(embedding=[0.1] * 1536),
                MagicMock(embedding=[0.2] * 1536)
            ]
        )
        
        service = EmbeddingService(client=mock_openai_client)
        
        results = await service.embed_batch(["Hello", "World"])
        
        assert len(results) == 2
        assert len(results[0]) == 1536
        assert len(results[1]) == 1536
    
    @pytest.mark.asyncio
    async def test_embed_empty_text_raises_error(self, mock_openai_client):
        """Test that embedding empty text raises error."""
        service = EmbeddingService(client=mock_openai_client)
        
        with pytest.raises(ValueError, match="Text cannot be empty"):
            await service.embed("")
    
    def test_cosine_similarity(self):
        """Test cosine similarity calculation."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        vec3 = [0.0, 1.0, 0.0]
        
        # Same vectors should have similarity 1.0
        assert EmbeddingService.cosine_similarity(vec1, vec2) == 1.0
        
        # Orthogonal vectors should have similarity 0.0
        assert EmbeddingService.cosine_similarity(vec1, vec3) == 0.0
