import pytest
import asyncio
from typing import Generator
from unittest.mock import AsyncMock


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_redis() -> AsyncMock:
    """Mock Redis client."""
    mock = AsyncMock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.setex = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def mock_embedding_service() -> AsyncMock:
    """Mock embedding service."""
    mock = AsyncMock()
    mock.embed = AsyncMock(return_value=[0.1] * 1536)
    mock.embed_batch = AsyncMock(return_value=[[0.1] * 1536])
    return mock
