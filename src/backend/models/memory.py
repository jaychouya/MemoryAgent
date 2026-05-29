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
    content: str = ""
    description: str = ""
    emotion: Optional[str] = None
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    related_episodes: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)
    
    def __init__(self, **data):
        if 'content' not in data or not data['content']:
            data['content'] = data.get('description', '')
        super().__init__(**data)


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
