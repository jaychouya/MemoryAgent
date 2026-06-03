"""Tests for LLM-based memory selector."""
import pytest
from unittest.mock import AsyncMock
from datetime import datetime, timedelta
from src.memory.selector import MemorySelector


@pytest.fixture
def mock_llm():
    """Create a mock LLM service."""
    llm = AsyncMock()
    llm.generate_response = AsyncMock(return_value={
        "content": '["user_1", "feedback_1"]'
    })
    return llm


@pytest.fixture
def selector(mock_llm):
    """Create a selector with mock LLM."""
    return MemorySelector(llm_service=mock_llm)


def test_selector_creates():
    """MemorySelector 应该能创建。"""
    selector = MemorySelector()
    assert selector is not None


def test_selector_has_stale_threshold(selector):
    """应该有老化阈值。"""
    assert selector.STALE_WARNING_DAYS == 2


@pytest.mark.asyncio
async def test_selector_selects_memories(selector):
    """select 应该选择记忆。"""
    memories = [
        {"id": "user_1", "description": "用户喜欢 Python", "type": "user", "created_at": datetime.now().isoformat()},
        {"id": "feedback_1", "description": "不要用 mock", "type": "feedback", "created_at": datetime.now().isoformat()},
        {"id": "project_1", "description": "项目截止日期", "type": "project", "created_at": datetime.now().isoformat()},
    ]
    
    selected = await selector.select("Python 排序", memories)
    
    assert len(selected) > 0
    assert selected[0]["id"] == "user_1"


@pytest.mark.asyncio
async def test_selector_filters_surfaced(selector):
    """select 应该过滤已展示的记忆。"""
    memories = [
        {"id": "user_1", "description": "用户喜欢 Python", "type": "user", "created_at": datetime.now().isoformat()},
    ]
    
    # 第一次选择
    await selector.select("Python", memories)
    
    # 第二次应该被过滤
    selected = await selector.select("Python", memories)
    
    assert len(selected) == 0


@pytest.mark.asyncio
async def test_selector_handles_empty_memories(selector):
    """select 应该处理空记忆列表。"""
    selected = await selector.select("test", [])
    
    assert len(selected) == 0


@pytest.mark.asyncio
async def test_selector_handles_no_llm():
    """没有 LLM 时应该使用 fallback。"""
    selector = MemorySelector(llm_service=None)
    
    memories = [
        {"id": "user_1", "description": "用户喜欢 Python", "type": "user", "created_at": datetime.now().isoformat()},
    ]
    
    selected = await selector.select("Python", memories)
    
    assert len(selected) > 0


def test_selector_build_manifest(selector):
    """_build_manifest 应该构建清单。"""
    memories = [
        {"id": "user_1", "description": "用户喜欢 Python", "type": "user", "created_at": datetime.now().isoformat()},
        {"id": "feedback_1", "description": "不要用 mock", "type": "feedback", "created_at": (datetime.now() - timedelta(days=5)).isoformat()},
    ]
    
    manifest = selector._build_manifest(memories)
    
    assert "user_1" in manifest
    assert "feedback_1" in manifest
    assert "用户喜欢 Python" in manifest
    assert "(今天)" in manifest or "(5天前)" in manifest


def test_selector_fallback_select(selector):
    """_fallback_select 应该使用关键词匹配。"""
    memories = [
        {"id": "user_1", "description": "用户喜欢 Python", "type": "user", "created_at": datetime.now().isoformat()},
        {"id": "feedback_1", "description": "不要用 mock", "type": "feedback", "created_at": datetime.now().isoformat()},
    ]
    
    selected = selector._fallback_select("Python", memories, top_k=2)
    
    assert len(selected) > 0
    assert selected[0]["id"] == "user_1"


def test_selector_filter_tool_docs(selector):
    """_filter_tool_docs 应该过滤工具文档。"""
    memories = [
        {"id": "mem_1", "description": "用户喜欢 Python", "type": "user"},
        {"id": "mem_2", "description": "git 使用说明", "type": "reference"},
        {"id": "mem_3", "description": "git 警告：不要 force push", "type": "reference"},
    ]
    
    filtered = selector._filter_tool_docs(memories, ["git"])
    
    # 应该保留用户记忆和警告
    assert len(filtered) == 2
    assert any(m["id"] == "mem_1" for m in filtered)
    assert any(m["id"] == "mem_3" for m in filtered)


def test_selector_get_stale_warning(selector):
    """_get_stale_warning 应该返回老化警告。"""
    # 新记忆
    new_memory = {"created_at": datetime.now().isoformat()}
    assert selector._get_stale_warning(new_memory) is None
    
    # 旧记忆
    old_memory = {"created_at": (datetime.now() - timedelta(days=5)).isoformat()}
    warning = selector._get_stale_warning(old_memory)
    
    assert warning is not None
    assert "5 天" in warning


def test_selector_clear_surfaced(selector):
    """clear_surfaced 应该清空已展示记忆。"""
    selector.already_surfaced.add("user_1")
    
    selector.clear_surfaced()
    
    assert len(selector.already_surfaced) == 0


def test_selector_get_stats(selector):
    """get_stats 应该返回统计信息。"""
    stats = selector.get_stats()
    
    assert "surfaced_count" in stats
    assert "stale_threshold_days" in stats
