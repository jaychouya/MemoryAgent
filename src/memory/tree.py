"""MemoryTree - Unified memory interface inspired by OpenHuman."""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.memory.storage import MemoryStorage
from src.memory.retrieval import MemoryRetrieval
from src.memory.types import MemoryItem, MemoryType
from src.memory.worker import BackgroundWorker
from src.memory.folder import MemoryFolder

logger = logging.getLogger(__name__)


class MemoryTree:
    """
    MemoryTree - Local-First memory system.
    
    Inspired by OpenHuman's Memory Tree:
    - saveContext: Store interaction in local memory
    - retrieveRelevantContext: Retrieve relevant memories
    - syncFromIntegrations: Sync from external tools (20min loop)
    - dream: Deep memory folding when idle
    """
    
    def __init__(self, base_dir: str = "memories"):
        self.storage = MemoryStorage(base_dir)
        self.retrieval = MemoryRetrieval(self.storage)
        self.folder = MemoryFolder(max_per_group=10)
        self.worker = BackgroundWorker(interval=300)  # 5 minutes
        
        # Register background tasks
        self.worker.register_task(self._sync_memories, interval=1200)  # 20 minutes
        self.worker.register_task(self._dream, interval=3600)  # 1 hour
    
    async def saveContext(self, user_id: str, interaction: Dict[str, Any]) -> bool:
        """
        Save interaction context to local memory.
        
        Args:
            user_id: User identifier
            interaction: Dict with query, reply, metadata
            
        Returns:
            True if successful
        """
        try:
            # Determine memory type
            memory_type = self._classify_interaction(interaction)
            
            # Create memory item
            memory = MemoryItem.create(
                memory_type=memory_type,
                content=interaction.get("query", ""),
                description=interaction.get("reply", "")[:100],
                metadata={
                    "user_id": user_id,
                    "reply": interaction.get("reply", ""),
                    "timestamp": datetime.now().isoformat(),
                    **interaction.get("metadata", {})
                }
            )
            
            # Store
            success = await self.storage.store(memory)
            
            if success:
                logger.info(f"Saved context for user {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to save context: {e}")
            return False
    
    async def retrieveRelevantContext(
        self,
        query: str,
        user_id: str = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant context from local memory.
        
        Args:
            query: User's query
            user_id: User identifier
            limit: Maximum memories to return
            
        Returns:
            List of relevant memories
        """
        return await self.retrieval.retrieve(
            query=query,
            user_id=user_id,
            limit=limit
        )
    
    async def syncFromIntegrations(self, tools: List[Any] = None) -> int:
        """
        Sync memories from external integrations.
        
        This simulates OpenHuman's 20-minute auto-fetch loop.
        
        Args:
            tools: List of integration tools (Gmail, Notion, GitHub, etc.)
            
        Returns:
            Number of new memories synced
        """
        # TODO: Implement actual integration sync
        # For now, this is a placeholder
        logger.info("Syncing from integrations...")
        return 0
    
    async def dream(self) -> Dict[str, Any]:
        """
        Deep memory folding (Dreaming state).
        
        When idle, fold old memories into summaries.
        
        Returns:
            Folding statistics
        """
        try:
            # Get all memories
            all_memories = await self.storage.search(limit=1000)
            
            # Add to folder
            for memory in all_memories:
                self.folder.add_memory({
                    "id": memory.id,
                    "type": memory.type.value,
                    "content": memory.content,
                    "importance": memory.metadata.get("importance", 0.5)
                })
            
            # Fold
            folded = self.folder.fold()
            
            # Get stats
            stats = self.folder.get_stats()
            
            logger.info(f"Dreaming complete: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Dreaming failed: {e}")
            return {"error": str(e)}
    
    def _classify_interaction(self, interaction: Dict[str, Any]) -> MemoryType:
        """Classify interaction into memory type."""
        query = interaction.get("query", "").lower()
        
        # Simple classification
        if any(word in query for word in ["喜欢", "偏好", "习惯", "prefer"]):
            return MemoryType.USER
        elif any(word in query for word in ["不要", "避免", "必须", "应该"]):
            return MemoryType.FEEDBACK
        elif any(word in query for word in ["项目", "截止", "deadline", "任务"]):
            return MemoryType.PROJECT
        else:
            return MemoryType.REFERENCE
    
    def _sync_memories(self):
        """Background task: Sync from integrations."""
        import asyncio
        asyncio.run(self.syncFromIntegrations())
    
    def _dream(self):
        """Background task: Deep memory folding."""
        import asyncio
        asyncio.run(self.dream())
    
    def start(self):
        """Start background worker."""
        self.worker.start()
        logger.info("MemoryTree background worker started")
    
    def stop(self):
        """Stop background worker."""
        self.worker.stop()
        logger.info("MemoryTree background worker stopped")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory tree statistics."""
        import asyncio
        storage_stats = asyncio.run(self.storage.get_stats())
        worker_stats = self.worker.get_stats()
        
        return {
            "storage": storage_stats,
            "worker": worker_stats
        }
