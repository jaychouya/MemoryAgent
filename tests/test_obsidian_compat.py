"""Test Obsidian compatibility for memory storage."""
import pytest
from src.memory.types import MemoryItem, MemoryType


def test_memory_creates_yaml_frontmatter():
    """记忆应该生成标准 YAML frontmatter。"""
    memory = MemoryItem.create(
        memory_type=MemoryType.USER,
        content="用户喜欢Python",
        description="用户偏好",
        metadata={"tags": ["preference", "python"]}
    )
    
    md = memory.to_markdown()
    
    # 应该包含 YAML frontmatter 分隔符
    assert md.startswith("---")
    assert md.count("---") >= 2
    
    # 应该包含必要字段
    assert "name:" in md
    assert "description:" in md
    assert "type:" in md
    assert "created:" in md


def test_memory_creates_tags():
    """记忆应该生成 Obsidian 标签。"""
    memory = MemoryItem.create(
        memory_type=MemoryType.USER,
        content="用户喜欢Python",
        description="用户偏好",
        metadata={"tags": ["preference", "python"]}
    )
    
    md = memory.to_markdown()
    
    # 应该在 frontmatter 中包含 tags 列表
    assert "tags:" in md
    assert "- preference" in md
    assert "- python" in md


def test_memory_creates_aliases():
    """记忆应该支持别名。"""
    memory = MemoryItem.create(
        memory_type=MemoryType.USER,
        content="用户喜欢Python",
        description="用户偏好",
        metadata={"aliases": ["用户编程偏好", "语言偏好"]}
    )
    
    md = memory.to_markdown()
    
    # 应该在 frontmatter 中包含 aliases 列表
    assert "aliases:" in md
    assert "- 用户编程偏好" in md
    assert "- 语言偏好" in md


def test_memory_preserves_wikilinks():
    """记忆应该保留 Obsidian 双向链接。"""
    memory = MemoryItem.create(
        memory_type=MemoryType.USER,
        content="用户喜欢Python，参考[[编程语言]]",
        description="用户偏好"
    )
    
    md = memory.to_markdown()
    
    # 应该保留 [[wikilinks]]
    assert "[[编程语言]]" in md


def test_memory_hashtags():
    """记忆应该生成 hashtags。"""
    memory = MemoryItem.create(
        memory_type=MemoryType.USER,
        content="用户喜欢Python",
        description="用户偏好",
        metadata={"tags": ["preference", "python"]}
    )
    
    md = memory.to_markdown()
    
    # 应该包含 hashtags（Obsidian 格式）
    assert "#preference" in md
    assert "#python" in md


def test_memory_content_preserved():
    """记忆内容应该完整保留。"""
    content = "用户喜欢Python，讨厌Java。偏好简洁语法。"
    memory = MemoryItem.create(
        memory_type=MemoryType.USER,
        content=content,
        description="用户偏好"
    )
    
    md = memory.to_markdown()
    
    # 内容应该完整保留
    assert content in md


def test_memory_metadata_preserved():
    """记忆元数据应该完整保留。"""
    memory = MemoryItem.create(
        memory_type=MemoryType.USER,
        content="用户喜欢Python",
        description="用户偏好",
        metadata={
            "tags": ["preference"],
            "aliases": ["用户偏好"],
            "importance": 0.8,
            "user_id": "user123"
        }
    )
    
    md = memory.to_markdown()
    
    # 元数据应该保留
    assert "importance: 0.8" in md
    assert "user_id: user123" in md
