"""Tests for conditional rules system."""
import pytest
import tempfile
import shutil
from pathlib import Path
from src.memory.conditional_rules import ConditionalRules, IncludeProcessor


@pytest.fixture
def temp_rules_dir():
    """Create a temporary rules directory."""
    temp_dir = tempfile.mkdtemp()
    rules_dir = Path(temp_dir) / "rules"
    rules_dir.mkdir()
    yield rules_dir
    shutil.rmtree(temp_dir)


def test_conditional_rules_creates(temp_rules_dir):
    """ConditionalRules 应该能创建。"""
    rules = ConditionalRules(rules_dir=str(temp_rules_dir))
    assert rules is not None


def test_load_rules(temp_rules_dir):
    """load_rules 应该加载规则文件。"""
    # 创建规则文件
    rule_file = temp_rules_dir / "frontend.md"
    rule_file.write_text("""---
name: 前端规范
description: React + Tailwind 项目规范
paths: ["**/*.tsx", "**/*.jsx"]
---

# 前端规范

使用 React Hooks""")
    
    rules = ConditionalRules(rules_dir=str(temp_rules_dir))
    rules.load_rules()
    
    assert len(rules.rules) == 1
    assert rules.rules[0].name == "前端规范"


def test_get_matching_rules(temp_rules_dir):
    """get_matching_rules 应该返回匹配的规则。"""
    # 创建规则文件
    rule_file = temp_rules_dir / "frontend.md"
    rule_file.write_text("""---
name: 前端规范
paths: ["**/*.tsx", "**/*.jsx"]
---

使用 React Hooks""")
    
    rules = ConditionalRules(rules_dir=str(temp_rules_dir))
    rules.load_rules()
    
    # 匹配的文件
    matching = rules.get_matching_rules("src/components/App.tsx")
    assert len(matching) == 1
    
    # 不匹配的文件
    matching = rules.get_matching_rules("src/main.py")
    assert len(matching) == 0


def test_assemble_rules(temp_rules_dir):
    """assemble_rules 应该组装匹配的规则。"""
    rule_file = temp_rules_dir / "frontend.md"
    rule_file.write_text("""---
name: 前端规范
paths: ["**/*.tsx"]
---

使用 React Hooks""")
    
    rules = ConditionalRules(rules_dir=str(temp_rules_dir))
    rules.load_rules()
    
    content = rules.assemble_rules("src/App.tsx")
    
    assert "React Hooks" in content


def test_get_stats(temp_rules_dir):
    """get_stats 应该返回统计信息。"""
    rule_file = temp_rules_dir / "test.md"
    rule_file.write_text("""---
name: 测试
paths: ["**/*.py"]
---

测试规范""")
    
    rules = ConditionalRules(rules_dir=str(temp_rules_dir))
    rules.load_rules()
    
    stats = rules.get_stats()
    
    assert stats["total_rules"] == 1
    assert stats["total_patterns"] == 1


def test_include_processor_creates():
    """IncludeProcessor 应该能创建。"""
    processor = IncludeProcessor()
    assert processor is not None


def test_include_processor_processes():
    """process 应该处理 @include 指令。"""
    temp_dir = tempfile.mkdtemp()
    
    try:
        # 创建被包含的文件
        include_file = Path(temp_dir) / "rules.md"
        include_file.write_text("# 规则\n\n不要用 mock")
        
        # 创建主文件
        main_content = "# 配置\n\n@include rules.md"
        
        processor = IncludeProcessor()
        result = processor.process(main_content, Path(temp_dir))
        
        assert "不要用 mock" in result
    finally:
        shutil.rmtree(temp_dir)


def test_include_processor_handles_missing():
    """process 应该处理不存在的文件。"""
    processor = IncludeProcessor()
    result = processor.process("@include missing.md", Path("/tmp"))
    
    assert "not found" in result.lower() or "Include" in result


def test_include_processor_prevents_circular():
    """process 应该防止循环引用。"""
    temp_dir = tempfile.mkdtemp()
    
    try:
        # 创建循环引用的文件
        file_a = Path(temp_dir) / "a.md"
        file_a.write_text("# A\n\n@include b.md")
        
        file_b = Path(temp_dir) / "b.md"
        file_b.write_text("# B\n\n@include a.md")
        
        processor = IncludeProcessor()
        result = processor.process("# Main\n\n@include a.md", Path(temp_dir))
        
        # 应该检测到循环引用
        assert "Circular" in result or "circular" in result or "Include" in result
    finally:
        shutil.rmtree(temp_dir)
