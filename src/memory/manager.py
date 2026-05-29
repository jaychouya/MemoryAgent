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
        working_memory,
        short_term_memory,
        long_term_memory,
        episodic_memory
    ):
        """Initialize memory manager with all layers."""
        self.working = working_memory
        self.short_term = short_term_memory
        self.long_term = long_term_memory
        self.episodic = episodic_memory
    
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
        all_results: List[MemorySearchResult] = []
        
        # 1. Get working memory context
        if session_id:
            working_context = await self.working.get_context(session_id)
            # Add recent messages as context
            for msg in working_context[-3:]:
                all_results.append(MemorySearchResult(
                    memory=type('obj', (object,), {
                        'content': msg.get('content', ''),
                        'layer': MemoryLayer.WORKING,
                        'to_dict': lambda: msg
                    })(),
                    score=0.5,  # Lower priority for working memory
                    retrieval_method="context"
                ))
        
        # 2. Search short-term memory
        try:
            short_term_results = await self.short_term.search(
                user_id=user_id,
                query=query,
                top_k=top_k // 2
            )
            all_results.extend(short_term_results)
        except Exception as e:
            logger.error(f"Error searching short-term memory: {e}")
        
        # 3. Search long-term memory
        try:
            long_term_results = await self.long_term.retrieve(
                user_id=user_id,
                query=query,
                top_k=top_k // 2
            )
            all_results.extend(long_term_results)
        except Exception as e:
            logger.error(f"Error searching long-term memory: {e}")
        
        # 4. Search episodic memory
        try:
            episodic_results = await self.episodic.search(
                user_id=user_id,
                query=query,
                top_k=top_k // 4
            )
            all_results.extend(episodic_results)
        except Exception as e:
            logger.error(f"Error searching episodic memory: {e}")
        
        # 5. Sort by relevance score and return top_k
        all_results.sort(key=lambda x: x.score, reverse=True)
        return all_results[:top_k]
    
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
