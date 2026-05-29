"""
Enhanced Memory Manager for MemoryAI Agent.

Implements Claude Code's memory architecture:
- Four-type memory classification
- File-based storage with markdown
- LLM-based retrieval
- Exclusion rules
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.memory.types import MemoryItem, MemoryType
from src.memory.storage import MemoryStorage
from src.memory.retrieval import MemoryRetrieval
from src.memory.exclusions import should_exclude, get_exclusion_reason

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Central memory manager with Claude Code-style architecture.
    
    Key features:
    1. Four-type memory classification
    2. File-based storage (markdown + YAML)
    3. LLM-based retrieval
    4. Exclusion rules
    5. Staleness detection
    """
    
    def __init__(
        self,
        storage_dir: str = "memories",
        llm_service=None
    ):
        self.storage = MemoryStorage(storage_dir)
        self.retrieval = MemoryRetrieval(self.storage, llm_service)
        self.llm = llm_service
    
    async def store(
        self,
        content: str,
        memory_type: MemoryType,
        description: str = None,
        user_id: str = None,
        metadata: Dict[str, Any] = None
    ) -> Optional[MemoryItem]:
        """
        Store a new memory.
        
        Args:
            content: Memory content
            memory_type: Type of memory
            description: One-line description
            user_id: User identifier
            metadata: Additional metadata
            
        Returns:
            Stored MemoryItem or None if excluded
        """
        # Check exclusion rules
        if should_exclude(content, memory_type.value):
            reason = get_exclusion_reason(content)
            logger.info(f"Memory excluded ({reason.value}): {content[:50]}...")
            return None
        
        # Create memory item
        memory = MemoryItem.create(
            memory_type=memory_type,
            content=content,
            description=description,
            metadata={
                "user_id": user_id,
                **(metadata or {})
            }
        )
        
        # Store
        success = await self.storage.store(memory)
        
        if success:
            return memory
        return None
    
    async def retrieve(
        self,
        query: str,
        user_id: str = None,
        session_id: str = None,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Retrieve relevant memories.
        
        Args:
            query: Search query
            user_id: User identifier
            session_id: Session identifier
            top_k: Maximum results
            
        Returns:
            List of memory dicts with content and metadata
        """
        return await self.retrieval.retrieve(
            query=query,
            user_id=user_id,
            limit=top_k
        )
    
    async def store_user_preference(
        self,
        preference: str,
        user_id: str
    ) -> Optional[MemoryItem]:
        """Store a user preference."""
        return await self.store(
            content=preference,
            memory_type=MemoryType.USER,
            description=f"用户偏好: {preference[:30]}",
            user_id=user_id
        )
    
    async def store_feedback(
        self,
        rule: str,
        reason: str,
        user_id: str
    ) -> Optional[MemoryItem]:
        """Store a behavioral feedback rule."""
        content = f"{rule}\n\n**原因:** {reason}"
        return await self.store(
            content=content,
            memory_type=MemoryType.FEEDBACK,
            description=f"行为规则: {rule[:30]}",
            user_id=user_id
        )
    
    async def store_project_info(
        self,
        info: str,
        deadline: str = None,
        user_id: str = None
    ) -> Optional[MemoryItem]:
        """Store project information."""
        content = info
        if deadline:
            content += f"\n\n**截止日期:** {deadline}"
        
        return await self.store(
            content=content,
            memory_type=MemoryType.PROJECT,
            description=f"项目信息: {info[:30]}",
            user_id=user_id
        )
    
    async def store_reference(
        self,
        what: str,
        where: str,
        user_id: str = None
    ) -> Optional[MemoryItem]:
        """Store an external reference pointer."""
        content = f"**{what}**\n\n位置: {where}"
        return await self.store(
            content=content,
            memory_type=MemoryType.REFERENCE,
            description=f"外部引用: {what[:30]}",
            user_id=user_id
        )
    
    async def get_stats(self) -> Dict[str, int]:
        """Get memory statistics."""
        return await self.storage.get_stats()
    
    async def format_for_prompt(self, query: str, user_id: str = None) -> str:
        """Get formatted memories for system prompt."""
        memories = await self.retrieve(query, user_id)
        return await self.retrieval.format_for_prompt(memories)
