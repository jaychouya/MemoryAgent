"""
Memory retrieval system for MemoryAI Agent.

Implements Claude Code's memory recall pattern:
- Scan memory file headers (first 30 lines)
- Use LLM to select relevant memories
- Staleness detection for old memories
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime

from src.memory.types import MemoryItem, MemoryType, MEMORY_TYPE_DESCRIPTIONS
from src.memory.storage import MemoryStorage

logger = logging.getLogger(__name__)


class MemoryRetrieval:
    """
    Memory retrieval system.
    
    Key features from Claude Code:
    1. Scan headers only (fast)
    2. LLM-based selection (accurate)
    3. Staleness detection (reliable)
    """
    
    STALENESS_WARNING_TEMPLATE = (
        "这条记忆已经有 {days} 天了。"
        "记忆是某个时间点的观察，不是实时状态——"
        "其中关于代码行为或 file:line 引用的断言可能已经过时。"
        "在当作事实引用之前，请先对照当前代码验证。"
    )
    
    def __init__(self, storage: MemoryStorage, llm_service=None):
        self.storage = storage
        self.llm = llm_service
    
    async def retrieve(
        self,
        query: str,
        user_id: str = None,
        limit: int = 5
    ) -> List[Dict]:
        """
        Retrieve relevant memories using SQLite index.
        
        Args:
            query: User's query
            user_id: User identifier
            limit: Maximum memories to return
            
        Returns:
            List of memory dicts with content and staleness info
        """
        # 使用 SQLite 索引搜索
        results = self.storage.index.search(
            query=query,
            user_id=user_id,
            limit=limit
        )
        
        # 添加过时警告
        for result in results:
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
                except:
                    result["age_days"] = 0
                    result["is_stale"] = False
                    result["staleness_warning"] = None
            else:
                result["age_days"] = 0
                result["is_stale"] = False
                result["staleness_warning"] = None
        
        return results
    
    async def _select_with_llm(
        self,
        query: str,
        memories: List[MemoryItem],
        limit: int
    ) -> List[MemoryItem]:
        """
        Use LLM to select relevant memories.
        
        Similar to Claude Code's Sonnet-based selection.
        """
        # Build manifest
        manifest_lines = []
        for mem in memories:
            manifest_lines.append(
                f"- [{mem.type.value}] {mem.id} ({mem.age_days()}d): {mem.description}"
            )
        
        manifest = "\n".join(manifest_lines)
        
        prompt = f"""你是一个记忆选择器。从以下记忆列表中，选择最多 {limit} 条与用户问题最相关的记忆。

用户问题: {query}

可用的记忆:
{manifest}

请只返回选中的记忆ID列表，用逗号分隔。如果没有相关记忆，返回空。"""
        
        try:
            response = await self.llm.generate_response(
                message=prompt,
                system_prompt="你是一个记忆选择器。只返回记忆ID列表。"
            )
            
            # Parse response
            content = response.get("content", "")
            selected_ids = [id.strip() for id in content.split(",") if id.strip()]
            
            # Map to memory items
            selected = []
            for mem in memories:
                if mem.id in selected_ids:
                    selected.append(mem)
                    if len(selected) >= limit:
                        break
            
            return selected or memories[:limit]
            
        except Exception as e:
            logger.warning(f"LLM selection failed, using fallback: {e}")
            return self._select_with_keywords(query, memories, limit)
    
    def _select_with_keywords(
        self,
        query: str,
        memories: List[MemoryItem],
        limit: int
    ) -> List[MemoryItem]:
        """Simple keyword-based selection fallback."""
        query_lower = query.lower()
        scored = []
        
        for mem in memories:
            score = 0
            
            # Check description match
            if query_lower in mem.description.lower():
                score += 2
            
            # Check content match
            if query_lower in mem.content.lower():
                score += 1
            
            # Boost recent memories
            if not mem.is_stale():
                score += 0.5
            
            if score > 0:
                scored.append((score, mem))
        
        # Sort by score
        scored.sort(key=lambda x: x[0], reverse=True)
        
        return [mem for _, mem in scored[:limit]]
    
    async def format_for_prompt(self, memories: List[Dict]) -> str:
        """Format memories for system prompt injection."""
        if not memories:
            return ""
        
        lines = ["## 相关记忆\n"]
        
        for mem in memories:
            lines.append(f"### {mem['description']}")
            lines.append(f"类型: {MEMORY_TYPE_DESCRIPTIONS.get(mem['type'], mem['type'])}")
            lines.append(f"\n{mem['content']}\n")
            
            if mem.get("staleness_warning"):
                lines.append(f"⚠️ {mem['staleness_warning']}\n")
        
        return "\n".join(lines)
