"""
Memory retrieval system for MemoryAI Agent.
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime

from src.memory.types import MemoryType, MEMORY_TYPE_DESCRIPTIONS
from src.memory.storage import MemoryStorage
from src.memory.vector_store import VectorStore, HybridRetriever
from src.memory.embeddings import local_embed

logger = logging.getLogger(__name__)


class MemoryRetrieval:
    """Hybrid keyword + vector retrieval with staleness warnings."""

    STALENESS_WARNING_TEMPLATE = (
        "这条记忆已经有 {days} 天了。"
        "记忆是某个时间点的观察，不是实时状态——"
        "其中关于代码行为或 file:line 引用的断言可能已经过时。"
        "在当作事实引用之前，请先对照当前代码验证。"
    )

    def __init__(
        self,
        storage: MemoryStorage,
        llm_service=None,
        vector_store: Optional[VectorStore] = None
    ):
        self.storage = storage
        self.llm = llm_service
        self.vector_store = vector_store or VectorStore()
        self.hybrid = HybridRetriever(self.vector_store)

    def index_memory_vector(
        self,
        memory_id: str,
        content: str,
        user_id: str = None,
        memory_type: str = "user"
    ):
        """Add or refresh vector index entry for a memory."""
        try:
            embedding = local_embed(content)
            self.vector_store.add(
                text=content,
                embedding=embedding,
                metadata={
                    "user_id": user_id,
                    "memory_type": memory_type,
                },
                id=memory_id,
            )
        except Exception as e:
            logger.warning(f"Vector index failed for {memory_id}: {e}")

    async def retrieve(
        self,
        query: str,
        user_id: str = None,
        limit: int = 5
    ) -> List[Dict]:
        keyword_results = self.storage.index.search(
            query=query or "",
            user_id=user_id,
            limit=limit * 2
        )

        if user_id:
            keyword_results = [
                r for r in keyword_results
                if r.get("user_id") == user_id
                or (r.get("memory_id") or "").startswith(f"{user_id}_")
            ]

        if not keyword_results and user_id:
            keyword_results = self.storage.index.search(
                query="",
                user_id=user_id,
                limit=limit * 2
            )
            keyword_results = [
                r for r in keyword_results
                if r.get("user_id") == user_id
                or (r.get("memory_id") or "").startswith(f"{user_id}_")
            ]

        selection_reason = "fallback_all_user"
        if query and keyword_results:
            try:
                query_embedding = local_embed(query)
                merged = await self.hybrid.retrieve(
                    query=query,
                    query_embedding=query_embedding,
                    keyword_results=keyword_results,
                    top_k=limit
                )
                results = self._normalize_hybrid_results(merged, limit)
                selection_reason = "keyword+vector"
            except Exception as e:
                logger.warning(f"Hybrid retrieval failed, using keyword only: {e}")
                results = keyword_results[:limit]
                selection_reason = "keyword_only"
        else:
            results = keyword_results[:limit]
            selection_reason = "fallback_all_user" if not query else "keyword_only"

        if user_id:
            results = [
                r for r in results
                if r.get("user_id") == user_id
                or (r.get("memory_id") or r.get("id") or "").startswith(f"{user_id}_")
            ]

        for result in results:
            self._apply_staleness(result)
            result["selection_reason"] = selection_reason

        return results[:limit]

    def _normalize_hybrid_results(self, merged: List[Dict], limit: int) -> List[Dict]:
        normalized = []
        for item in merged[:limit]:
            doc_id = item.get("id") or item.get("memory_id", "")
            text = item.get("text") or item.get("content", "")
            normalized.append({
                "memory_id": doc_id,
                "id": doc_id,
                "content": text,
                "memory_type": item.get("metadata", {}).get("memory_type")
                or item.get("memory_type", "user"),
                "user_id": item.get("metadata", {}).get("user_id")
                or item.get("user_id"),
                "score": item.get("score", 0.0),
                "description": text[:80] if text else "",
            })
        return normalized

    def _apply_staleness(self, result: Dict):
        created_at = result.get("created_at")
        if created_at:
            try:
                created = datetime.fromisoformat(created_at)
                age_days = (datetime.now() - created).days
                result["age_days"] = age_days
                result["is_stale"] = age_days > 1
                if result["is_stale"]:
                    result["staleness_warning"] = self.STALENESS_WARNING_TEMPLATE.format(
                        days=age_days
                    )
                else:
                    result["staleness_warning"] = None
                return
            except Exception:
                pass
        result["age_days"] = 0
        result["is_stale"] = False
        result["staleness_warning"] = None

    async def format_for_prompt(self, memories: List[Dict]) -> str:
        if not memories:
            return ""

        lines = ["## 相关记忆\n"]
        for mem in memories:
            mem_type = mem.get("memory_type") or mem.get("type", "user")
            desc = mem.get("description") or (mem.get("content", "")[:80])
            lines.append(f"### {desc}")
            try:
                type_label = MEMORY_TYPE_DESCRIPTIONS[MemoryType(mem_type)]
            except (ValueError, KeyError):
                type_label = str(mem_type)
            lines.append(f"类型: {type_label}")
            lines.append(f"\n{mem.get('content', '')}\n")
            if mem.get("staleness_warning"):
                lines.append(f"⚠️ {mem['staleness_warning']}\n")
        return "\n".join(lines)
