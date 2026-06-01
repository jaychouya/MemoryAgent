"""Memory folder for Dreaming state - hierarchical memory folding."""

import logging
from typing import Dict, List, Any
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


class MemoryFolder:
    """Memory folder for hierarchical folding (Dreaming state)."""
    
    def __init__(self, max_per_group: int = 10):
        self.max_per_group = max_per_group
        self.memories: List[Dict[str, Any]] = []
    
    def add_memory(self, memory: Dict[str, Any]):
        """Add a memory to the folder."""
        self.memories.append(memory)
    
    def get_hierarchy(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get memories grouped by type."""
        hierarchy = defaultdict(list)
        for memory in self.memories:
            memory_type = memory.get("type", "unknown")
            hierarchy[memory_type].append(memory)
        return dict(hierarchy)
    
    def _summarize_group(self, memories: List[Dict[str, Any]]) -> str:
        """Summarize a group of memories."""
        if not memories:
            return ""
        
        # 提取关键信息
        key_points = []
        for mem in memories:
            content = mem.get("content", "")
            # 提取核心内容（去除冗余）
            if len(content) > 50:
                content = content[:50] + "..."
            key_points.append(content)
        
        # 合并关键点
        summary = "；".join(key_points)
        return summary
    
    def _sort_by_importance(self, memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort memories by importance (descending)."""
        return sorted(memories, key=lambda m: m.get("importance", 0), reverse=True)
    
    def fold(self) -> Dict[str, List[Dict[str, Any]]]:
        """Fold memories - keep important ones, summarize the rest."""
        hierarchy = self.get_hierarchy()
        folded = {}
        
        for memory_type, memories in hierarchy.items():
            if len(memories) <= self.max_per_group:
                # 数量少，保留所有
                folded[memory_type] = memories
            else:
                # 数量多，折叠
                sorted_memories = self._sort_by_importance(memories)
                
                # 保留最重要的
                important = sorted_memories[:self.max_per_group]
                
                # 摘要其余的
                rest = sorted_memories[self.max_per_group:]
                if rest:
                    summary_content = self._summarize_group(rest)
                    summary_memory = {
                        "id": f"summary_{memory_type}_{datetime.now().timestamp()}",
                        "type": memory_type,
                        "content": summary_content,
                        "importance": 0.5,
                        "is_summary": True,
                        "summarized_count": len(rest)
                    }
                    important.append(summary_memory)
                
                folded[memory_type] = important
        
        return folded
    
    def get_summary(self) -> str:
        """Get overall summary of all memories."""
        hierarchy = self.get_hierarchy()
        summaries = []
        
        for memory_type, memories in hierarchy.items():
            if memories:
                summary = self._summarize_group(memories)
                summaries.append(f"[{memory_type}] {summary}")
        
        return "\n".join(summaries)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get folder statistics."""
        hierarchy = self.get_hierarchy()
        
        return {
            "total": len(self.memories),
            "by_type": {k: len(v) for k, v in hierarchy.items()},
            "max_per_group": self.max_per_group
        }
