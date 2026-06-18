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
from src.memory.trust import initial_trust, boost_on_recall, reset_on_user_correction
from src.utils.config import settings

SEMANTIC_DEDUP_THRESHOLD = 0.92

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
        metadata: Dict[str, Any] = None,
        auto_supersede: bool = True,
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

        if user_id and await self._is_semantic_duplicate(content, user_id):
            logger.info(f"Memory skipped (semantic dedup): {content[:50]}...")
            return None

        # Create memory item
        meta = {"user_id": user_id, **(metadata or {})}
        if meta.get("trust_score") is None:
            meta["trust_score"] = initial_trust(memory_type.value)
        memory = MemoryItem.create(
            memory_type=memory_type,
            content=content,
            description=description,
            metadata=meta,
        )
        
        # Store
        success = await self.storage.store(memory)
        
        if success:
            supersedes = memory.metadata.get("supersedes")
            if supersedes:
                await self._retire_memory(
                    str(supersedes),
                    memory.id,
                    conflict_reason="explicit_supersedes",
                )
            elif user_id and auto_supersede:
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

    async def _retire_memory(
        self,
        memory_id: str,
        superseded_by: str,
        conflict_reason: str = "auto_conflict",
    ) -> None:
        await self.storage.update_metadata(
            memory_id,
            {
                "superseded_by": superseded_by,
                "valid_until": datetime.now().isoformat(),
                "conflict_reason": conflict_reason,
            },
        )
        self.storage.index.delete(memory_id)
        self.persistent_vectors.delete(memory_id)

    async def _is_semantic_duplicate(self, content: str, user_id: str) -> bool:
        try:
            query_emb = embed_text(content)
            hits = self.vector_store.search(
                query_embedding=query_emb,
                top_k=3,
                user_id=user_id,
            )
            for hit in hits:
                score = float(hit.get("score") or 0)
                if score >= SEMANTIC_DEDUP_THRESHOLD:
                    return True
        except Exception as e:
            logger.debug(f"Semantic dedup skip: {e}")
        return False

    async def record_recall_usage(self, memory_ids: List[str]) -> None:
        for mid in memory_ids:
            if not mid:
                continue
            try:
                item = await self.storage.retrieve(mid)
                if not item:
                    continue
                trust = boost_on_recall(item.metadata.get("trust_score"))
                await self.storage.update_metadata(
                    mid,
                    {
                        "trust_score": trust,
                        "recall_count": int(item.metadata.get("recall_count") or 0) + 1,
                        "last_recalled_at": datetime.now().isoformat(),
                    },
                )
            except Exception as e:
                logger.debug(f"Trust bump skip {mid}: {e}")

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
            await self._retire_memory(
                old_id,
                memory.id,
                conflict_reason=row.get("conflict_reason", "auto_conflict"),
            )

    async def resolve_conflict(
        self,
        keep_id: str,
        supersede_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        item = await self.storage.retrieve(supersede_id)
        if not item:
            return {"ok": False, "reason": "not_found"}
        owner = item.metadata.get("user_id")
        if user_id and owner and owner != user_id:
            return {"ok": False, "reason": "forbidden"}
        await self._retire_memory(
            supersede_id,
            keep_id,
            conflict_reason="user_resolved",
        )
        return {"ok": True, "superseded": supersede_id, "kept": keep_id}

    async def store_resolved_conflict(
        self,
        content: str,
        memory_type: MemoryType,
        supersede_ids: List[str],
        user_id: str,
        project_id: str = None,
        session_id: str = None,
    ) -> Optional[MemoryItem]:
        meta: Dict[str, Any] = {"user_id": user_id, "source": "conflict_resolve"}
        if project_id:
            meta["project_id"] = project_id
        if session_id:
            meta["source_session_id"] = session_id
        if supersede_ids:
            meta["supersedes"] = supersede_ids[0]
        item = await self.store(
            content=content,
            memory_type=memory_type,
            description=f"用户确认: {content[:30]}",
            user_id=user_id,
            metadata=meta,
            auto_supersede=False,
        )
        if item and len(supersede_ids) > 1:
            for old_id in supersede_ids[1:]:
                await self.resolve_conflict(item.id, old_id, user_id)
        return item

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
                await self.storage.update_metadata(
                    memory_id,
                    {
                        "trust_score": reset_on_user_correction(mem.type.value),
                        "user_corrected_at": datetime.now().isoformat(),
                    },
                )
                self.persistent_vectors.upsert(
                    memory_id=mem.id,
                    content=mem.content,
                    user_id=mem.metadata.get("user_id"),
                    memory_type=mem.type.value,
                    embedding=embed_text(mem.content),
                )
        return ok

    async def list_archived_memories(
        self,
        user_id: str,
        project_id: str = None,
        limit: int = 30,
    ) -> List[Dict]:
        out: List[Dict] = []
        for mt in MemoryType:
            type_dir = self.storage.base_dir / mt.value
            if not type_dir.exists():
                continue
            for file_path in type_dir.glob("*.md"):
                try:
                    raw = file_path.read_text(encoding="utf-8")
                    item = MemoryItem.from_markdown(raw, file_path.stem)
                except Exception:
                    continue
                uid = item.metadata.get("user_id")
                if uid != user_id:
                    continue
                pid = item.metadata.get("project_id")
                if project_id and pid and pid != project_id:
                    continue
                if not item.metadata.get("superseded_by"):
                    continue
                out.append({
                    "memory_id": item.id,
                    "content": item.content,
                    "description": item.description,
                    "memory_type": item.type.value,
                    "user_id": uid,
                    "project_id": pid,
                    "superseded_by": item.metadata.get("superseded_by"),
                    "valid_until": item.metadata.get("valid_until"),
                    "conflict_reason": item.metadata.get("conflict_reason"),
                    "updated_at": item.updated_at.isoformat() if item.updated_at else "",
                })
        out.sort(key=lambda r: r.get("valid_until") or r.get("updated_at") or "", reverse=True)
        return out[:limit]

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
        top_k: int = 5,
        fast: bool = False,
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
        from src.utils import as_int

        top_k = as_int(top_k, 5)
        return await self.retrieval.retrieve(
            query=query,
            user_id=user_id,
            project_id=project_id,
            limit=top_k,
            fast=fast,
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
    
    async def count_memories(
        self,
        user_id: str,
        project_id: str = None,
    ) -> int:
        return self.storage.index.count(user_id=user_id, project_id=project_id)

    def get_active_stats(
        self,
        user_id: str = None,
        project_id: str = None,
    ) -> Dict[str, int]:
        by_type = self.storage.index.counts_by_type(user_id=user_id, project_id=project_id)
        return {
            "total": sum(by_type.values()),
            "user": by_type.get("user", 0),
            "feedback": by_type.get("feedback", 0),
            "project": by_type.get("project", 0),
            "reference": by_type.get("reference", 0),
        }

    async def get_stats(self) -> Dict[str, int]:
        """Get memory statistics."""
        return await self.storage.get_stats()
    
    async def format_for_prompt(self, query: str, user_id: str = None) -> str:
        """Get formatted memories for system prompt."""
        memories = await self.retrieve(query, user_id)
        return await self.retrieval.format_for_prompt(memories)
