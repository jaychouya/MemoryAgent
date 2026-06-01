"""
Memory types for MemoryAI Agent.

Inspired by Claude Code's four-type memory classification:
- user: User profile, preferences, knowledge level
- feedback: Behavioral feedback, what to do/not do
- project: Project dynamics, deadlines, decisions
- reference: External pointers, where to find information
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
import hashlib


class MemoryType(str, Enum):
    """
    Four types of memory.
    
    Each type serves a specific purpose:
    - USER: Who the user is, their preferences
    - FEEDBACK: Behavioral rules, do's and don'ts
    - PROJECT: What's happening, deadlines, decisions
    - REFERENCE: Where to find external information
    """
    USER = "user"
    FEEDBACK = "feedback"
    PROJECT = "project"
    REFERENCE = "reference"


@dataclass
class MemoryItem:
    """
    A single memory item.
    
    Each memory has:
    - id: Unique identifier
    - type: One of the four memory types
    - content: The actual memory content
    - description: One-line summary for retrieval
    - metadata: Additional information
    - created_at: Creation timestamp
    - updated_at: Last update timestamp
    - access_count: How many times this memory was accessed
    """
    id: str
    type: MemoryType
    content: str
    description: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    
    @classmethod
    def create(
        cls,
        memory_type: MemoryType,
        content: str,
        description: str = None,
        metadata: Dict[str, Any] = None
    ) -> "MemoryItem":
        """Create a new memory item with auto-generated ID."""
        # Generate ID from content hash
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        
        # 如果有 user_id，将其包含在 memory_id 中
        user_id = (metadata or {}).get("user_id")
        if user_id:
            memory_id = f"{user_id}_{memory_type.value}_{content_hash}"
        else:
            memory_id = f"{memory_type.value}_{content_hash}"
        
        return cls(
            id=memory_id,
            type=memory_type,
            content=content,
            description=description or content[:50],
            metadata=metadata or {}
        )
    
    def to_markdown(self) -> str:
        """Convert memory to markdown format for storage (Obsidian compatible)."""
        lines = [
            "---",
            f"name: {self.id}",
            f"description: {self.description}",
            f"type: {self.type.value}",
            f"created: {self.created_at.isoformat()}",
            f"updated: {self.updated_at.isoformat()}",
        ]
        
        # 添加 tags（Obsidian YAML 列表格式）
        if self.metadata.get("tags"):
            lines.append("tags:")
            for tag in self.metadata["tags"]:
                lines.append(f"  - {tag}")
        
        # 添加 aliases（Obsidian YAML 列表格式）
        if self.metadata.get("aliases"):
            lines.append("aliases:")
            for alias in self.metadata["aliases"]:
                lines.append(f"  - {alias}")
        
        # 保存其他 metadata
        for key, value in self.metadata.items():
            if key not in ["tags", "aliases"]:
                lines.append(f"{key}: {value}")
        
        lines.append("---")
        lines.append("")
        
        # 添加 hashtags（Obsidian 格式）
        if self.metadata.get("tags"):
            for tag in self.metadata["tags"]:
                lines.append(f"#{tag}")
            lines.append("")
        
        lines.append(self.content)
        
        return "\n".join(lines)
    
    @classmethod
    def from_markdown(cls, markdown: str, memory_id: str = None) -> "MemoryItem":
        """Parse memory from markdown format."""
        lines = markdown.split("\n")
        
        # Parse frontmatter
        metadata = {}
        content_start = 0
        in_frontmatter = False
        in_metadata = False
        
        for i, line in enumerate(lines):
            if line.strip() == "---":
                if in_frontmatter:
                    content_start = i + 1
                    break
                in_frontmatter = True
                continue
            
            if in_frontmatter:
                if line.strip() == "metadata:":
                    in_metadata = True
                    continue
                
                if in_metadata and line.startswith("  "):
                    # 解析 metadata 的 key: value
                    key_value = line.strip()
                    if ":" in key_value:
                        key, value = key_value.split(":", 1)
                        metadata[key.strip()] = value.strip()
                elif ":" in line and not line.startswith("  "):
                    in_metadata = False
                    key, value = line.split(":", 1)
                    metadata[key.strip()] = value.strip()
        
        # Get content
        content = "\n".join(lines[content_start:]).strip()
        
        # 解析 metadata 中的嵌套字段
        user_metadata = {}
        for key, value in metadata.items():
            if key not in ["name", "description", "type", "created", "updated"]:
                # 尝试转换数字类型
                try:
                    if "." in value:
                        user_metadata[key] = float(value)
                    else:
                        user_metadata[key] = int(value)
                except ValueError:
                    user_metadata[key] = value
        
        return cls(
            id=memory_id or metadata.get("name", "unknown"),
            type=MemoryType(metadata.get("type", "user")),
            content=content,
            description=metadata.get("description", ""),
            metadata=user_metadata,
            created_at=datetime.fromisoformat(metadata.get("created", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(metadata.get("updated", datetime.now().isoformat()))
        )
    
    def touch(self):
        """Update access timestamp and count."""
        self.updated_at = datetime.now()
        self.access_count += 1
    
    def age_days(self) -> int:
        """Get age in days."""
        return (datetime.now() - self.updated_at).days
    
    def is_stale(self, max_days: int = 1) -> bool:
        """Check if memory is stale (older than max_days)."""
        return self.age_days() > max_days


# Memory type descriptions for prompt injection
MEMORY_TYPE_DESCRIPTIONS = {
    MemoryType.USER: "用户画像：角色、偏好、知识水平",
    MemoryType.FEEDBACK: "行为反馈：该做什么、不该做什么",
    MemoryType.PROJECT: "项目动态：在做什么、截止日期、协作信息",
    MemoryType.REFERENCE: "外部指针：哪里能找到什么信息",
}
