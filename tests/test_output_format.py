"""Test output format is pure text without Markdown."""
import pytest
from src.agent.prompts.sections import OUTPUT_STYLE


def test_output_style_forbids_markdown():
    """System Prompt 应该禁止使用 Markdown 符号。"""
    content = OUTPUT_STYLE.content
    
    # 验证包含禁止的符号列表
    assert "#" in content
    assert "*" in content
    assert "`" in content
    assert "|" in content
    assert ">" in content
    assert "-" in content
    
    # 验证包含示例
    assert "正确的输出示例" in content
    assert "Python 是一种高级编程语言" in content


def test_output_style_has_code_example():
    """System Prompt 应该包含代码示例的正确格式。"""
    content = OUTPUT_STYLE.content
    
    # 验证包含代码示例说明
    assert "代码示例" in content
    assert "def bubble_sort" in content
