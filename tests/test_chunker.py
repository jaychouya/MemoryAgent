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
        assert len(chunk) <= 300


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
