"""MEMORY.md index system - lightweight index always loaded in system prompt."""

import logging
import hashlib
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# 索引限制（参考 Claude Code）
MAX_INDEX_LINES = 200
MAX_INDEX_BYTES = 25_000  # 25KB


class MemoryIndex:
    """MEMORY.md index - always loaded in system prompt."""
    
    def __init__(self, storage_dir: str = "memories"):
        self.storage_dir = Path(storage_dir)
        self.index_path = self.storage_dir / "MEMORY.md"
        self.entries: List[Dict[str, Any]] = []
    
    def build_index(self, memories: List[Dict[str, Any]]) -> str:
        """Build MEMORY.md index from memories."""
        self.entries = []
        
        for memory in memories:
            entry = {
                "id": memory.get("id", ""),
                "name": memory.get("id", ""),
                "description": memory.get("description", "")[:100],
                "type": memory.get("type", "unknown"),
                "age_days": self._calculate_age(memory.get("created_at")),
                "file_path": self._get_file_path(memory)
            }
            self.entries.append(entry)
        
        # 生成索引内容
        index_content = self._format_index()
        
        # 截断双保险
        index_content = self._truncate_index(index_content)
        
        # 保存到文件
        self.index_path.write_text(index_content, encoding="utf-8")
        
        logger.info(f"Built MEMORY.md index: {len(self.entries)} entries")
        return index_content
    
    def _format_index(self) -> str:
        """Format index content."""
        lines = [
            "# Memory Index",
            "",
            "Available memories:",
            ""
        ]
        
        # 按类型分组
        by_type = {}
        for entry in self.entries:
            memory_type = entry["type"]
            if memory_type not in by_type:
                by_type[memory_type] = []
            by_type[memory_type].append(entry)
        
        # 格式化
        type_labels = {
            "user": "用户画像",
            "feedback": "行为偏好",
            "project": "项目动态",
            "reference": "外部引用"
        }
        
        for memory_type, entries in by_type.items():
            label = type_labels.get(memory_type, memory_type)
            lines.append(f"## {label}")
            lines.append("")
            
            for entry in entries:
                age_str = ""
                if entry["age_days"] is not None:
                    if entry["age_days"] == 0:
                        age_str = " (今天)"
                    elif entry["age_days"] == 1:
                        age_str = " (昨天)"
                    elif entry["age_days"] < 7:
                        age_str = f" ({entry['age_days']}天前)"
                    elif entry["age_days"] < 30:
                        age_str = f" ({entry['age_days'] // 7}周前)"
                    else:
                        age_str = f" ({entry['age_days']}天前)"
                
                lines.append(f"- {entry['name']}: {entry['description']}{age_str}")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def _truncate_index(self, content: str) -> str:
        """Truncate index with double safety (lines + bytes)."""
        lines = content.split("\n")
        
        # 行数限制
        if len(lines) > MAX_INDEX_LINES:
            lines = lines[:MAX_INDEX_LINES]
            lines.append("")
            lines.append("⚠️ 索引已截断，部分记忆未显示。")
        
        # 字节限制
        result = "\n".join(lines)
        if len(result.encode("utf-8")) > MAX_INDEX_BYTES:
            # 按字节截断
            result = result.encode("utf-8")[:MAX_INDEX_BYTES].decode("utf-8", errors="ignore")
            result += "\n\n⚠️ 索引已截断，部分记忆未显示。"
        
        return result
    
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
    
    def _get_file_path(self, memory: Dict[str, Any]) -> str:
        """Get file path for memory."""
        memory_type = memory.get("type", "unknown")
        memory_id = memory.get("id", "unknown")
        return f"memories/{memory_type}/{memory_id}.md"
    
    def get_index_content(self) -> str:
        """Get current index content."""
        if self.index_path.exists():
            return self.index_path.read_text(encoding="utf-8")
        return ""
    
    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        content = self.get_index_content()
        lines = content.split("\n")
        
        return {
            "total_entries": len(self.entries),
            "index_lines": len(lines),
            "index_bytes": len(content.encode("utf-8")),
            "max_lines": MAX_INDEX_LINES,
            "max_bytes": MAX_INDEX_BYTES
        }
