# MemoMind Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a personal AI assistant with cognitive memory architecture (working/short-term/long-term/episodic memory) that gets smarter over time.

**Architecture:** Four-layer memory system inspired by human cognition, with autonomous decision engine and explainability module. Python backend with FastAPI, Next.js frontend, Redis + PostgreSQL + Chroma for storage.

**Tech Stack:** Python 3.11, FastAPI, LangChain, Redis, PostgreSQL + pgvector, Chroma, Next.js 14, TypeScript, Tailwind CSS

---

## Phase 1: Project Setup & Foundation

### Task 1.1: Initialize Project Structure

**Files:**
- Create: `requirements.txt`
- Create: `pyproject.toml`
- Create: `src/utils/__init__.py`
- Create: `src/memory/__init__.py`
- Create: `src/agent/__init__.py`
- Create: `src/backend/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Create requirements.txt**

```txt
# Core
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0

# LangChain
langchain==0.1.4
langchain-openai==0.0.5
langgraph==0.0.20

# Database
redis==5.0.1
asyncpg==0.29.0
sqlalchemy[asyncio]==2.0.25
pgvector==0.2.4
chromadb==0.4.22

# Embedding
openai==1.12.0
tiktoken==0.5.2

# Utilities
python-dotenv==1.0.0
networkx==3.2.1
numpy==1.26.3

# Testing
pytest==7.4.4
pytest-asyncio==0.23.3
pytest-mock==3.12.0
httpx==0.26.0
```

- [ ] **Step 2: Create pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "memomind"
version = "0.1.0"
description = "Personal AI Assistant with Cognitive Memory Architecture"
requires-python = ">=3.11"

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.ruff]
line-length = 100
target-version = "py311"
select = ["E", "F", "I", "N", "W", "UP"]
```

- [ ] **Step 3: Create package __init__.py files**

```python
# src/utils/__init__.py
"""Utility functions and helpers."""

# src/memory/__init__.py
"""Memory system implementation."""

# src/agent/__init__.py
"""Agent core and decision engine."""

# src/backend/__init__.py
"""FastAPI backend application."""

# tests/__init__.py
"""Test suite for MemoMind."""
```

- [ ] **Step 4: Create test configuration**

```python
# tests/conftest.py
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

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
```

- [ ] **Step 5: Initialize git and commit**

```bash
git init
git add .
git commit -m "chore: initialize project structure with dependencies"
```

---

### Task 1.2: Configuration Management

**Files:**
- Create: `src/utils/config.py`
- Create: `.env.example`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write failing test for config**

```python
# tests/test_config.py
import pytest
from src.utils.config import Settings

def test_settings_default_values():
    """Test that settings have correct default values."""
    settings = Settings()
    assert settings.APP_NAME == "MemoMind"
    assert settings.DEBUG == False
    assert settings.REDIS_URL == "redis://localhost:6379"
    assert settings.WORKING_MEMORY_TTL == 3600
    assert settings.SHORT_TERM_MEMORY_DAYS == 30
    assert settings.MAX_CONTEXT_MESSAGES == 20

def test_settings_from_env(monkeypatch):
    """Test that settings can be loaded from environment."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")
    monkeypatch.setenv("DEBUG", "true")
    
    settings = Settings()
    assert settings.OPENAI_API_KEY == "test-key-123"
    assert settings.DEBUG == True
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_config.py -v
```
Expected: FAIL with "ModuleNotFoundError: No module named 'src.utils.config'"

- [ ] **Step 3: Implement Settings class**

```python
# src/utils/config.py
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # App
    APP_NAME: str = "MemoMind"
    DEBUG: bool = False
    
    # API Keys
    OPENAI_API_KEY: Optional[str] = None
    ZHIPU_API_KEY: Optional[str] = None
    
    # Redis (Working Memory)
    REDIS_URL: str = "redis://localhost:6379"
    WORKING_MEMORY_TTL: int = 3600  # 1 hour
    
    # PostgreSQL (Short-term + Episodic Memory)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/memomind"
    
    # Chroma (Long-term Memory)
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8000
    CHROMA_COLLECTION: str = "long_term_memory"
    
    # Memory Settings
    SHORT_TERM_MEMORY_DAYS: int = 30
    MAX_CONTEXT_MESSAGES: int = 20
    MEMORY_CONSOLIDATION_INTERVAL: int = 3600  # 1 hour
    
    # LLM Settings
    LLM_MODEL: str = "gpt-4"
    LLM_TEMPERATURE: float = 0.7
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSIONS: int = 1536
    
    # Decision Engine Settings
    AUTONOMOUS_ACTIONS: list = [
        "memory_search",
        "context_retrieval",
        "response_generation",
        "memory_consolidation"
    ]
    CONFIRM_REQUIRED_ACTIONS: list = [
        "memory_delete",
        "preference_update",
        "external_api_call"
    ]
    FORBIDDEN_ACTIONS: list = [
        "financial_transaction",
        "personal_data_export"
    ]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()
```

- [ ] **Step 4: Create .env.example**

```env
# MemoMind Configuration

# API Keys (required)
OPENAI_API_KEY=sk-your-openai-key-here

# Redis
REDIS_URL=redis://localhost:6379

# PostgreSQL
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/memomind

# Chroma
CHROMA_HOST=localhost
CHROMA_PORT=8000

# Debug
DEBUG=false
```

- [ ] **Step 5: Run test to verify it passes**

```bash
pytest tests/test_config.py -v
```
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/utils/config.py tests/test_config.py .env.example
git commit -m "feat: add configuration management with pydantic-settings"
```

---

### Task 1.3: Data Models - Memory Types

**Files:**
- Create: `src/backend/models/message.py`
- Create: `src/backend/models/memory.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Write failing tests for message model**

```python
# tests/test_models.py
import pytest
from datetime import datetime
from src.backend.models.message import Message, MessageRole
from src.backend.models.memory import (
    WorkingMemoryItem,
    ShortTermMemoryItem,
    LongTermMemoryItem,
    EpisodicMemoryItem,
    MemoryLayer
)

class TestMessageModel:
    def test_create_user_message(self):
        """Test creating a user message."""
        msg = Message(
            content="Hello, I like coffee",
            role=MessageRole.USER
        )
        assert msg.content == "Hello, I like coffee"
        assert msg.role == MessageRole.USER
        assert isinstance(msg.timestamp, datetime)
        assert msg.message_id is not None
    
    def test_create_assistant_message(self):
        """Test creating an assistant message."""
        msg = Message(
            content="I'll remember that!",
            role=MessageRole.ASSISTANT
        )
        assert msg.role == MessageRole.ASSISTANT
    
    def test_message_to_dict(self):
        """Test message serialization."""
        msg = Message(content="test", role=MessageRole.USER)
        d = msg.to_dict()
        assert "content" in d
        assert "role" in d
        assert "timestamp" in d
        assert d["role"] == "user"

class TestMemoryModels:
    def test_working_memory_item(self):
        """Test working memory item creation."""
        item = WorkingMemoryItem(
            session_id="abc123",
            content="Current context",
            ttl=3600
        )
        assert item.session_id == "abc123"
        assert item.layer == MemoryLayer.WORKING
    
    def test_short_term_memory_item(self):
        """Test short-term memory item creation."""
        item = ShortTermMemoryItem(
            user_id="user1",
            content="User likes coffee",
            importance_score=0.8
        )
        assert item.layer == MemoryLayer.SHORT_TERM
        assert item.importance_score == 0.8
    
    def test_long_term_memory_item(self):
        """Test long-term memory item creation."""
        item = LongTermMemoryItem(
            user_id="user1",
            content="Prefers dark roast coffee",
            category="food_preference",
            confidence=0.95
        )
        assert item.layer == MemoryLayer.LONG_TERM
        assert item.category == "food_preference"
    
    def test_episodic_memory_item(self):
        """Test episodic memory item creation."""
        item = EpisodicMemoryItem(
            user_id="user1",
            description="First time trying espresso",
            emotion="excited",
            importance=0.9
        )
        assert item.layer == MemoryLayer.EPISODIC
        assert item.emotion == "excited"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_models.py -v
```
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Implement Message model**

```python
# src/backend/models/message.py
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class MessageRole(str, Enum):
    """Message role enumeration."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    """Chat message model."""
    
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str
    role: MessageRole
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: dict = Field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Serialize message to dictionary."""
        return {
            "message_id": self.message_id,
            "content": self.content,
            "role": self.role.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }
    
    class Config:
        use_enum_values = True
```

- [ ] **Step 4: Implement Memory models**

```python
# src/backend/models/memory.py
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from typing import Optional, List
import uuid


class MemoryLayer(str, Enum):
    """Memory layer enumeration."""
    WORKING = "working"
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    EPISODIC = "episodic"


class MemoryBase(BaseModel):
    """Base memory model with common fields."""
    
    memory_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    content: str
    layer: MemoryLayer
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: dict = Field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Serialize memory to dictionary."""
        return {
            "memory_id": self.memory_id,
            "user_id": self.user_id,
            "content": self.content,
            "layer": self.layer.value,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata
        }


class WorkingMemoryItem(MemoryBase):
    """Working memory item - current session context."""
    
    session_id: str
    layer: MemoryLayer = MemoryLayer.WORKING
    ttl: int = 3600  # Time to live in seconds
    

class ShortTermMemoryItem(MemoryBase):
    """Short-term memory item - recent conversations and temporary info."""
    
    layer: MemoryLayer = MemoryLayer.SHORT_TERM
    importance_score: float = Field(default=0.5, ge=0.0, le=1.0)
    expires_at: Optional[datetime] = None
    memory_type: str = "general"  # conversation_summary, todo, temporary_preference


class LongTermMemoryItem(MemoryBase):
    """Long-term memory item - stable preferences and knowledge."""
    
    layer: MemoryLayer = MemoryLayer.LONG_TERM
    category: str = "general"  # food_preference, hobby, habit, knowledge
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    access_count: int = 0
    last_accessed: Optional[datetime] = None


class EpisodicMemoryItem(MemoryBase):
    """Episodic memory item - important events and experiences."""
    
    layer: MemoryLayer = MemoryLayer.EPISODIC
    description: str
    emotion: Optional[str] = None  # happy, sad, excited, neutral, etc.
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    related_episodes: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)


class MemorySearchResult(BaseModel):
    """Memory search result with relevance score."""
    
    memory: MemoryBase
    score: float = Field(ge=0.0, le=1.0)
    retrieval_method: str = "semantic"  # semantic, keyword, graph
    
    def to_dict(self) -> dict:
        return {
            "memory": self.memory.to_dict(),
            "score": self.score,
            "retrieval_method": self.retrieval_method
        }
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_models.py -v
```
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/backend/models/ tests/test_models.py
git commit -m "feat: add message and memory data models"
```

---

## Phase 2: Memory Layers Implementation

### Task 2.1: Working Memory Layer

**Files:**
- Create: `src/memory/layers/__init__.py`
- Create: `src/memory/layers/working.py`
- Create: `tests/test_working_memory.py`

- [ ] **Step 1: Write failing tests for working memory**

```python
# tests/test_working_memory.py
import pytest
import json
from unittest.mock import AsyncMock, patch
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_working_memory.py -v
```
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Implement WorkingMemory class**

```python
# src/memory/layers/__init__.py
"""Memory layer implementations."""

# src/memory/layers/working.py
import json
import logging
from typing import List, Optional
from datetime import datetime

from src.backend.models.message import Message

logger = logging.getLogger(__name__)


class WorkingMemory:
    """
    Working Memory Layer - Current session context.
    
    Human analogy: What you're thinking about right now.
    
    Implementation:
    - Redis for high-speed read/write
    - Automatic expiration with TTL
    - Sliding window to limit context size
    """
    
    def __init__(self, redis_client, ttl: int = 3600, max_messages: int = 20):
        """
        Initialize working memory.
        
        Args:
            redis_client: AsyncRedis client instance
            ttl: Time to live in seconds (default: 1 hour)
            max_messages: Maximum messages to keep in context
        """
        self.redis = redis_client
        self.ttl = ttl
        self.max_messages = max_messages
    
    def _key(self, session_id: str) -> str:
        """Generate Redis key for session."""
        return f"working:{session_id}"
    
    async def get_context(self, session_id: str) -> List[dict]:
        """
        Get current session context.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of message dictionaries
        """
        key = self._key(session_id)
        data = await self.redis.get(key)
        
        if not data:
            return []
        
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse working memory for session {session_id}")
            return []
    
    async def add_message(self, session_id: str, message: Message) -> None:
        """
        Add message to working memory.
        
        Args:
            session_id: Session identifier
            message: Message to add
        """
        key = self._key(session_id)
        
        # Get existing context
        context = await self.get_context(session_id)
        
        # Add new message
        context.append(message.to_dict())
        
        # Apply sliding window
        if len(context) > self.max_messages:
            context = context[-self.max_messages:]
        
        # Store back to Redis with TTL
        await self.redis.setex(key, self.ttl, json.dumps(context))
        
        logger.debug(f"Added message to working memory for session {session_id}")
    
    async def clear(self, session_id: str) -> None:
        """
        Clear working memory for a session.
        
        Args:
            session_id: Session identifier
        """
        key = self._key(session_id)
        await self.redis.delete(key)
        logger.debug(f"Cleared working memory for session {session_id}")
    
    async def count(self, session_id: str) -> int:
        """
        Get message count in working memory.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Number of messages in context
        """
        context = await self.get_context(session_id)
        return len(context)
    
    async def get_recent_messages(self, session_id: str, n: int = 5) -> List[dict]:
        """
        Get N most recent messages.
        
        Args:
            session_id: Session identifier
            n: Number of recent messages to return
            
        Returns:
            List of recent message dictionaries
        """
        context = await self.get_context(session_id)
        return context[-n:] if len(context) >= n else context
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_working_memory.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/memory/layers/ tests/test_working_memory.py
git commit -m "feat: implement working memory layer with Redis"
```

---

### Task 2.2: Embedding Service

**Files:**
- Create: `src/utils/embedding.py`
- Create: `tests/test_embedding.py`

- [ ] **Step 1: Write failing tests for embedding service**

```python
# tests/test_embedding.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_embedding.py -v
```
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Implement EmbeddingService**

```python
# src/utils/embedding.py
import logging
from typing import List
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Embedding service for text vectorization.
    
    Uses OpenAI's embedding model to convert text to vectors.
    """
    
    def __init__(
        self,
        client: AsyncOpenAI,
        model: str = "text-embedding-3-small",
        dimensions: int = 1536
    ):
        """
        Initialize embedding service.
        
        Args:
            client: AsyncOpenAI client instance
            model: Embedding model name
            dimensions: Output vector dimensions
        """
        self.client = client
        self.model = model
        self.dimensions = dimensions
    
    async def embed(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding vector
            
        Raises:
            ValueError: If text is empty
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=text.strip(),
                dimensions=self.dimensions
            )
            
            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding for text of length {len(text)}")
            
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        # Filter out empty texts
        valid_texts = [t.strip() for t in texts if t and t.strip()]
        
        if not valid_texts:
            raise ValueError("No valid texts to embed")
        
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=valid_texts,
                dimensions=self.dimensions
            )
            
            embeddings = [item.embedding for item in response.data]
            logger.debug(f"Generated {len(embeddings)} embeddings")
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            raise
    
    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Similarity score between -1 and 1
        """
        import numpy as np
        
        a = np.array(vec1)
        b = np.array(vec2)
        
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return float(dot_product / (norm_a * norm_b))
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_embedding.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/utils/embedding.py tests/test_embedding.py
git commit -m "feat: implement embedding service for text vectorization"
```

---

### Task 2.3: Short-term Memory Layer

**Files:**
- Create: `src/memory/layers/short_term.py`
- Create: `tests/test_short_term_memory.py`

- [ ] **Step 1: Write failing tests for short-term memory**

```python
# tests/test_short_term_memory.py
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
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
    async def test_search_returns_relevant_memories(self, short_term_memory, mock_db_session):
        """Test searching returns relevant memories."""
        # Mock database response
        mock_memory = MagicMock()
        mock_memory.id = "mem1"
        mock_memory.content = "User likes coffee"
        mock_memory.importance_score = 0.8
        mock_memory.created_at = datetime.now()
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_memory]
        mock_db_session.execute.return_value = mock_result
        
        results = await short_term_memory.search("user1", "coffee preference")
        
        assert len(results) == 1
        assert results[0].content == "User likes coffee"
    
    @pytest.mark.asyncio
    async def test_get_expired_memories(self, short_term_memory, mock_db_session):
        """Test getting expired memories for cleanup."""
        mock_memory = MagicMock()
        mock_memory.id = "mem1"
        mock_memory.expires_at = datetime.now() - timedelta(days=1)
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_memory]
        mock_db_session.execute.return_value = mock_result
        
        expired = await short_term_memory.get_expired("user1")
        
        assert len(expired) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_short_term_memory.py -v
```
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Implement ShortTermMemory class**

```python
# src/memory/layers/short_term.py
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.models.memory import ShortTermMemoryItem, MemorySearchResult
from src.utils.embedding import EmbeddingService

logger = logging.getLogger(__name__)


class ShortTermMemory:
    """
    Short-term Memory Layer - Recent conversations and temporary info.
    
    Human analogy: What happened yesterday, recent events.
    
    Implementation:
    - PostgreSQL with pgvector for persistent storage
    - Semantic search via vector similarity
    - Automatic expiration based on TTL
    - Importance scoring for retention priority
    """
    
    def __init__(
        self,
        db_session: AsyncSession,
        embedding_service: EmbeddingService,
        default_ttl_days: int = 30
    ):
        """
        Initialize short-term memory.
        
        Args:
            db_session: Async SQLAlchemy session
            embedding_service: Service for generating embeddings
            default_ttl_days: Default time-to-live in days
        """
        self.db = db_session
        self.embedder = embedding_service
        self.default_ttl_days = default_ttl_days
    
    async def store(self, item: ShortTermMemoryItem) -> str:
        """
        Store a memory in short-term storage.
        
        Args:
            item: Memory item to store
            
        Returns:
            Memory ID
        """
        # Generate embedding
        embedding = await self.embedder.embed(item.content)
        
        # Calculate expiration
        expires_at = item.expires_at or datetime.now() + timedelta(days=self.default_ttl_days)
        
        # Create database record
        record = ShortTermMemoryRecord(
            id=item.memory_id,
            user_id=item.user_id,
            content=item.content,
            embedding=embedding,
            memory_type=item.memory_type,
            importance_score=item.importance_score,
            created_at=item.created_at,
            expires_at=expires_at,
            metadata=item.metadata
        )
        
        self.db.add(record)
        await self.db.commit()
        
        logger.info(f"Stored short-term memory {item.memory_id} for user {item.user_id}")
        return item.memory_id
    
    async def search(
        self,
        user_id: str,
        query: str,
        top_k: int = 5,
        min_importance: float = 0.0
    ) -> List[MemorySearchResult]:
        """
        Search short-term memories by semantic similarity.
        
        Args:
            user_id: User identifier
            query: Search query
            top_k: Number of results to return
            min_importance: Minimum importance score filter
            
        Returns:
            List of memory search results
        """
        query_embedding = await self.embedder.embed(query)
        
        # Build query
        stmt = (
            select(ShortTermMemoryRecord)
            .where(ShortTermMemoryRecord.user_id == user_id)
            .where(ShortTermMemoryRecord.expires_at > datetime.now())
            .where(ShortTermMemoryRecord.importance_score >= min_importance)
            .order_by(
                ShortTermMemoryRecord.embedding.cosine_distance(query_embedding)
            )
            .limit(top_k)
        )
        
        result = await self.db.execute(stmt)
        records = result.scalars().all()
        
        # Convert to search results
        results = []
        for record in records:
            memory_item = ShortTermMemoryItem(
                memory_id=record.id,
                user_id=record.user_id,
                content=record.content,
                importance_score=record.importance_score,
                created_at=record.created_at,
                metadata=record.metadata or {}
            )
            
            results.append(MemorySearchResult(
                memory=memory_item,
                score=1.0 - record.embedding.cosine_distance(query_embedding),
                retrieval_method="semantic"
            ))
        
        return results
    
    async def get_expired(self, user_id: str) -> List[ShortTermMemoryItem]:
        """
        Get expired memories for cleanup.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of expired memory items
        """
        stmt = (
            select(ShortTermMemoryRecord)
            .where(ShortTermMemoryRecord.user_id == user_id)
            .where(ShortTermMemoryRecord.expires_at <= datetime.now())
        )
        
        result = await self.db.execute(stmt)
        records = result.scalars().all()
        
        return [
            ShortTermMemoryItem(
                memory_id=r.id,
                user_id=r.user_id,
                content=r.content,
                importance_score=r.importance_score,
                created_at=r.created_at,
                metadata=r.metadata or {}
            )
            for r in records
        ]
    
    async def delete(self, memory_id: str) -> bool:
        """
        Delete a specific memory.
        
        Args:
            memory_id: Memory identifier
            
        Returns:
            True if deleted, False if not found
        """
        stmt = delete(ShortTermMemoryRecord).where(ShortTermMemoryRecord.id == memory_id)
        result = await self.db.execute(stmt)
        await self.db.commit()
        
        return result.rowcount > 0
    
    async def get_by_id(self, memory_id: str) -> Optional[ShortTermMemoryItem]:
        """
        Get a specific memory by ID.
        
        Args:
            memory_id: Memory identifier
            
        Returns:
            Memory item if found, None otherwise
        """
        stmt = select(ShortTermMemoryRecord).where(ShortTermMemoryRecord.id == memory_id)
        result = await self.db.execute(stmt)
        record = result.scalar_one_or_none()
        
        if not record:
            return None
        
        return ShortTermMemoryItem(
            memory_id=record.id,
            user_id=record.user_id,
            content=record.content,
            importance_score=record.importance_score,
            created_at=record.created_at,
            metadata=record.metadata or {}
        )


# SQLAlchemy model (would be in a separate models file in production)
from sqlalchemy import Column, String, Float, DateTime, JSON
from sqlalchemy.orm import declarative_base
from pgvector.sqlalchemy import Vector

Base = declarative_base()


class ShortTermMemoryRecord(Base):
    """SQLAlchemy model for short-term memory."""
    
    __tablename__ = "short_term_memories"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    content = Column(String, nullable=False)
    embedding = Column(Vector(1536))
    memory_type = Column(String, default="general")
    importance_score = Column(Float, default=0.5)
    created_at = Column(DateTime, default=datetime.now)
    expires_at = Column(DateTime, nullable=False)
    metadata = Column(JSON, default={})
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_short_term_memory.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/memory/layers/short_term.py tests/test_short_term_memory.py
git commit -m "feat: implement short-term memory layer with PostgreSQL"
```

---

## Phase 3: Memory Manager & Consolidation

### Task 3.1: Memory Manager

**Files:**
- Create: `src/memory/manager.py`
- Create: `src/memory/retrieval.py`
- Create: `tests/test_memory_manager.py`

- [ ] **Step 1: Write failing tests for memory manager**

```python
# tests/test_memory_manager.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.memory.manager import MemoryManager
from src.backend.models.memory import (
    WorkingMemoryItem,
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_memory_manager.py -v
```
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Implement MemoryManager**

```python
# src/memory/manager.py
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.backend.models.message import Message
from src.backend.models.memory import (
    ShortTermMemoryItem,
    LongTermMemoryItem,
    EpisodicMemoryItem,
    MemorySearchResult,
    MemoryLayer
)
from src.memory.layers.working import WorkingMemory
from src.memory.layers.short_term import ShortTermMemory
from src.memory.layers.long_term import LongTermMemory
from src.memory.layers.episodic import EpisodicMemory
from src.memory.retrieval import MemoryRetriever

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Central memory manager coordinating all memory layers.
    
    Responsibilities:
    - Route memories to appropriate layers
    - Coordinate retrieval across layers
    - Trigger memory consolidation
    - Extract memories from conversations
    """
    
    def __init__(
        self,
        working_memory: WorkingMemory,
        short_term_memory: ShortTermMemory,
        long_term_memory: LongTermMemory,
        episodic_memory: EpisodicMemory
    ):
        """Initialize memory manager with all layers."""
        self.working = working_memory
        self.short_term = short_term_memory
        self.long_term = long_term_memory
        self.episodic = episodic_memory
        self.retriever = MemoryRetriever(
            working=working_memory,
            short_term=short_term_memory,
            long_term=long_term_memory,
            episodic=episodic_memory
        )
    
    async def process_message(
        self,
        session_id: str,
        user_id: str,
        message: Message
    ) -> Dict[str, Any]:
        """
        Process a new message through the memory system.
        
        Args:
            session_id: Current session identifier
            user_id: User identifier
            message: New message to process
            
        Returns:
            Dictionary with memory update information
        """
        updates = {
            "working": False,
            "short_term": False,
            "extracted_memories": []
        }
        
        # 1. Add to working memory
        await self.working.add_message(session_id, message)
        updates["working"] = True
        
        # 2. Extract potential memories from message
        extracted = await self._extract_memories(message)
        
        # 3. Store extracted memories in appropriate layers
        for memory in extracted:
            if memory["type"] == "preference":
                # Store preferences in short-term initially
                item = ShortTermMemoryItem(
                    user_id=user_id,
                    content=memory["content"],
                    importance_score=memory.get("confidence", 0.5),
                    memory_type="preference"
                )
                await self.short_term.store(item)
                updates["short_term"] = True
                updates["extracted_memories"].append(memory)
            
            elif memory["type"] == "event":
                # Store events in episodic memory
                item = EpisodicMemoryItem(
                    user_id=user_id,
                    description=memory["content"],
                    emotion=memory.get("emotion"),
                    importance=memory.get("importance", 0.5)
                )
                await self.episodic.store_episode(item)
                updates["extracted_memories"].append(memory)
        
        return updates
    
    async def retrieve(
        self,
        user_id: str,
        query: str,
        session_id: Optional[str] = None,
        top_k: int = 10
    ) -> List[MemorySearchResult]:
        """
        Retrieve relevant memories across all layers.
        
        Args:
            user_id: User identifier
            query: Search query
            session_id: Current session (for working memory)
            top_k: Maximum results to return
            
        Returns:
            List of memory search results, ranked by relevance
        """
        return await self.retriever.retrieve(
            user_id=user_id,
            query=query,
            session_id=session_id,
            top_k=top_k
        )
    
    async def consolidate(self, user_id: str) -> Dict[str, int]:
        """
        Run memory consolidation - move important short-term memories to long-term.
        
        Args:
            user_id: User identifier
            
        Returns:
            Statistics about consolidation
        """
        stats = {"consolidated": 0, "deleted": 0, "errors": 0}
        
        # Get expired short-term memories
        expired = await self.short_term.get_expired(user_id)
        
        for memory in expired:
            try:
                # Check if memory is important enough to keep
                if memory.importance_score >= 0.7:
                    # Move to long-term memory
                    long_term_item = LongTermMemoryItem(
                        user_id=user_id,
                        content=memory.content,
                        category=self._categorize_content(memory.content),
                        confidence=memory.importance_score
                    )
                    await self.long_term.store(long_term_item)
                    stats["consolidated"] += 1
                
                # Delete from short-term
                await self.short_term.delete(memory.memory_id)
                stats["deleted"] += 1
                
            except Exception as e:
                logger.error(f"Error consolidating memory {memory.memory_id}: {e}")
                stats["errors"] += 1
        
        logger.info(f"Consolidation complete for user {user_id}: {stats}")
        return stats
    
    async def _extract_memories(self, message: Message) -> List[Dict[str, Any]]:
        """
        Extract potential memories from a message.
        
        This is a simplified version - in production, use LLM for extraction.
        """
        memories = []
        content = message.content.lower()
        
        # Simple pattern matching for demo
        preference_patterns = [
            "i like", "i love", "i prefer", "i enjoy",
            "my favorite", "i hate", "i dislike"
        ]
        
        for pattern in preference_patterns:
            if pattern in content:
                memories.append({
                    "type": "preference",
                    "content": message.content,
                    "confidence": 0.7
                })
                break
        
        return memories
    
    def _categorize_content(self, content: str) -> str:
        """Categorize memory content for long-term storage."""
        content_lower = content.lower()
        
        categories = {
            "food": ["food", "eat", "drink", "coffee", "tea", "restaurant"],
            "hobby": ["hobby", "enjoy", "fun", "game", "sport"],
            "work": ["work", "job", "project", "meeting"],
            "health": ["health", "exercise", "gym", "doctor"]
        }
        
        for category, keywords in categories.items():
            if any(kw in content_lower for kw in keywords):
                return category
        
        return "general"


# src/memory/retrieval.py
import logging
from typing import List, Optional
from dataclasses import dataclass

from src.backend.models.memory import MemorySearchResult

logger = logging.getLogger(__name__)


class MemoryRetriever:
    """
    Coordinates memory retrieval across all layers.
    
    Implements a multi-stage retrieval pipeline:
    1. Working memory (most recent context)
    2. Short-term memory (recent relevant memories)
    3. Long-term memory (stable preferences)
    4. Episodic memory (related events)
    """
    
    def __init__(self, working, short_term, long_term, episodic):
        """Initialize with all memory layers."""
        self.working = working
        self.short_term = short_term
        self.long_term = long_term
        self.episodic = episodic
    
    async def retrieve(
        self,
        user_id: str,
        query: str,
        session_id: Optional[str] = None,
        top_k: int = 10
    ) -> List[MemorySearchResult]:
        """
        Retrieve and rank memories from all layers.
        
        Args:
            user_id: User identifier
            query: Search query
            session_id: Session identifier for working memory
            top_k: Maximum results
            
        Returns:
            Ranked list of memory search results
        """
        all_results: List[MemorySearchResult] = []
        
        # 1. Search short-term memory
        try:
            short_term_results = await self.short_term.search(
                user_id=user_id,
                query=query,
                top_k=top_k // 2
            )
            all_results.extend(short_term_results)
        except Exception as e:
            logger.error(f"Error searching short-term memory: {e}")
        
        # 2. Search long-term memory
        try:
            long_term_results = await self.long_term.retrieve(
                user_id=user_id,
                query=query,
                top_k=top_k // 2
            )
            all_results.extend(long_term_results)
        except Exception as e:
            logger.error(f"Error searching long-term memory: {e}")
        
        # 3. Search episodic memory
        try:
            episodic_results = await self.episodic.search(
                user_id=user_id,
                query=query,
                top_k=top_k // 4
            )
            all_results.extend(episodic_results)
        except Exception as e:
            logger.error(f"Error searching episodic memory: {e}")
        
        # 4. Sort by relevance score and return top_k
        all_results.sort(key=lambda x: x.score, reverse=True)
        return all_results[:top_k]
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_memory_manager.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/memory/manager.py src/memory/retrieval.py tests/test_memory_manager.py
git commit -m "feat: implement memory manager with cross-layer retrieval"
```

---

## Phase 4: Agent Core & Decision Engine

### Task 4.1: Decision Engine

**Files:**
- Create: `src/agent/decision.py`
- Create: `src/agent/core.py`
- Create: `tests/test_decision_engine.py`

- [ ] **Step 1: Write failing tests for decision engine**

```python
# tests/test_decision_engine.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.agent.decision import DecisionEngine, Decision, DecisionBoundary
from src.backend.models.memory import MemorySearchResult, LongTermMemoryItem


class TestDecisionBoundary:
    def test_autonomous_action_classification(self):
        """Test that autonomous actions are correctly classified."""
        boundary = DecisionBoundary()
        assert boundary.get_type("memory_search") == "AUTONOMOUS"
        assert boundary.get_type("response_generation") == "AUTONOMOUS"
    
    def test_confirm_required_action_classification(self):
        """Test that confirm-required actions are correctly classified."""
        boundary = DecisionBoundary()
        assert boundary.get_type("memory_delete") == "CONFIRM_REQUIRED"
        assert boundary.get_type("preference_update") == "CONFIRM_REQUIRED"
    
    def test_forbidden_action_classification(self):
        """Test that forbidden actions are correctly classified."""
        boundary = DecisionBoundary()
        assert boundary.get_type("financial_transaction") == "FORBIDDEN"
    
    def test_unknown_action_defaults_to_confirm(self):
        """Test that unknown actions default to requiring confirmation."""
        boundary = DecisionBoundary()
        assert boundary.get_type("unknown_action") == "CONFIRM_REQUIRED"


class TestDecisionEngine:
    @pytest.fixture
    def mock_memory_manager(self):
        """Mock memory manager."""
        mock = AsyncMock()
        mock.retrieve.return_value = [
            MemorySearchResult(
                memory=LongTermMemoryItem(
                    user_id="user1",
                    content="Prefers coffee",
                    category="food"
                ),
                score=0.9
            )
        ]
        return mock
    
    @pytest.fixture
    def decision_engine(self, mock_memory_manager):
        """Create decision engine with mock dependencies."""
        return DecisionEngine(
            memory_manager=mock_memory_manager,
            llm_service=AsyncMock()
        )
    
    @pytest.mark.asyncio
    async def test_autonomous_action_execution(self, decision_engine):
        """Test that autonomous actions are executed without confirmation."""
        decision = await decision_engine.decide(
            user_input="What do I like to drink?",
            context={"user_id": "user1", "session_id": "abc"}
        )
        
        assert decision.action == "execute"
        assert len(decision.memories_used) > 0
    
    @pytest.mark.asyncio
    async def test_forbidden_action_refusal(self, decision_engine):
        """Test that forbidden actions are refused."""
        decision = await decision_engine.decide(
            user_input="Transfer money from my account",
            context={"user_id": "user1", "session_id": "abc"}
        )
        
        assert decision.action == "refuse"
        assert "not allowed" in decision.reason.lower() or "授权" in decision.reason
    
    @pytest.mark.asyncio
    async def test_confirm_required_action(self, decision_engine):
        """Test that confirm-required actions ask for confirmation."""
        decision = await decision_engine.decide(
            user_input="Delete all my memories",
            context={"user_id": "user1", "session_id": "abc"}
        )
        
        assert decision.action == "confirm"
        assert decision.question is not None
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_decision_engine.py -v
```
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Implement DecisionEngine**

```python
# src/agent/decision.py
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from src.backend.models.memory import MemorySearchResult

logger = logging.getLogger(__name__)


class ActionType(str, Enum):
    """Types of actions the agent can take."""
    EXECUTE = "execute"
    CONFIRM = "confirm"
    REFUSE = "refuse"


@dataclass
class Decision:
    """Represents an agent decision."""
    
    action: ActionType
    reason: str = ""
    plan: Optional[Dict[str, Any]] = None
    memories_used: List[MemorySearchResult] = field(default_factory=list)
    question: Optional[str] = None
    info: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize decision to dictionary."""
        return {
            "action": self.action.value,
            "reason": self.reason,
            "plan": self.plan,
            "memories_count": len(self.memories_used),
            "question": self.question,
            "info": self.info
        }


class DecisionBoundary:
    """
    Defines boundaries for agent autonomous actions.
    
    This is a core component for trustworthy AI - it ensures
    the agent only acts autonomously within defined limits.
    """
    
    # Actions the agent can take without asking
    AUTONOMOUS = {
        "memory_search",
        "context_retrieval",
        "response_generation",
        "memory_consolidation",
        "information_lookup"
    }
    
    # Actions that require user confirmation
    CONFIRM_REQUIRED = {
        "memory_delete",
        "preference_update",
        "external_api_call",
        "file_operation",
        "settings_change"
    }
    
    # Actions the agent must never take autonomously
    FORBIDDEN = {
        "financial_transaction",
        "personal_data_export",
        "account_modification",
        "security_change"
    }
    
    def get_type(self, action: str) -> str:
        """
        Get the boundary type for an action.
        
        Args:
            action: Action name
            
        Returns:
            "AUTONOMOUS", "CONFIRM_REQUIRED", or "FORBIDDEN"
        """
        if action in self.AUTONOMOUS:
            return "AUTONOMOUS"
        elif action in self.FORBIDDEN:
            return "FORBIDDEN"
        else:
            # Default to requiring confirmation for unknown actions
            return "CONFIRM_REQUIRED"
    
    def is_allowed(self, action: str) -> bool:
        """Check if an action is allowed at all."""
        return action not in self.FORBIDDEN


class DecisionEngine:
    """
    Agent decision engine with autonomy boundaries.
    
    Responsibilities:
    - Classify user intent
    - Check action against boundaries
    - Retrieve relevant memories
    - Generate execution plans
    """
    
    def __init__(self, memory_manager, llm_service):
        """
        Initialize decision engine.
        
        Args:
            memory_manager: Memory manager instance
            llm_service: LLM service for intent classification
        """
        self.memory = memory_manager
        self.llm = llm_service
        self.boundary = DecisionBoundary()
    
    async def decide(
        self,
        user_input: str,
        context: Dict[str, Any]
    ) -> Decision:
        """
        Make a decision based on user input and context.
        
        Args:
            user_input: User's message
            context: Current context (user_id, session_id, etc.)
            
        Returns:
            Decision object with action and supporting info
        """
        # 1. Classify intent
        intent = await self._classify_intent(user_input)
        
        # 2. Check boundary
        boundary_type = self.boundary.get_type(intent["action"])
        
        # 3. Handle based on boundary type
        if boundary_type == "FORBIDDEN":
            return Decision(
                action=ActionType.REFUSE,
                reason="此操作需要用户明确授权，我无法自主执行。"
            )
        
        if boundary_type == "CONFIRM_REQUIRED":
            return Decision(
                action=ActionType.CONFIRM,
                question=f"我准备执行：{intent['description']}，确认吗？",
                info=intent
            )
        
        # 4. For AUTONOMOUS actions, retrieve memories and plan
        user_id = context.get("user_id")
        session_id = context.get("session_id")
        
        relevant_memories = []
        if user_id:
            relevant_memories = await self.memory.retrieve(
                user_id=user_id,
                query=user_input,
                session_id=session_id,
                top_k=5
            )
        
        # 5. Generate execution plan
        plan = await self._make_plan(intent, relevant_memories, context)
        
        return Decision(
            action=ActionType.EXECUTE,
            plan=plan,
            memories_used=relevant_memories,
            reason=f"自主执行：{intent['description']}"
        )
    
    async def _classify_intent(self, user_input: str) -> Dict[str, Any]:
        """
        Classify user intent.
        
        Simplified version - in production, use LLM for classification.
        """
        input_lower = user_input.lower()
        
        # Simple keyword-based classification for demo
        if any(kw in input_lower for kw in ["delete", "remove", "删除"]):
            return {
                "action": "memory_delete",
                "description": "删除记忆",
                "confidence": 0.8
            }
        elif any(kw in input_lower for kw in ["remember", "记住", "learn"]):
            return {
                "action": "memory_store",
                "description": "存储新记忆",
                "confidence": 0.9
            }
        elif any(kw in input_lower for kw in ["what", "how", "why", "什么", "怎么", "为什么"]):
            return {
                "action": "memory_search",
                "description": "搜索记忆",
                "confidence": 0.85
            }
        else:
            return {
                "action": "response_generation",
                "description": "生成回复",
                "confidence": 0.7
            }
    
    async def _make_plan(
        self,
        intent: Dict[str, Any],
        memories: List[MemorySearchResult],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate execution plan.
        
        Args:
            intent: Classified intent
            memories: Relevant memories
            context: Current context
            
        Returns:
            Execution plan
        """
        return {
            "intent": intent,
            "memories_to_use": [m.memory.content for m in memories[:3]],
            "steps": [
                "Retrieve relevant context",
                "Generate response",
                "Update memory if needed"
            ]
        }
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_decision_engine.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/agent/decision.py tests/test_decision_engine.py
git commit -m "feat: implement decision engine with autonomy boundaries"
```

---

## Phase 5: API Layer

### Task 5.1: FastAPI Application

**Files:**
- Create: `src/backend/main.py`
- Create: `src/backend/api/chat.py`
- Create: `src/backend/api/memory.py`
- Create: `tests/test_api.py`

- [ ] **Step 1: Write failing tests for API**

```python
# tests/test_api.py
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_api.py -v
```
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Implement FastAPI application**

```python
# src/backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from src.backend.api import chat, memory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="MemoMind API",
    description="Personal AI Assistant with Cognitive Memory Architecture",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(memory.router, prefix="/api", tags=["memory"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "MemoMind",
        "version": "0.1.0"
    }
```

```python
# src/backend/api/__init__.py
"""API routers."""

# src/backend/api/chat.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str = Field(..., min_length=1, max_length=10000)
    session_id: str = Field(default="default")
    user_id: str = Field(default="anonymous")


class MemoryUpdate(BaseModel):
    """Memory update information."""
    type: str
    content: str
    layer: str
    action: str


class DecisionExplanation(BaseModel):
    """Decision explanation."""
    action: str
    confidence: float
    reasoning: str


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str
    memory_updates: List[MemoryUpdate] = []
    decision_explanation: Optional[DecisionExplanation] = None


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process a chat message.
    
    This endpoint:
    1. Receives user message
    2. Processes through memory system
    3. Generates response
    4. Returns response with memory updates
    """
    try:
        # TODO: Integrate with actual agent and memory manager
        # For now, return a mock response
        
        response = f"I received your message: '{request.message}'. "
        
        # Simulate memory extraction
        memory_updates = []
        if "like" in request.message.lower() or "喜欢" in request.message:
            memory_updates.append(MemoryUpdate(
                type="preference",
                content=request.message,
                layer="short_term",
                action="created"
            ))
            response += "I'll remember your preference!"
        
        return ChatResponse(
            response=response,
            memory_updates=memory_updates,
            decision_explanation=DecisionExplanation(
                action="response_generation",
                confidence=0.9,
                reasoning="Processed user message and extracted preferences"
            )
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

```python
# src/backend/api/memory.py
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class MemoryResponse(BaseModel):
    """Memory response model."""
    memory_id: str
    content: str
    layer: str
    created_at: str
    metadata: dict = {}


@router.get("/memories", response_model=List[MemoryResponse])
async def list_memories(
    user_id: str = Query(..., description="User identifier"),
    layer: Optional[str] = Query(None, description="Memory layer filter"),
    limit: int = Query(20, ge=1, le=100)
):
    """
    List memories for a user.
    
    Args:
        user_id: User identifier
        layer: Optional layer filter (working, short_term, long_term, episodic)
        limit: Maximum number of memories to return
    """
    # TODO: Integrate with actual memory manager
    # For now, return mock data
    
    mock_memories = [
        MemoryResponse(
            memory_id="mem_001",
            content="User likes coffee",
            layer="long_term",
            created_at="2024-01-15T10:30:00",
            metadata={"category": "food_preference"}
        ),
        MemoryResponse(
            memory_id="mem_002",
            content="Had meeting about project X",
            layer="short_term",
            created_at="2024-01-20T14:00:00",
            metadata={"type": "event"}
        )
    ]
    
    if layer:
        mock_memories = [m for m in mock_memories if m.layer == layer]
    
    return mock_memories[:limit]


@router.delete("/memories/{memory_id}")
async def delete_memory(memory_id: str):
    """
    Delete a specific memory.
    
    Args:
        memory_id: Memory identifier to delete
    """
    # TODO: Integrate with actual memory manager
    logger.info(f"Deleting memory {memory_id}")
    
    return {"status": "deleted", "memory_id": memory_id}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_api.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/backend/ tests/test_api.py
git commit -m "feat: implement FastAPI backend with chat and memory endpoints"
```

---

## Phase 6: Frontend

### Task 6.1: Next.js Application Setup

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/next.config.js`
- Create: `frontend/tailwind.config.js`
- Create: `frontend/src/app/layout.tsx`
- Create: `frontend/src/app/page.tsx`
- Create: `frontend/src/components/ChatPanel.tsx`

- [ ] **Step 1: Initialize Next.js project**

```bash
cd frontend && npx create-next-app@latest . --typescript --tailwind --app --no-git
```

- [ ] **Step 2: Create ChatPanel component**

```typescript
// frontend/src/components/ChatPanel.tsx
'use client';

import { useState } from 'react';

interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
}

export default function ChatPanel() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: input,
      role: 'user',
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: input,
          session_id: 'demo-session',
          user_id: 'demo-user',
        }),
      });

      const data = await response.json();

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: data.response,
        role: 'assistant',
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Failed to send message:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[600px] bg-white rounded-lg shadow-lg">
      {/* Header */}
      <div className="p-4 border-b bg-blue-600 text-white rounded-t-lg">
        <h2 className="text-lg font-semibold">MemoMind Chat</h2>
        <p className="text-sm opacity-80">Your AI assistant remembers</p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map(message => (
          <div
            key={message.id}
            className={`flex ${
              message.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            <div
              className={`max-w-[70%] p-3 rounded-lg ${
                message.role === 'user'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 text-gray-800'
              }`}
            >
              {message.content}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 p-3 rounded-lg">
              <span className="animate-pulse">Thinking...</span>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="p-4 border-t">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyPress={e => e.key === 'Enter' && sendMessage()}
            placeholder="Type your message..."
            className="flex-1 p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isLoading}
          />
          <button
            onClick={sendMessage}
            disabled={isLoading || !input.trim()}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Update main page**

```typescript
// frontend/src/app/page.tsx
import ChatPanel from '@/components/ChatPanel';

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-center mb-8 text-gray-800">
          MemoMind
        </h1>
        <p className="text-center text-gray-600 mb-8">
          Personal AI Assistant with Cognitive Memory Architecture
        </p>
        <div className="flex justify-center">
          <ChatPanel />
        </div>
      </div>
    </main>
  );
}
```

- [ ] **Step 4: Run frontend to verify**

```bash
cd frontend && npm run dev
```
Expected: Frontend runs on http://localhost:3000

- [ ] **Step 5: Commit**

```bash
git add frontend/
git commit -m "feat: implement Next.js frontend with chat interface"
```

---

## Summary

**Total Tasks:** 11 main tasks with ~50 sub-steps

**Phases:**
1. ✅ Project Setup & Foundation
2. ✅ Memory Layers (Working, Short-term, Long-term, Episodic)
3. ✅ Memory Manager & Consolidation
4. ✅ Agent Core & Decision Engine
5. ✅ API Layer (FastAPI)
6. ✅ Frontend (Next.js)

**Next Steps After Implementation:**
1. Run full integration tests
2. Add environment variables for API keys
3. Deploy with Docker Compose
4. Add more sophisticated LLM integration
5. Implement memory visualization
6. Add user authentication

---

**Plan Version:** v1.0
**Created:** 2026-05-28
