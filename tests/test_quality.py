"""Tests for memory quality management."""
import pytest
from datetime import datetime, timedelta
from src.memory.quality import MemoryQualityManager, MemoryQualityScore


def test_memory_quality_manager_creates():
    """MemoryQualityManager 应该能创建。"""
    manager = MemoryQualityManager()
    assert manager is not None


def test_score_memory_returns_scores():
    """score_memory 应该返回质量分数。"""
    manager = MemoryQualityManager()
    
    memory = {
        "content": "用户喜欢Python，讨厌Java",
        "metadata": {"type": "user"},
        "created_at": datetime.now().isoformat()
    }
    
    score = manager.score_memory(memory)
    
    assert isinstance(score, MemoryQualityScore)
    assert 0 <= score.relevance <= 1
    assert 0 <= score.freshness <= 1
    assert 0 <= score.specificity <= 1
    assert 0 <= score.importance <= 1
    assert 0 <= score.overall <= 1


def test_score_memory_high_quality():
    """高质量记忆应该有高分。"""
    manager = MemoryQualityManager()
    
    memory = {
        "content": "用户喜欢Python，讨厌Java，因为Python语法简洁，适合快速开发",
        "metadata": {"type": "feedback", "importance": 0.9},
        "created_at": datetime.now().isoformat()
    }
    
    score = manager.score_memory(memory)
    
    assert score.overall > 0.6


def test_score_memory_low_quality():
    """低质量记忆应该有低分。"""
    manager = MemoryQualityManager()
    
    memory = {
        "content": "嗯",
        "metadata": {},
        "created_at": (datetime.now() - timedelta(days=90)).isoformat()
    }
    
    score = manager.score_memory(memory)
    
    assert score.overall < 0.5


def test_detect_conflicts_finds_conflicts():
    """detect_conflicts 应该能发现冲突。"""
    manager = MemoryQualityManager()
    
    memories = [
        {"id": "1", "content": "用户喜欢Python"},
        {"id": "2", "content": "用户讨厌Python"}
    ]
    
    conflicts = manager.detect_conflicts(memories)
    
    assert len(conflicts) > 0


def test_detect_conflicts_no_conflicts():
    """没有冲突时应该返回空列表。"""
    manager = MemoryQualityManager()
    
    memories = [
        {"id": "1", "content": "用户喜欢Python"},
        {"id": "2", "content": "用户喜欢Java"}
    ]
    
    conflicts = manager.detect_conflicts(memories)
    
    assert len(conflicts) == 0


def test_get_low_quality_memories():
    """get_low_quality_memories 应该返回低质量记忆。"""
    manager = MemoryQualityManager()
    
    memories = [
        {
            "id": "1",
            "content": "用户喜欢Python，讨厌Java，因为Python语法简洁",
            "metadata": {"type": "feedback"},
            "created_at": datetime.now().isoformat()
        },
        {
            "id": "2",
            "content": "嗯",
            "metadata": {},
            "created_at": (datetime.now() - timedelta(days=90)).isoformat()
        }
    ]
    
    low_quality = manager.get_low_quality_memories(memories)
    
    assert len(low_quality) > 0
    assert low_quality[0]["memory"]["id"] == "2"


def test_get_stale_memories():
    """get_stale_memories 应该返回过期记忆。"""
    manager = MemoryQualityManager()
    
    memories = [
        {
            "id": "1",
            "content": "新记忆",
            "created_at": datetime.now().isoformat()
        },
        {
            "id": "2",
            "content": "旧记忆",
            "created_at": (datetime.now() - timedelta(days=60)).isoformat()
        }
    ]
    
    stale = manager.get_stale_memories(memories)
    
    assert len(stale) == 1
    assert stale[0]["id"] == "2"


def test_cleanup_memories_dry_run():
    """cleanup_memories dry_run 应该返回清理计划。"""
    manager = MemoryQualityManager()
    
    memories = [
        {
            "id": "1",
            "content": "嗯",
            "metadata": {},
            "created_at": (datetime.now() - timedelta(days=90)).isoformat()
        }
    ]
    
    result = manager.cleanup_memories(memories, dry_run=True)
    
    assert result["dry_run"] is True
    assert result["to_cleanup_count"] > 0
