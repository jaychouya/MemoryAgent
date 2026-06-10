"""Streaming support for real-time AI responses."""

import json
import logging
from typing import Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class StreamEventType(str, Enum):
    """Types of streaming events."""
    TOKEN = "token"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    ERROR = "error"
    DONE = "done"
    MEMORY_WRITES = "memory_writes"


@dataclass
class StreamEvent:
    """A single streaming event."""
    type: StreamEventType
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_sse(self) -> str:
        """Convert to SSE format."""
        data = {
            "type": self.type.value,
            "content": self.content,
            "metadata": self.metadata
        }
        return f"data: {json.dumps(data)}\n\n"


class StreamingManager:
    """Manages streaming responses."""
    
    def __init__(self):
        self.events: list = []
    
    def create_token_event(self, token: str) -> StreamEvent:
        """Create a token event."""
        event = StreamEvent(
            type=StreamEventType.TOKEN,
            content=token
        )
        self.events.append(event)
        return event
    
    def create_tool_call_event(self, tool_name: str, arguments: Dict) -> StreamEvent:
        """Create a tool call event."""
        event = StreamEvent(
            type=StreamEventType.TOOL_CALL,
            content=tool_name,
            metadata={"arguments": arguments}
        )
        self.events.append(event)
        return event
    
    def create_tool_result_event(self, tool_name: str, result: str) -> StreamEvent:
        """Create a tool result event."""
        event = StreamEvent(
            type=StreamEventType.TOOL_RESULT,
            content=result,
            metadata={"tool_name": tool_name}
        )
        self.events.append(event)
        return event
    
    def create_error_event(self, error: str) -> StreamEvent:
        """Create an error event."""
        event = StreamEvent(
            type=StreamEventType.ERROR,
            content=error
        )
        self.events.append(event)
        return event
    
    def create_done_event(self) -> StreamEvent:
        """Create a done event."""
        event = StreamEvent(
            type=StreamEventType.DONE,
            content=""
        )
        self.events.append(event)
        return event
    
    async def stream_response(
        self,
        generator: AsyncGenerator[str, None]
    ) -> AsyncGenerator[str, None]:
        """Stream response as SSE events."""
        try:
            async for token in generator:
                event = self.create_token_event(token)
                yield event.to_sse()
            
            # Send done event
            done_event = self.create_done_event()
            yield done_event.to_sse()
            
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            error_event = self.create_error_event(str(e))
            yield error_event.to_sse()
    
    def get_events(self) -> list:
        """Get all events."""
        return self.events.copy()
    
    def clear(self):
        """Clear all events."""
        self.events.clear()
