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
            user_id="user1",
            session_id="abc123",
            content="Current context"
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
