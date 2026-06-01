"""Memory summarizer for hierarchical compression."""

from typing import List, Dict
from collections import defaultdict


class MemorySummarizer:
    """
    Create hierarchical summaries of memories.
    
    Inspired by Memory Tree:
    - Group by type
    - Summarize each group
    - Create hierarchy
    """
    
    def summarize(self, memories: List[Dict]) -> str:
        """
        Create summary from memories.
        
        Args:
            memories: List of memory dicts
            
        Returns:
            Summary text
        """
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
    
    def create_hierarchy(self, memories: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Create hierarchical structure from memories.
        
        Args:
            memories: List of memory dicts
            
        Returns:
            Hierarchy dict grouped by type
        """
        hierarchy = defaultdict(list)
        
        for mem in memories:
            memory_type = mem.get("type", "unknown")
            hierarchy[memory_type].append(mem)
        
        return dict(hierarchy)
    
    def fold_memories(
        self,
        memories: List[Dict],
        max_per_group: int = 10
    ) -> Dict[str, str]:
        """
        Fold memories into summaries per group.
        
        Args:
            memories: List of memory dicts
            max_per_group: Maximum memories per group before folding
            
        Returns:
            Dict of type -> summary
        """
        hierarchy = self.create_hierarchy(memories)
        
        folded = {}
        for memory_type, group_memories in hierarchy.items():
            if len(group_memories) > max_per_group:
                # 折叠：创建摘要
                folded[memory_type] = self.summarize(group_memories)
            else:
                # 保留原始内容
                folded[memory_type] = "\n".join(
                    m.get("content", "") for m in group_memories
                )
        
        return folded
