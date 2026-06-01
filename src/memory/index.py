"""SQLite index for fast memory retrieval."""

import sqlite3
import logging
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class MemoryIndex:
    """
    SQLite-based memory index.
    
    Features:
    - Full-text search (FTS5)
    - User filtering
    - Importance sorting
    - Fast retrieval
    """
    
    def __init__(self, db_path: str = "memories/index.db"):
        """
        Initialize index.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            # 主表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    memory_id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    user_id TEXT,
                    importance REAL DEFAULT 0.5,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 全文搜索索引
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts 
                USING fts5(memory_id, content, memory_type, user_id)
            """)
            
            # 索引
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_id 
                ON memories(user_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memory_type 
                ON memories(memory_type)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_importance 
                ON memories(importance)
            """)
            
            conn.commit()
    
    def add(
        self,
        memory_id: str,
        content: str,
        memory_type: str,
        user_id: str = None,
        importance: float = 0.5
    ):
        """
        Add memory to index.
        
        Args:
            memory_id: Unique memory identifier
            content: Memory content
            memory_type: Type of memory
            user_id: User identifier
            importance: Importance score (0-1)
        """
        with sqlite3.connect(self.db_path) as conn:
            # 插入主表
            conn.execute("""
                INSERT OR REPLACE INTO memories 
                (memory_id, content, memory_type, user_id, importance)
                VALUES (?, ?, ?, ?, ?)
            """, (memory_id, content, memory_type, user_id, importance))
            
            # 插入全文搜索表
            conn.execute("""
                INSERT OR REPLACE INTO memories_fts 
                (memory_id, content, memory_type, user_id)
                VALUES (?, ?, ?, ?)
            """, (memory_id, content, memory_type, user_id))
            
            conn.commit()
        
        logger.info(f"Added to index: {memory_id}")
    
    def search(
        self,
        query: str,
        user_id: str = None,
        memory_type: str = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Search memories.
        
        Args:
            query: Search query
            user_id: Filter by user
            memory_type: Filter by type
            limit: Maximum results
            
        Returns:
            List of matching memories
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # 构建查询
            if query:
                # 使用 LIKE 进行模糊搜索（FTS5 中文支持不好）
                sql = """
                    SELECT * FROM memories 
                    WHERE content LIKE ?
                """
                params = [f"%{query}%"]
            else:
                sql = "SELECT * FROM memories WHERE 1=1"
                params = []
            
            # 添加过滤条件
            if user_id:
                sql += " AND memories.user_id = ?"
                params.append(user_id)
            
            if memory_type:
                sql += " AND memory_type = ?"
                params.append(memory_type)
            
            # 排序和限制
            sql += " ORDER BY importance DESC, updated_at DESC LIMIT ?"
            params.append(limit)
            
            cursor = conn.execute(sql, params)
            results = [dict(row) for row in cursor.fetchall()]
            
            return results
    
    def delete(self, memory_id: str):
        """
        Delete memory from index.
        
        Args:
            memory_id: Memory identifier
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM memories WHERE memory_id = ?", (memory_id,))
            conn.execute("DELETE FROM memories_fts WHERE memory_id = ?", (memory_id,))
            conn.commit()
        
        logger.info(f"Deleted from index: {memory_id}")
    
    def get_stats(self) -> Dict:
        """
        Get index statistics.
        
        Returns:
            Statistics dictionary
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM memories")
            total = cursor.fetchone()[0]
            
            cursor = conn.execute("""
                SELECT memory_type, COUNT(*) 
                FROM memories 
                GROUP BY memory_type
            """)
            by_type = dict(cursor.fetchall())
            
            cursor = conn.execute("""
                SELECT user_id, COUNT(*) 
                FROM memories 
                GROUP BY user_id
            """)
            by_user = dict(cursor.fetchall())
            
            return {
                "total": total,
                "by_type": by_type,
                "by_user": by_user
            }
