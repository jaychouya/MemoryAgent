"""Pytest configuration for the test suite."""
from unittest.mock import AsyncMock

import pytest

pytest_plugins = ("pytest_asyncio",)


@pytest.fixture
def mock_redis() -> AsyncMock:
    mock = AsyncMock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.setex = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def mock_embedding_service() -> AsyncMock:
    mock = AsyncMock()
    mock.embed = AsyncMock(return_value=[0.1] * 1536)
    mock.embed_batch = AsyncMock(return_value=[[0.1] * 1536])
    return mock
