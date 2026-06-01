"""Test memory scorer."""
import pytest
from src.memory.scorer import MemoryScorer


def test_scorer_scores_user_preferences():
    """评分器应该给用户偏好高分。"""
    scorer = MemoryScorer()
    
    content = "我喜欢Python，讨厌Java，因为Python语法简洁易读"
    memory_type = "user"
    
    score = scorer.score(content, memory_type)
    
    # 用户偏好应该有较高分数
    assert score >= 0.4


def test_scorer_scores_feedback():
    """评分器应该给行为反馈高分。"""
    scorer = MemoryScorer()
    
    content = "不要用mock数据库，必须使用真实数据库"
    memory_type = "feedback"
    
    score = scorer.score(content, memory_type)
    
    # 行为反馈应该有较高分数
    assert score >= 0.4


def test_scorer_scores_low_for_noise():
    """评分器应该给噪音内容低分。"""
    scorer = MemoryScorer()
    
    content = "嗯"
    memory_type = "user"
    
    score = scorer.score(content, memory_type)
    
    # 噪音应该有低分
    assert score < 0.5
