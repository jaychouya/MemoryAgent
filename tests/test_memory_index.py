"""Tests for MEMORY.md index system."""
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from src.memory.memory_index import MemoryIndex, MAX_INDEX_LINES, MAX_INDEX_BYTES


@pytest.fixture
def memory_index():
    """Create a temporary memory index."""
    temp_dir = tempfile.mkdtemp()
    index = MemoryIndex(storage_dir=temp_dir)
    yield index
    shutil.rmtree(temp_dir)


def test_memory_index_creates():
    """MemoryIndex 应该能创建。"""
    with tempfile.TemporaryDirectory() as temp_dir:
        index = MemoryIndex(storage_dir=temp_dir)
        assert index is not None


def test_build_index(memory_index):
    """build_index 应该构建索引。"""
    memories = [
        {
            "id": "user_1",
            "type": "user",
            "description": "用户喜欢 Python",
            "created_at": datetime.now().isoformat()
        },
        {
            "id": "feedback_1",
            "type": "feedback",
            "description": "不要用 mock 数据库",
            "created_at": (datetime.now() - timedelta(days=5)).isoformat()
        }
    ]
    
    content = memory_index.build_index(memories)
    
    assert "用户画像" in content
    assert "行为偏好" in content
    assert "用户喜欢 Python" in content
    assert "不要用 mock 数据库" in content


def test_build_index_groups_by_type(memory_index):
    """build_index 应该按类型分组。"""
    memories = [
        {"id": "u1", "type": "user", "description": "用户画像1", "created_at": datetime.now().isoformat()},
        {"id": "u2", "type": "user", "description": "用户画像2", "created_at": datetime.now().isoformat()},
        {"id": "f1", "type": "feedback", "description": "行为偏好1", "created_at": datetime.now().isoformat()},
    ]
    
    content = memory_index.build_index(memories)
    
    # 应该有类型标题
    assert "## 用户画像" in content
    assert "## 行为偏好" in content


def test_build_index_shows_age(memory_index):
    """build_index 应该显示记忆年龄。"""
    memories = [
        {"id": "u1", "type": "user", "description": "今天", "created_at": datetime.now().isoformat()},
        {"id": "u2", "type": "user", "description": "昨天", "created_at": (datetime.now() - timedelta(days=1)).isoformat()},
        {"id": "u3", "type": "user", "description": "5天前", "created_at": (datetime.now() - timedelta(days=5)).isoformat()},
    ]
    
    content = memory_index.build_index(memories)
    
    assert "(今天)" in content
    assert "(昨天)" in content
    assert "(5天前)" in content


def test_build_index_saves_file(memory_index):
    """build_index 应该保存文件。"""
    memories = [
        {"id": "u1", "type": "user", "description": "测试", "created_at": datetime.now().isoformat()}
    ]
    
    memory_index.build_index(memories)
    
    assert memory_index.index_path.exists()


def test_truncate_index_by_lines(memory_index):
    """_truncate_index 应该按行数截断。"""
    # 创建超过限制的内容
    lines = ["line " + str(i) for i in range(MAX_INDEX_LINES + 50)]
    content = "\n".join(lines)
    
    truncated = memory_index._truncate_index(content)
    
    result_lines = truncated.split("\n")
    assert len(result_lines) <= MAX_INDEX_LINES + 5  # 允许警告信息


def test_truncate_index_by_bytes(memory_index):
    """_truncate_index 应该按字节截断。"""
    # 创建超过限制的内容
    content = "x" * (MAX_INDEX_BYTES + 1000)
    
    truncated = memory_index._truncate_index(content)
    
    assert len(truncated.encode("utf-8")) <= MAX_INDEX_BYTES + 200  # 允许警告信息


def test_get_index_content(memory_index):
    """get_index_content 应该获取索引内容。"""
    memories = [
        {"id": "u1", "type": "user", "description": "测试", "created_at": datetime.now().isoformat()}
    ]
    
    memory_index.build_index(memories)
    content = memory_index.get_index_content()
    
    assert "测试" in content


def test_get_stats(memory_index):
    """get_stats 应该返回统计信息。"""
    memories = [
        {"id": "u1", "type": "user", "description": "测试", "created_at": datetime.now().isoformat()}
    ]
    
    memory_index.build_index(memories)
    stats = memory_index.get_stats()
    
    assert stats["total_entries"] == 1
    assert stats["index_lines"] > 0
    assert stats["index_bytes"] > 0
