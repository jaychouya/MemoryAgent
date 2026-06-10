"""Test output format prompts markdown + LaTeX for math."""
from src.agent.prompts.sections import OUTPUT_STYLE


def test_output_style_supports_markdown_and_math():
    content = OUTPUT_STYLE.content
    assert "Markdown" in content
    assert "$$" in content
    assert "LaTeX" in content
    assert "全角" in content


def test_output_style_has_math_example():
    content = OUTPUT_STYLE.content
    assert "第一步" in content
    assert "**答案：**" in content
    assert "------" in content
    assert "x^2 + y^2" in content
    assert "\\iint" in content
    assert "禁止" in content
