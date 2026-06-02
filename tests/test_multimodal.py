"""Tests for multimodal support."""
import pytest
import tempfile
import os
from pathlib import Path
from src.agent.multimodal import MultimodalProcessor, MultimodalContent, ModalityType


def test_multimodal_processor_creates():
    """MultimodalProcessor 应该能创建。"""
    processor = MultimodalProcessor()
    assert processor is not None


def test_process_file_txt():
    """process_file 应该能处理文本文件。"""
    processor = MultimodalProcessor()
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Hello World")
        temp_path = f.name
    
    try:
        content = processor.process_file(temp_path)
        
        assert content is not None
        assert content.modality_type == ModalityType.FILE
        assert "Hello World" in content.text
    finally:
        os.unlink(temp_path)


def test_process_file_unsupported_format():
    """process_file 应该拒绝不支持的格式。"""
    processor = MultimodalProcessor()
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xyz', delete=False) as f:
        f.write("test")
        temp_path = f.name
    
    try:
        content = processor.process_file(temp_path)
        
        assert content is None
    finally:
        os.unlink(temp_path)


def test_create_multimodal_message_text():
    """create_multimodal_message 应该能创建文本消息。"""
    processor = MultimodalProcessor()
    
    content = processor.create_multimodal_message(text="Hello")
    
    assert content is not None
    assert content.text == "Hello"
    assert content.modality_type == ModalityType.TEXT


def test_create_multimodal_message_file():
    """create_multimodal_message 应该能创建文件消息。"""
    processor = MultimodalProcessor()
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("File content")
        temp_path = f.name
    
    try:
        content = processor.create_multimodal_message(file_path=temp_path)
        
        assert content is not None
        assert "File content" in content.text
        assert content.modality_type == ModalityType.FILE
    finally:
        os.unlink(temp_path)


def test_format_for_llm_text():
    """format_for_llm 应该能格式化文本内容。"""
    processor = MultimodalProcessor()
    
    content = MultimodalContent(text="Hello", modality_type=ModalityType.TEXT)
    result = processor.format_for_llm(content)
    
    assert "content" in result
    assert len(result["content"]) == 1
    assert result["content"][0]["type"] == "text"
    assert result["content"][0]["text"] == "Hello"


def test_get_supported_formats():
    """get_supported_formats 应该返回支持的格式。"""
    processor = MultimodalProcessor()
    
    formats = processor.get_supported_formats()
    
    assert "images" in formats
    assert "files" in formats
    assert ".jpg" in formats["images"]
    assert ".txt" in formats["files"]
