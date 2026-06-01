"""Test memory summarizer."""
import pytest
from src.memory.summarizer import MemorySummarizer


def test_summarizer_creates_summary():
    """摘要生成器应该能创建摘要。"""
    summarizer = MemorySummarizer()
    
    memories = [
        {"content": "用户喜欢Python，因为语法简洁", "importance": 0.8},
        {"content": "用户讨厌Java，因为代码冗长", "importance": 0.7},
        {"content": "用户偏好简洁语法，讨厌冗余代码", "importance": 0.6}
    ]
    
    summary = summarizer.summarize(memories)
    
    # 摘要应该包含关键信息
    assert "Python" in summary
    # 摘要应该存在
    assert len(summary) > 0


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
