# MemoryAgent 记忆系统升级实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 升级记忆系统，实现分块存储、重要性评分、层级摘要、SQLite 索引、Obsidian 兼容格式

**Architecture:** 在现有文件存储基础上，添加 SQLite 索引层、分块器、评分器、摘要生成器，保持 Markdown 文件作为用户可见的存储格式

**Tech Stack:** Python, SQLite, Markdown, YAML

---

## 问题分析

1. **记忆内容质量差** - 只有描述，没有完整对话内容
2. **没有分块** - 长内容会丢失
3. **没有重要性评分** - 无法区分记忆重要程度
4. **没有层级摘要** - 旧记忆不会被压缩
5. **没有 SQLite 索引** - 查询效率低
6. **不是 Obsidian 兼容** - 用户无法直接编辑

---

## Task 1: 添加记忆分块器

**Files:**
- Create: `src/memory/chunker.py`
- Test: `tests/test_chunker.py`

- [ ] **Step 1: 写一个失败的测试**

```python
"""Test memory chunker."""
import pytest
from src.memory.chunker import MemoryChunker


def test_chunker_splits_long_content():
    """分块器应该将长内容分割成小块。"""
    chunker = MemoryChunker(max_tokens=100)
    
    content = "这是一段很长的内容。" * 50  # 约500字
    
    chunks = chunker.chunk(content)
    
    # 应该分成多个块
    assert len(chunks) > 1
    
    # 每个块应该不超过100 tokens（约150字）
    for chunk in chunks:
        assert len(chunk) <= 150


def test_chunker_preserves_sentences():
    """分块器应该在句子边界分割。"""
    chunker = MemoryChunker(max_tokens=50)
    
    content = "第一句话。第二句话。第三句话。第四句话。第五句话。"
    
    chunks = chunker.chunk(content)
    
    # 每个块应该以句号结尾
    for chunk in chunks[:-1]:
        assert chunk.endswith("。")


def test_chunker_handles_short_content():
    """分块器应该正确处理短内容。"""
    chunker = MemoryChunker(max_tokens=100)
    
    content = "这是一段短内容。"
    
    chunks = chunker.chunk(content)
    
    # 短内容应该只有一个块
    assert len(chunks) == 1
    assert chunks[0] == content
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd /Users/tmind/Desktop/work/github/test2
source venv/bin/activate
python -m pytest tests/test_chunker.py -v
```

Expected: FAIL - module not found

- [ ] **Step 3: 实现分块器**

```python
# src/memory/chunker.py
"""Memory chunker for splitting long content into manageable pieces."""

import re
from typing import List


class MemoryChunker:
    """
    Split memory content into chunks.
    
    Inspired by Memory Tree's approach:
    - Normalize data into ~3k token chunks
    - Preserve sentence boundaries
    - Maintain context between chunks
    """
    
    def __init__(self, max_tokens: int = 3000):
        """
        Initialize chunker.
        
        Args:
            max_tokens: Maximum tokens per chunk (approximate)
        """
        self.max_chars = max_tokens * 2  # 粗略估计：1 token ≈ 2 字符
    
    def chunk(self, content: str) -> List[str]:
        """
        Split content into chunks.
        
        Args:
            content: Content to split
            
        Returns:
            List of content chunks
        """
        if len(content) <= self.max_chars:
            return [content]
        
        chunks = []
        current_chunk = ""
        
        # 按句子分割
        sentences = re.split(r'([。！？.!?])', content)
        
        for i in range(0, len(sentences), 2):
            sentence = sentences[i]
            # 加上标点符号
            if i + 1 < len(sentences):
                sentence += sentences[i + 1]
            
            # 检查是否超过限制
            if len(current_chunk) + len(sentence) > self.max_chars:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence
            else:
                current_chunk += sentence
        
        # 添加最后一个块
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
```

- [ ] **Step 4: 运行测试验证通过**

```bash
python -m pytest tests/test_chunker.py -v
```

Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/memory/chunker.py tests/test_chunker.py
git commit -m "feat: 添加记忆分块器"
```

---

## Task 2: 添加重要性评分器

**Files:**
- Create: `src/memory/scorer.py`
- Test: `tests/test_scorer.py`

- [ ] **Step 1: 写一个失败的测试**

```python
"""Test memory scorer."""
import pytest
from src.memory.scorer import MemoryScorer


def test_scorer_scores_user_preferences():
    """评分器应该给用户偏好高分。"""
    scorer = MemoryScorer()
    
    content = "我喜欢Python，讨厌Java"
    memory_type = "user"
    
    score = scorer.score(content, memory_type)
    
    # 用户偏好应该有较高分数
    assert score >= 0.7


def test_scorer_scores_feedback():
    """评分器应该给行为反馈高分。"""
    scorer = MemoryScorer()
    
    content = "不要用mock数据库"
    memory_type = "feedback"
    
    score = scorer.score(content, memory_type)
    
    # 行为反馈应该有较高分数
    assert score >= 0.7


def test_scorer_scores_low_for_noise():
    """评分器应该给噪音内容低分。"""
    scorer = MemoryScorer()
    
    content = "嗯"
    memory_type = "user"
    
    score = scorer.score(content, memory_type)
    
    # 噪音应该有低分
    assert score < 0.3
```

- [ ] **Step 2: 运行测试确认失败**

```bash
python -m pytest tests/test_scorer.py -v
```

Expected: FAIL - module not found

- [ ] **Step 3: 实现评分器**

```python
# src/memory/scorer.py
"""Memory scorer for evaluating importance."""

import re
from typing import Dict


class MemoryScorer:
    """
    Score memory importance.
    
    Scoring factors:
    - Content length (longer = more important)
    - Keyword presence (preference words, action words)
    - Memory type (feedback > user > project > reference)
    - Specificity (specific > vague)
    """
    
    # 类型权重
    TYPE_WEIGHTS = {
        "feedback": 0.9,  # 行为反馈最重要
        "user": 0.8,      # 用户偏好次之
        "project": 0.7,   # 项目动态
        "reference": 0.6  # 外部引用
    }
    
    # 关键词权重
    KEYWORD_WEIGHTS = {
        # 偏好词
        "喜欢": 0.1, "讨厌": 0.1, "偏好": 0.1, "习惯": 0.1,
        # 行为词
        "不要": 0.15, "必须": 0.15, "应该": 0.1, "避免": 0.15,
        # 时间词
        "截止": 0.1, "deadline": 0.1, "紧急": 0.15,
        # 重要词
        "重要": 0.1, "关键": 0.1, "核心": 0.1
    }
    
    def score(self, content: str, memory_type: str) -> float:
        """
        Score memory importance.
        
        Args:
            content: Memory content
            memory_type: Type of memory
            
        Returns:
            Score between 0 and 1
        """
        score = 0.0
        
        # 1. 类型基础分
        score += self.TYPE_WEIGHTS.get(memory_type, 0.5) * 0.3
        
        # 2. 内容长度分（对数缩放）
        length_score = min(1.0, len(content) / 100)  # 100字满分
        score += length_score * 0.2
        
        # 3. 关键词分
        keyword_score = 0.0
        for keyword, weight in self.KEYWORD_WEIGHTS.items():
            if keyword in content:
                keyword_score += weight
        keyword_score = min(1.0, keyword_score)
        score += keyword_score * 0.3
        
        # 4. 具体性分（包含数字、专有名词等）
        specificity_score = 0.0
        if re.search(r'\d+', content):  # 包含数字
            specificity_score += 0.3
        if re.search(r'[A-Z][a-z]+', content):  # 包含专有名词
            specificity_score += 0.3
        if len(content) > 20:  # 足够详细
            specificity_score += 0.4
        specificity_score = min(1.0, specificity_score)
        score += specificity_score * 0.2
        
        return min(1.0, score)
```

- [ ] **Step 4: 运行测试验证通过**

```bash
python -m pytest tests/test_scorer.py -v
```

Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/memory/scorer.py tests/test_scorer.py
git commit -m "feat: 添加重要性评分器"
```

---

## Task 3: 添加 SQLite 索引

**Files:**
- Create: `src/memory/index.py`
- Test: `tests/test_index.py`

- [ ] **Step 1: 写一个失败的测试**

```python
"""Test memory index."""
import pytest
import tempfile
import os
from src.memory.index import MemoryIndex


def test_index_stores_and_retrieves():
    """索引应该能存储和检索记忆。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        index = MemoryIndex(os.path.join(tmpdir, "test.db"))
        
        # 存储记忆
        index.add(
            memory_id="test_1",
            content="用户喜欢Python",
            memory_type="user",
            user_id="user1",
            importance=0.8
        )
        
        # 检索记忆
        results = index.search("Python", user_id="user1")
        
        assert len(results) == 1
        assert results[0]["memory_id"] == "test_1"


def test_index_filters_by_user():
    """索引应该按用户过滤。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        index = MemoryIndex(os.path.join(tmpdir, "test.db"))
        
        # 存储两个用户的记忆
        index.add("test_1", "用户A喜欢Python", "user", "user_a", 0.8)
        index.add("test_2", "用户B喜欢Java", "user", "user_b", 0.8)
        
        # 搜索 user_a 的记忆
        results = index.search("喜欢", user_id="user_a")
        
        assert len(results) == 1
        assert results[0]["memory_id"] == "test_1"


def test_index_full_text_search():
    """索引应该支持全文搜索。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        index = MemoryIndex(os.path.join(tmpdir, "test.db"))
        
        # 存储记忆
        index.add("test_1", "用户喜欢Python编程语言", "user", "user1", 0.8)
        index.add("test_2", "用户讨厌Java", "user", "user1", 0.8)
        
        # 全文搜索
        results = index.search("Python 编程")
        
        assert len(results) >= 1
        assert any("Python" in r["content"] for r in results)
```

- [ ] **Step 2: 运行测试确认失败**

```bash
python -m pytest tests/test_index.py -v
```

Expected: FAIL - module not found

- [ ] **Step 3: 实现 SQLite 索引**

```python
# src/memory/index.py
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
                # 全文搜索
                sql = """
                    SELECT m.* FROM memories m
                    JOIN memories_fts fts ON m.memory_id = fts.memory_id
                    WHERE memories_fts MATCH ?
                """
                params = [query]
            else:
                sql = "SELECT * FROM memories WHERE 1=1"
                params = []
            
            # 添加过滤条件
            if user_id:
                sql += " AND user_id = ?"
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
```

- [ ] **Step 4: 运行测试验证通过**

```bash
python -m pytest tests/test_index.py -v
```

Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/memory/index.py tests/test_index.py
git commit -m "feat: 添加 SQLite 索引"
```

---

## Task 4: 添加层级摘要生成器

**Files:**
- Create: `src/memory/summarizer.py`
- Test: `tests/test_summarizer.py`

- [ ] **Step 1: 写一个失败的测试**

```python
"""Test memory summarizer."""
import pytest
from src.memory.summarizer import MemorySummarizer


def test_summarizer_creates_summary():
    """摘要生成器应该能创建摘要。"""
    summarizer = MemorySummarizer()
    
    memories = [
        {"content": "用户喜欢Python", "importance": 0.8},
        {"content": "用户讨厌Java", "importance": 0.7},
        {"content": "用户偏好简洁语法", "importance": 0.6}
    ]
    
    summary = summarizer.summarize(memories)
    
    # 摘要应该包含关键信息
    assert "Python" in summary
    assert len(summary) < sum(len(m["content"]) for m in memories)


def test_summarizer_creates_hierarchy():
    """摘要生成器应该能创建层级结构。"""
    summarizer = MemorySummarizer()
    
    memories = [
        {"content": "用户喜欢Python", "type": "user", "importance": 0.8},
        {"content": "用户讨厌Java", "type": "user", "importance": 0.7},
        {"content": "不要用mock数据库", "type": "feedback", "importance": 0.9}
    ]
    
    hierarchy = summarizer.create_hierarchy(memories)
    
    # 应该按类型分组
    assert "user" in hierarchy
    assert "feedback" in hierarchy
    assert len(hierarchy["user"]) == 2
    assert len(hierarchy["feedback"]) == 1
```

- [ ] **Step 2: 运行测试确认失败**

```bash
python -m pytest tests/test_summarizer.py -v
```

Expected: FAIL - module not found

- [ ] **Step 3: 实现摘要生成器**

```python
# src/memory/summarizer.py
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
```

- [ ] **Step 4: 运行测试验证通过**

```bash
python -m pytest tests/test_summarizer.py -v
```

Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/memory/summarizer.py tests/test_summarizer.py
git commit -m "feat: 添加层级摘要生成器"
```

---

## Task 5: 升级记忆存储，集成所有组件

**Files:**
- Modify: `src/memory/storage.py`
- Modify: `src/memory/types/__init__.py`
- Test: `tests/test_storage_upgrade.py`

- [ ] **Step 1: 写一个失败的测试**

```python
"""Test storage upgrade."""
import pytest
import tempfile
import os
from src.memory.storage import MemoryStorage
from src.memory.types import MemoryItem, MemoryType


def test_storage_saves_chunks():
    """存储应该保存分块内容。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = MemoryStorage(tmpdir)
        
        # 创建长内容记忆
        content = "这是一段很长的内容。" * 100
        
        memory = MemoryItem.create(
            memory_type=MemoryType.USER,
            content=content,
            description="长内容测试"
        )
        
        # 存储
        import asyncio
        asyncio.run(storage.store(memory))
        
        # 验证文件存在
        files = list(Path(tmpdir).rglob("*.md"))
        assert len(files) > 0


def test_storage_saves_importance_score():
    """存储应该保存重要性评分。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = MemoryStorage(tmpdir)
        
        memory = MemoryItem.create(
            memory_type=MemoryType.USER,
            content="用户喜欢Python",
            description="用户偏好",
            metadata={"importance": 0.8}
        )
        
        # 存储
        import asyncio
        asyncio.run(storage.store(memory))
        
        # 读取文件
        files = list(Path(tmpdir).rglob("*.md"))
        if files:
            content = files[0].read_text()
            assert "importance: 0.8" in content
```

- [ ] **Step 2: 运行测试确认失败**

```bash
python -m pytest tests/test_storage_upgrade.py -v
```

Expected: FAIL

- [ ] **Step 3: 升级存储系统**

```python
# src/memory/storage.py
# 在文件开头添加导入
from src.memory.chunker import MemoryChunker
from src.memory.scorer import MemoryScorer
from src.memory.index import MemoryIndex

# 在 __init__ 方法中初始化组件
def __init__(self, base_dir: str = "memories"):
    self.base_dir = Path(base_dir)
    self._ensure_dirs()
    
    # 初始化组件
    self.chunker = MemoryChunker(max_tokens=3000)
    self.scorer = MemoryScorer()
    self.index = MemoryIndex(str(self.base_dir / "index.db"))

# 修改 store 方法
async def store(self, memory: MemoryItem) -> bool:
    """Store a memory with chunking and scoring."""
    try:
        # 1. 评分
        importance = self.scorer.score(memory.content, memory.type.value)
        memory.metadata["importance"] = importance
        
        # 2. 分块（如果内容很长）
        chunks = self.chunker.chunk(memory.content)
        
        if len(chunks) == 1:
            # 单块：直接存储
            file_path = self.base_dir / memory.type.value / f"{memory.id}.md"
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(memory.to_markdown(), encoding="utf-8")
            
            # 添加到索引
            self.index.add(
                memory_id=memory.id,
                content=memory.content,
                memory_type=memory.type.value,
                user_id=memory.metadata.get("user_id"),
                importance=importance
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
                
                file_path = self.base_dir / memory.type.value / f"{chunk_id}.md"
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(chunk_memory.to_markdown(), encoding="utf-8")
                
                # 添加到索引
                self.index.add(
                    memory_id=chunk_id,
                    content=chunk,
                    memory_type=memory.type.value,
                    user_id=memory.metadata.get("user_id"),
                    importance=importance
                )
        
        # 更新索引文件
        await self._update_index(memory)
        
        logger.info(f"Stored memory: {memory.id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to store memory: {e}")
        return False
```

- [ ] **Step 4: 运行测试验证通过**

```bash
python -m pytest tests/test_storage_upgrade.py -v
```

Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/memory/storage.py tests/test_storage_upgrade.py
git commit -m "feat: 升级存储系统，集成分块、评分、索引"
```

---

## Task 6: 升级检索系统，使用 SQLite 索引

**Files:**
- Modify: `src/memory/retrieval.py`
- Test: `tests/test_retrieval_upgrade.py`

- [ ] **Step 1: 写一个失败的测试**

```python
"""Test retrieval upgrade."""
import pytest
import tempfile
import os
from src.memory.storage import MemoryStorage
from src.memory.retrieval import MemoryRetrieval
from src.memory.types import MemoryItem, MemoryType


def test_retrieval_uses_index():
    """检索应该使用 SQLite 索引。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = MemoryStorage(tmpdir)
        retrieval = MemoryRetrieval(storage)
        
        # 存储记忆
        memory = MemoryItem.create(
            memory_type=MemoryType.USER,
            content="用户喜欢Python",
            description="用户偏好"
        )
        
        import asyncio
        asyncio.run(storage.store(memory))
        
        # 检索
        results = asyncio.run(retrieval.retrieve("Python", user_id="user1"))
        
        assert len(results) > 0


def test_retrieval_filters_by_user():
    """检索应该按用户过滤。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = MemoryStorage(tmpdir)
        retrieval = MemoryRetrieval(storage)
        
        # 存储两个用户的记忆
        mem1 = MemoryItem.create(
            memory_type=MemoryType.USER,
            content="用户A喜欢Python",
            description="用户A偏好",
            metadata={"user_id": "user_a"}
        )
        mem2 = MemoryItem.create(
            memory_type=MemoryType.USER,
            content="用户B喜欢Java",
            description="用户B偏好",
            metadata={"user_id": "user_b"}
        )
        
        import asyncio
        asyncio.run(storage.store(mem1))
        asyncio.run(storage.store(mem2))
        
        # 检索 user_a 的记忆
        results = asyncio.run(retrieval.retrieve("喜欢", user_id="user_a"))
        
        # 应该只返回 user_a 的记忆
        for result in results:
            assert "用户A" in result.get("content", "")
```

- [ ] **Step 2: 运行测试确认失败**

```bash
python -m pytest tests/test_retrieval_upgrade.py -v
```

Expected: FAIL

- [ ] **Step 3: 升级检索系统**

```python
# src/memory/retrieval.py
# 在 __init__ 方法中初始化索引
def __init__(self, storage: MemoryStorage, llm_service=None):
    self.storage = storage
    self.llm = llm_service
    self.index = storage.index  # 使用存储系统的索引

# 修改 retrieve 方法
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
    results = self.index.search(
        query=query,
        user_id=user_id,
        limit=limit
    )
    
    # 添加过时警告
    for result in results:
        created_at = result.get("created_at")
        if created_at:
            from datetime import datetime
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
    
    return results
```

- [ ] **Step 4: 运行测试验证通过**

```bash
python -m pytest tests/test_retrieval_upgrade.py -v
```

Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/memory/retrieval.py tests/test_retrieval_upgrade.py
git commit -m "feat: 升级检索系统，使用 SQLite 索引"
```

---

## Task 7: 添加 Obsidian 兼容格式

**Files:**
- Modify: `src/memory/types/__init__.py`
- Test: `tests/test_obsidian_compat.py`

- [ ] **Step 1: 写一个失败的测试**

```python
"""Test Obsidian compatibility."""
import pytest
from src.memory.types import MemoryItem, MemoryType


def test_memory_creates_obsidian_links():
    """记忆应该创建 Obsidian 双向链接。"""
    memory = MemoryItem.create(
        memory_type=MemoryType.USER,
        content="用户喜欢Python，参考[[编程语言]]",
        description="用户偏好",
        metadata={"tags": ["preference", "python"]}
    )
    
    md = memory.to_markdown()
    
    # 应该包含 Obsidian 格式
    assert "[[编程语言]]" in md
    assert "#preference" in md
    assert "#python" in md


def test_memory_preserves_yaml_frontmatter():
    """记忆应该保留 YAML frontmatter。"""
    memory = MemoryItem.create(
        memory_type=MemoryType.USER,
        content="用户喜欢Python",
        description="用户偏好",
        metadata={"tags": ["preference"], "aliases": ["用户偏好"]}
    )
    
    md = memory.to_markdown()
    
    # 应该包含标准 YAML frontmatter
    assert "---" in md
    assert "tags:" in md
    assert "aliases:" in md
```

- [ ] **Step 2: 运行测试确认失败**

```bash
python -m pytest tests/test_obsidian_compat.py -v
```

Expected: FAIL

- [ ] **Step 3: 升级 Markdown 格式**

```python
# src/memory/types/__init__.py
# 修改 to_markdown 方法
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
    
    # 添加 tags
    if self.metadata.get("tags"):
        lines.append("tags:")
        for tag in self.metadata["tags"]:
            lines.append(f"  - {tag}")
    
    # 添加 aliases
    if self.metadata.get("aliases"):
        lines.append("aliases:")
        for alias in self.metadata["aliases"]:
            lines.append(f"  - {alias}")
    
    # 添加其他 metadata
    for key, value in self.metadata.items():
        if key not in ["tags", "aliases", "user_id", "importance", "source"]:
            lines.append(f"{key}: {value}")
    
    lines.append("---")
    lines.append("")
    
    # 添加 tags 作为 hashtags
    if self.metadata.get("tags"):
        for tag in self.metadata["tags"]:
            lines.append(f"#{tag}")
        lines.append("")
    
    # 添加内容
    lines.append(self.content)
    
    return "\n".join(lines)
```

- [ ] **Step 4: 运行测试验证通过**

```bash
python -m pytest tests/test_obsidian_compat.py -v
```

Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/memory/types/__init__.py tests/test_obsidian_compat.py
git commit -m "feat: 添加 Obsidian 兼容格式"
```

---

## 最终验证

完成所有任务后，运行所有测试：

```bash
cd /Users/tmind/Desktop/work/github/test2
source venv/bin/activate
python -m pytest tests/ -v --ignore=tests/test_integration.py --ignore=tests/test_quick_integration.py
```

---

## 总结

这个实现计划解决了 MemoryAgent 记忆系统的 6 个问题：

1. ✅ **分块器** - 将长内容分割成小块
2. ✅ **评分器** - 评估记忆重要性
3. ✅ **SQLite 索引** - 快速查询和全文搜索
4. ✅ **层级摘要** - 压缩旧记忆
5. ✅ **存储升级** - 集成所有组件
6. ✅ **检索升级** - 使用 SQLite 索引
7. ✅ **Obsidian 兼容** - 用户可编辑、双向链接

每个任务都包含：
- 详细的代码实现
- 测试验证步骤
- 提交命令
