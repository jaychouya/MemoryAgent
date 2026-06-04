"""Redis working-memory layer (deferred — not wired to chat/MemoryManager)."""
import json
import logging
from typing import List, Optional
from datetime import datetime

from src.backend.models.message import Message

logger = logging.getLogger(__name__)


class WorkingMemory:
    """
    Working Memory Layer - Current session context (library/tests only).
    
    Runtime chat uses `sessions/*.json` + Markdown MemoryManager instead.
    
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
