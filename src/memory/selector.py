"""LLM-based memory selector - inspired by Claude Code's findRelevantMemories."""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class MemorySelector:
    """
    LLM-based memory selector.
    
    Inspired by Claude Code's findRelevantMemories:
    - Scans memory headers (first 30 lines)
    - Builds a title list
    - Uses LLM to select top-5
    - Filters already surfaced memories
    - Filters tool documentation (but keeps warnings)
    """
    
    # 老化警告阈值（天）
    STALE_WARNING_DAYS = 2
    
    # 系统提示词
    SYSTEM_PROMPT = """你是一个记忆选择器。从可用记忆列表中，选择与用户问题最相关的记忆。

规则：
1. 只选择你确定会有帮助的记忆
2. 宁可少选，不可错选
3. 不确定的就别选
4. 优先选择最近的记忆

输出格式（JSON 数组）：
```json
["memory_id_1", "memory_id_2", "memory_id_3", "memory_id_4", "memory_id_5"]
```

如果没有相关记忆，返回空数组 `[]`。"""
    
    def __init__(self, llm_service=None):
        self.llm = llm_service
        self.already_surfaced: set = set()  # 已展示的记忆 ID
    
    async def select(
        self,
        query: str,
        memories: List[Dict[str, Any]],
        top_k: int = 5,
        recent_tools: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Select relevant memories using LLM.
        
        Args:
            query: User's query
            memories: All available memories
            top_k: Number of memories to select
            recent_tools: Recently used tools (to filter docs)
            
        Returns:
            List of selected memories
        """
        if not memories:
            return []
        
        if not self.llm:
            # Fallback: simple keyword matching
            return self._fallback_select(query, memories, top_k)
        
        # 过滤已展示的记忆
        candidates = [
            m for m in memories
            if m.get("id") not in self.already_surfaced
        ]
        
        # 过滤工具文档（保留警告）
        if recent_tools:
            candidates = self._filter_tool_docs(candidates, recent_tools)
        
        if not candidates:
            return []
        
        # 构建记忆清单
        manifest = self._build_manifest(candidates)
        
        # 调用 LLM 选择
        try:
            selected_ids = await self._call_llm(query, manifest, top_k)
            
            # 匹配记忆
            selected = []
            for memory in candidates:
                if memory.get("id") in selected_ids:
                    selected.append(memory)
                    self.already_surfaced.add(memory.get("id"))
                    
                    if len(selected) >= top_k:
                        break
            
            # 添加老化警告
            for memory in selected:
                memory["stale_warning"] = self._get_stale_warning(memory)
            
            logger.info(f"Selected {len(selected)} memories for query")
            return selected
            
        except Exception as e:
            logger.error(f"LLM selection failed: {e}")
            return self._fallback_select(query, candidates, top_k)
    
    def _build_manifest(self, memories: List[Dict[str, Any]]) -> str:
        """Build memory manifest for LLM."""
        lines = []
        
        for memory in memories:
            memory_id = memory.get("id", "unknown")
            description = memory.get("description", "")[:80]
            memory_type = memory.get("type", "unknown")
            age_days = self._calculate_age(memory.get("created_at"))
            
            age_str = ""
            if age_days is not None:
                if age_days == 0:
                    age_str = " (今天)"
                elif age_days == 1:
                    age_str = " (昨天)"
                else:
                    age_str = f" ({age_days}天前)"
            
            lines.append(f"- {memory_id}: {description} [{memory_type}]{age_str}")
        
        return "\n".join(lines)
    
    async def _call_llm(
        self,
        query: str,
        manifest: str,
        top_k: int
    ) -> set:
        """Call LLM to select memories."""
        prompt = f"""用户问题: {query}

可用记忆:
{manifest}

请选择最多 {top_k} 条最相关的记忆。返回 JSON 数组格式的记忆 ID 列表。"""
        
        response = await self.llm.generate_response(
            message=prompt,
            system_prompt=self.SYSTEM_PROMPT
        )
        
        content = response.get("content", "")
        
        # 解析 JSON
        try:
            json_start = content.find("[")
            json_end = content.rfind("]") + 1
            
            if json_start == -1 or json_end == 0:
                return set()
            
            json_str = content[json_start:json_end]
            selected_ids = json.loads(json_str)
            
            return set(selected_ids)
            
        except json.JSONDecodeError:
            return set()
    
    def _fallback_select(
        self,
        query: str,
        memories: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Fallback: simple keyword matching."""
        query_lower = query.lower()
        scored = []
        
        for memory in memories:
            score = 0
            
            description = memory.get("description", "").lower()
            content = memory.get("content", "").lower()
            
            # 关键词匹配
            if query_lower in description:
                score += 3
            if query_lower in content:
                score += 1
            
            # 最近的记忆加分
            age_days = self._calculate_age(memory.get("created_at"))
            if age_days is not None:
                if age_days <= 1:
                    score += 2
                elif age_days <= 7:
                    score += 1
            
            if score > 0:
                scored.append((score, memory))
        
        # 按分数排序
        scored.sort(key=lambda x: x[0], reverse=True)
        
        # 返回 top-k
        selected = [memory for _, memory in scored[:top_k]]
        
        # 添加老化警告
        for memory in selected:
            memory["stale_warning"] = self._get_stale_warning(memory)
        
        return selected
    
    def _filter_tool_docs(
        self,
        memories: List[Dict[str, Any]],
        recent_tools: List[str]
    ) -> List[Dict[str, Any]]:
        """Filter out tool documentation (keep warnings)."""
        filtered = []
        
        for memory in memories:
            description = memory.get("description", "").lower()
            memory_type = memory.get("type", "")
            
            # 检查是否是工具文档
            is_tool_doc = False
            for tool in recent_tools:
                if tool.lower() in description:
                    is_tool_doc = True
                    break
            
            # 如果是工具文档，只保留警告/坑点
            if is_tool_doc:
                # 检查是否包含警告关键词
                warning_keywords = ["警告", "注意", "坑", "问题", "错误", "warning", "caution", "issue"]
                has_warning = any(kw in description for kw in warning_keywords)
                
                if has_warning:
                    filtered.append(memory)
            else:
                filtered.append(memory)
        
        return filtered
    
    def _calculate_age(self, created_at: Any) -> Optional[int]:
        """Calculate age in days."""
        if not created_at:
            return None
        
        try:
            if isinstance(created_at, str):
                created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            else:
                created = created_at
            
            return (datetime.now() - created.replace(tzinfo=None)).days
        except:
            return None
    
    def _get_stale_warning(self, memory: Dict[str, Any]) -> Optional[str]:
        """Get staleness warning for memory."""
        age_days = self._calculate_age(memory.get("created_at"))
        
        if age_days is None:
            return None
        
        if age_days >= self.STALE_WARNING_DAYS:
            return f"这条记忆已经有 {age_days} 天了。记忆是某个时间点的观察，不是实时状态——在当作事实引用之前，请先对照当前代码验证。"
        
        return None
    
    def clear_surfaced(self):
        """Clear already surfaced memories."""
        self.already_surfaced.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get selector statistics."""
        return {
            "surfaced_count": len(self.already_surfaced),
            "stale_threshold_days": self.STALE_WARNING_DAYS
        }
