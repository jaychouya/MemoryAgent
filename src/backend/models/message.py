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
