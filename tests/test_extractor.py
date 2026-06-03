"""Tests for Extract Memories Agent."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.memory.extractor import ExtractMemoriesAgent, ExtractedMemory


@pytest.fixture
def mock_llm():
    """Create a mock LLM service."""
    llm = AsyncMock()
    llm.generate_response = AsyncMock(return_value={
        "content": '''
```json
[
  {
    "content": "用户喜欢 Python",
    "memory_type": "user",
    "description": "用户偏好 Python 语言",
    "reason": "用户明确表达偏好",
    "confidence": 0.9
  }
]
```
'''
    })
    return llm


@pytest.fixture
def extractor(mock_llm):
    """Create an extractor with mock LLM."""
    return ExtractMemoriesAgent(llm_service=mock_llm)


def test_extractor_creates():
    """ExtractMemoriesAgent 应该能创建。"""
    extractor = ExtractMemoriesAgent()
    assert extractor is not None


def test_extractor_has_memory_types(extractor):
    """应该定义记忆类型。"""
    assert "user" in extractor.MEMORY_TYPES
    assert "feedback" in extractor.MEMORY_TYPES
    assert "project" in extractor.MEMORY_TYPES
    assert "reference" in extractor.MEMORY_TYPES


def test_extractor_has_exclusion_rules(extractor):
    """应该有排除规则。"""
    assert len(extractor.EXCLUSION_RULES) > 0


@pytest.mark.asyncio
async def test_extractor_extracts_memories(extractor):
    """extract 应该提取记忆。"""
    messages = [
        {"role": "user", "content": "我喜欢 Python，讨厌 Java"},
        {"role": "assistant", "content": "好的，我记住了"}
    ]
    
    memories = await extractor.extract(messages)
    
    assert len(memories) > 0
    assert memories[0].memory_type == "user"
    assert "Python" in memories[0].content


@pytest.mark.asyncio
async def test_extractor_filters_duplicates(extractor):
    """extract 应该过滤重复记忆。"""
    messages = [
        {"role": "user", "content": "我喜欢 Python"},
    ]
    
    existing = [
        {"description": "用户偏好 Python 语言"}
    ]
    
    memories = await extractor.extract(messages, existing_memories=existing)
    
    # 应该被过滤掉
    assert len(memories) == 0


@pytest.mark.asyncio
async def test_extractor_handles_no_llm():
    """没有 LLM 时应该返回空列表。"""
    extractor = ExtractMemoriesAgent(llm_service=None)
    
    messages = [{"role": "user", "content": "test"}]
    memories = await extractor.extract(messages)
    
    assert len(memories) == 0


def test_extractor_parses_json(extractor):
    """_parse_extracted_memories 应该解析 JSON。"""
    content = '''
```json
[
  {
    "content": "用户喜欢 Python",
    "memory_type": "user",
    "description": "用户偏好",
    "reason": "明确表达",
    "confidence": 0.9
  }
]
```
'''
    
    memories = extractor._parse_extracted_memories(content)
    
    assert len(memories) == 1
    assert memories[0].content == "用户喜欢 Python"
    assert memories[0].memory_type == "user"


def test_extractor_handles_invalid_json(extractor):
    """_parse_extracted_memories 应该处理无效 JSON。"""
    content = "这不是 JSON"
    
    memories = extractor._parse_extracted_memories(content)
    
    assert len(memories) == 0


def test_extractor_is_similar(extractor):
    """_is_similar 应该检查相似度。"""
    # 相同内容应该相似
    assert extractor._is_similar("用户喜欢Python", "用户喜欢Python") is True
    # 完全不同应该不相似
    assert extractor._is_similar("用户喜欢Python", "今天天气很好") is False


def test_extractor_get_stats(extractor):
    """get_stats 应该返回统计信息。"""
    stats = extractor.get_stats()
    
    assert "extracted_count" in stats
    assert "memory_types" in stats
    assert "exclusion_rules" in stats
