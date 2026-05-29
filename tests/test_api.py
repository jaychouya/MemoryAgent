import pytest
from httpx import AsyncClient, ASGITransport
from src.backend.main import app


class TestChatAPI:
    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health check endpoint."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_chat_endpoint(self):
        """Test chat endpoint with message."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/chat",
                json={
                    "message": "Hello, I like coffee",
                    "session_id": "test-session"
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "memory_updates" in data
    
    @pytest.mark.asyncio
    async def test_chat_validation_error(self):
        """Test chat endpoint validation."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/chat",
                json={"message": ""}  # Empty message
            )
        
        assert response.status_code == 422


class TestMemoryAPI:
    @pytest.mark.asyncio
    async def test_list_memories(self):
        """Test listing memories."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/memories",
                params={"user_id": "test-user"}
            )
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)
