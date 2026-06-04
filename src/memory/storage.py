"""
Memory storage system for MemoryAI Agent.

Implements Claude Code's memory storage pattern:
- Each memory as a separate .md file
- YAML frontmatter for metadata
- MEMORY.md as lightweight index (200 line limit)
"""

import os
import logging
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime

from src.memory.types import MemoryItem, MemoryType
from src.memory.chunker import MemoryChunker
from src.memory.scorer import MemoryScorer
from src.memory.index import MemoryIndex

logger = logging.getLogger(__name__)


class MemoryStorage:
    """
    File-based memory storage system.
    
    Storage structure:
    memories/
    ├── MEMORY.md          # Index file (max 200 lines)
    ├── index.db           # SQLite index
    ├── user/
    │   └── user_preferences.md
    ├── feedback/
    │   └── no_mock_database.md
    ├── project/
    │   └── auth_rewrite.md
    └── reference/
        └── grafana_dashboard.md
    """
    
    MAX_INDEX_LINES = 200
    MAX_INDEX_BYTES = 25_000  # 25KB
    
    def __init__(self, base_dir: str = "memories"):
        self.base_dir = Path(base_dir)
        self._ensure_dirs()
        
        # 初始化组件
        self.chunker = MemoryChunker(max_tokens=3000)
        self.scorer = MemoryScorer()
        self.index = MemoryIndex(str(self.base_dir / "index.db"))
    
    def _ensure_dirs(self):
        """Ensure memory directories exist."""
        for memory_type in MemoryType:
            (self.base_dir / memory_type.value).mkdir(parents=True, exist_ok=True)
    
    async def store(self, memory: MemoryItem) -> bool:
        """
        Store a memory item with chunking and scoring.
        
        Args:
            memory: Memory item to store
            
        Returns:
            True if successful
        """
        try:
            # 1. 计算重要性评分
            importance = self.scorer.score(memory.content, memory.type.value)
            memory.metadata["importance"] = importance
            
            # 2. 分块（如果内容很长）
            chunks = self.chunker.chunk(memory.content)
            
            if len(chunks) == 1:
                # 单块：直接存储
                file_path = self._get_file_path(memory)
                file_path.write_text(memory.to_markdown(), encoding="utf-8")
                
                # 添加到索引
                self.index.add(
                    memory_id=memory.id,
                    content=memory.content,
                    memory_type=memory.type.value,
                    user_id=memory.metadata.get("user_id"),
                    importance=importance,
                    project_id=memory.metadata.get("project_id"),
                )
            else:
                # 多块：分块存储
                for i, chunk in enumerate(chunks):
                    chunk_id = f"{memory.id}_chunk_{i}"
                    chunk_memory = MemoryItem(
                        id=chunk_id,
                        type=memory.type,
                        content=chunk,
                        description=f"{memory.description} (part {i+1})",
                        metadata={**memory.metadata, "parent_id": memory.id, "chunk_index": i}
                    )
                    
                    file_path = self._get_file_path(chunk_memory)
                    file_path.write_text(chunk_memory.to_markdown(), encoding="utf-8")
                    
                    # 添加到索引
                    self.index.add(
                        memory_id=chunk_id,
                        content=chunk,
                        memory_type=memory.type.value,
                        user_id=memory.metadata.get("user_id"),
                        importance=importance,
                        project_id=memory.metadata.get("project_id"),
                    )
            
            # 更新 MEMORY.md 索引
            await self._update_index(memory)
            
            logger.info(f"Stored memory: {memory.id} (importance={importance:.2f})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            return False
    
    async def retrieve(self, memory_id: str) -> Optional[MemoryItem]:
        """
        Retrieve a memory by ID.
        
        Args:
            memory_id: Memory identifier
            
        Returns:
            MemoryItem if found, None otherwise
        """
        # Search across all type directories
        for memory_type in MemoryType:
            file_path = self.base_dir / memory_type.value / f"{memory_id}.md"
            if file_path.exists():
                content = file_path.read_text(encoding="utf-8")
                memory = MemoryItem.from_markdown(content, memory_id)
                memory.touch()
                return memory
        
        return None
    
    async def search(
        self,
        query: str = None,
        memory_type: MemoryType = None,
        user_id: str = None,
        limit: int = 10
    ) -> List[MemoryItem]:
        """
        Search memories.
        
        Args:
            query: Search query (matches description)
            memory_type: Filter by type
            user_id: Filter by user ID (for cross-session memory)
            limit: Maximum results
            
        Returns:
            List of matching MemoryItems
        """
        results = []
        
        types_to_search = [memory_type] if memory_type else list(MemoryType)
        
        for mt in types_to_search:
            type_dir = self.base_dir / mt.value
            if not type_dir.exists():
                continue
            
            for file_path in type_dir.glob("*.md"):
                try:
                    content = file_path.read_text(encoding="utf-8")
                    memory = MemoryItem.from_markdown(content, file_path.stem)
                    
                    mem_user = memory.metadata.get("user_id")
                    if user_id:
                        id_match = file_path.stem.startswith(f"{user_id}_") or file_path.stem.startswith(user_id)
                        meta_match = mem_user == user_id
                        if not (id_match or meta_match):
                            continue
                    
                    # Simple text matching
                    if query:
                        query_lower = query.lower()
                        if (query_lower in memory.description.lower() or 
                            query_lower in memory.content.lower()):
                            results.append(memory)
                    else:
                        results.append(memory)
                        
                except Exception as e:
                    logger.warning(f"Failed to parse {file_path}: {e}")
        
        # Sort by update time, most recent first
        results.sort(key=lambda m: m.updated_at, reverse=True)
        return results[:limit]
    
    async def update(
        self,
        memory_id: str,
        content: str = None,
        description: str = None,
    ) -> bool:
        memory = await self.retrieve(memory_id)
        if not memory:
            return False
        if content is not None:
            memory.content = content
        if description is not None:
            memory.description = description
        memory.touch()
        file_path = self._get_file_path(memory)
        file_path.write_text(memory.to_markdown(), encoding="utf-8")
        importance = self.scorer.score(memory.content, memory.type.value)
        self.index.add(
            memory_id=memory.id,
            content=memory.content,
            memory_type=memory.type.value,
            user_id=memory.metadata.get("user_id"),
            importance=importance,
            project_id=memory.metadata.get("project_id"),
        )
        return True

    async def delete(self, memory_id: str) -> bool:
        """
        Delete a memory.
        
        Args:
            memory_id: Memory identifier
            
        Returns:
            True if deleted
        """
        for memory_type in MemoryType:
            file_path = self.base_dir / memory_type.value / f"{memory_id}.md"
            if file_path.exists():
                file_path.unlink()
                self.index.delete(memory_id)
                await self._remove_from_index(memory_id)
                logger.info(f"Deleted memory: {memory_id}")
                return True
        
        return False
    
    async def get_index(self) -> str:
        """
        Get the memory index content.
        
        Returns:
            MEMORY.md content
        """
        index_path = self.base_dir / "MEMORY.md"
        if index_path.exists():
            return index_path.read_text(encoding="utf-8")
        return ""
    
    async def _update_index(self, memory: MemoryItem):
        """Update the MEMORY.md index file."""
        index_path = self.base_dir / "MEMORY.md"
        
        # Read existing index
        existing = ""
        if index_path.exists():
            existing = index_path.read_text(encoding="utf-8")
        
        # Add new entry
        entry = f"- [{memory.description}]({memory.type.value}/{memory.id}.md) — {memory.type.value}"
        
        if entry not in existing:
            new_index = existing.rstrip() + "\n" + entry + "\n"
            
            # Check limits
            lines = new_index.split("\n")
            if len(lines) > self.MAX_INDEX_LINES:
                # Truncate from beginning
                lines = lines[-self.MAX_INDEX_LINES:]
                new_index = "\n".join(lines)
            
            index_path.write_text(new_index, encoding="utf-8")
    
    async def _remove_from_index(self, memory_id: str):
        """Remove a memory from the index."""
        index_path = self.base_dir / "MEMORY.md"
        if not index_path.exists():
            return
        
        content = index_path.read_text(encoding="utf-8")
        lines = content.split("\n")
        
        # Filter out the memory entry
        new_lines = [line for line in lines if memory_id not in line]
        
        index_path.write_text("\n".join(new_lines), encoding="utf-8")
    
    def _get_file_path(self, memory: MemoryItem) -> Path:
        """Get file path for a memory."""
        return self.base_dir / memory.type.value / f"{memory.id}.md"
    
    async def get_stats(self) -> Dict[str, int]:
        """Get storage statistics."""
        stats = {"total": 0}
        
        for memory_type in MemoryType:
            type_dir = self.base_dir / memory_type.value
            if type_dir.exists():
                count = len(list(type_dir.glob("*.md")))
                stats[memory_type.value] = count
                stats["total"] += count
            else:
                stats[memory_type.value] = 0
        
        return stats
