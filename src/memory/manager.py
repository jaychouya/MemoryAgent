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
from pathlib import Path

from src.memory.types import MemoryItem, MemoryType
from src.memory.storage import MemoryStorage
from src.memory.retrieval import MemoryRetrieval
from src.memory.persistent_vector import PersistentVectorStore
from src.memory.conflicts import find_conflicts
from src.memory.exclusions import should_exclude, get_exclusion_reason
from src.memory.embeddings import embed_text
from src.utils.config import settings

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
        self.storage_dir = storage_dir
        db_path = str(Path(storage_dir) / "index.db")
        dim = settings.EMBEDDING_DIMENSIONS or 384
        self.persistent_vectors = PersistentVectorStore(db_path, dimension=dim)
        self.vector_store = self.persistent_vectors.get_vector_store()
        self.storage = MemoryStorage(storage_dir)
        self.retrieval = MemoryRetrieval(
            self.storage, llm_service, vector_store=self.vector_store
        )
        self.llm = llm_service
        if self.vector_store.size() == 0:
            rows = self.storage.index.search(query="", limit=5000)
            self.persistent_vectors.backfill_from_index_rows(rows)
    
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
            supersedes = memory.metadata.get("supersedes")
            if supersedes:
                await self.storage.update_metadata(
                    str(supersedes),
                    {
                        "superseded_by": memory.id,
                        "valid_until": datetime.now().isoformat(),
                    },
                )
                self.persistent_vectors.delete(str(supersedes))
            elif user_id:
                await self._auto_supersede_conflicts(memory, user_id)
            uid = user_id or memory.metadata.get("user_id")
            self.persistent_vectors.upsert(
                memory_id=memory.id,
                content=memory.content,
                user_id=uid,
                memory_type=memory.type.value,
                embedding=embed_text(memory.content),
            )
            return memory
        return None

    async def _auto_supersede_conflicts(self, memory: MemoryItem, user_id: str) -> None:
        rows = self.storage.index.search(
            query="",
            user_id=user_id,
            memory_type=memory.type.value,
            project_id=memory.metadata.get("project_id"),
            limit=100,
        )
        rows = [r for r in rows if (r.get("memory_id") or "") != memory.id]
        conflicts = find_conflicts(
            memory.content,
            rows,
            user_id=user_id,
            project_id=memory.metadata.get("project_id"),
            memory_type=memory.type.value,
        )
        for row in conflicts:
            old_id = row.get("memory_id") or row.get("id")
            if not old_id:
                continue
            await self.storage.update_metadata(
                old_id,
                {
                    "superseded_by": memory.id,
                    "valid_until": datetime.now().isoformat(),
                    "conflict_reason": row.get("conflict_reason", "auto_conflict"),
                },
            )
            self.persistent_vectors.delete(old_id)

    async def delete_memory(self, memory_id: str) -> bool:
        ok = await self.storage.delete(memory_id)
        if ok:
            self.persistent_vectors.delete(memory_id)
        return ok

    async def owns_memory(self, memory_id: str, user_id: str) -> bool:
        memory = await self.storage.retrieve(memory_id)
        if not memory:
            return False
        mem_user = memory.metadata.get("user_id")
        return mem_user == user_id

    async def update_memory(
        self,
        memory_id: str,
        content: str = None,
        description: str = None,
    ) -> bool:
        ok = await self.storage.update(memory_id, content=content, description=description)
        if ok:
            mem = await self.storage.retrieve(memory_id)
            if mem:
                self.persistent_vectors.upsert(
                    memory_id=mem.id,
                    content=mem.content,
                    user_id=mem.metadata.get("user_id"),
                    memory_type=mem.type.value,
                    embedding=embed_text(mem.content),
                )
        return ok

    async def list_memories(
        self,
        user_id: str,
        project_id: str = None,
        memory_type: str = None,
        limit: int = 20,
    ) -> List[Dict]:
        rows = self.storage.index.search(
            query="",
            user_id=user_id,
            memory_type=memory_type,
            project_id=project_id,
            limit=limit * 2,
        )
        out = []
        for row in rows:
            uid = row.get("user_id")
            mid = row.get("memory_id") or ""
            if uid != user_id:
                continue
            pid = row.get("project_id")
            if project_id and pid and pid != project_id:
                continue
            try:
                item = await self.storage.retrieve(mid)
                if item:
                    row["content"] = item.content
                    row["description"] = item.description
                    for key in (
                        "source_session_id",
                        "source_turn",
                        "source_quote",
                        "supersedes",
                        "superseded_by",
                        "valid_until",
                        "conflict_reason",
                    ):
                        if item.metadata.get(key) is not None:
                            row[key] = item.metadata.get(key)
            except Exception:
                pass
            row["project_id"] = pid
            out.append(row)
        return out[:limit]
    
    async def retrieve(
        self,
        query: str,
        user_id: str = None,
        session_id: str = None,
        project_id: str = None,
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
        results = await self.retrieval.retrieve(
            query=query,
            user_id=user_id,
            project_id=project_id,
            limit=top_k,
        )
        return results
    
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
