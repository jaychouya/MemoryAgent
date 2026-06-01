"""Test TokenJuice context compression."""
import pytest
from src.memory.compressor import CompressionRule, ContextCompressor


def test_compression_rule_matches_tool():
    """规则应该匹配工具名称。"""
    rule = CompressionRule(
        id="test_rule",
        match={"toolNames": ["git"]},
        filters={"skipPatterns": ["^On branch "]}
    )
    
    assert rule.matches("git", "git status") is True
    assert rule.matches("npm", "npm install") is False


def test_compression_rule_matches_argv():
    """规则应该匹配命令行参数。"""
    rule = CompressionRule(
        id="git_status",
        match={"argvIncludes": ["status"]},
        filters={"skipPatterns": ["^On branch "]}
    )
    
    assert rule.matches("git", "git status") is True
    assert rule.matches("git", "git commit") is False


def test_compression_rule_filters_lines():
    """规则应该过滤行。"""
    rule = CompressionRule(
        id="test_rule",
        match={"toolNames": ["git"]},
        filters={
            "skipPatterns": ["^On branch ", "^Your branch is "],
            "keepPatterns": ["^[MADRCU?]{2}\\s"]
        }
    )
    
    output = "On branch main\nYour branch is up to date\n M file.py\nAM file2.py\n"
    result = rule.apply(output)
    
    assert "On branch" not in result
    assert "Your branch" not in result
    assert "file2.py" in result


def test_compression_rule_head_tail():
    """规则应该支持 head-tail 保留策略。"""
    rule = CompressionRule(
        id="test_rule",
        match={"toolNames": ["git"]},
        filters={},
        output={"strategy": "head-tail", "headLines": 2, "tailLines": 1}
    )
    
    lines = ["line1", "line2", "line3", "line4", "line5", "line6"]
    result = rule.apply_head_tail("\n".join(lines))
    
    assert "line1" in result
    assert "line2" in result
    assert "line6" in result


def test_compressor_compresses_output():
    """压缩器应该压缩工具输出。"""
    compressor = ContextCompressor()
    
    # 添加规则
    compressor.add_rule(CompressionRule(
        id="git_status",
        match={"toolNames": ["git"]},
        filters={"skipPatterns": ["^On branch "]}
    ))
    
    # 压缩输出
    output = "On branch main\nYour branch is up to date\n M file.py\n"
    result = compressor.compress("git", "git status", output)
    
    assert "On branch" not in result
    assert "file.py" in result


def test_compressor_loads_builtin_rules():
    """压缩器应该加载内置规则。"""
    compressor = ContextCompressor()
    
    # 应该有内置规则
    assert len(compressor.rules) > 0


def test_compressor_measures_savings():
    """压缩器应该测量节省的 token 数。"""
    compressor = ContextCompressor()
    
    output = "On branch main\nYour branch is up to date\nnothing to commit\n M file.py\n" * 25
    result = compressor.compress("git", "git status", output)
    
    stats = compressor.get_stats()
    assert stats["total_input_tokens"] > 0
    assert stats["total_output_tokens"] > 0
    assert stats["savings_ratio"] > 0
