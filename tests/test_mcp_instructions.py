from src.mcp_server.instructions import (
    get_mcp_instructions,
    get_cursor_rule_body,
    get_sidecar_rule_mdc_body,
)


def test_mcp_instructions_include_layer7_authority():
    text = get_mcp_instructions()
    assert "权威层级" in text
    assert "Ground Truth" in text
    assert "禁止" in text
    assert "每轮最多" in text


def test_cursor_rule_body_matches_authority_snippet():
    text = get_cursor_rule_body()
    assert "行动前检查" in text
    assert "memory_recall" in text


def test_sidecar_mdc_includes_frontmatter():
    text = get_sidecar_rule_mdc_body()
    assert "alwaysApply: true" in text
    assert "注入记忆优先" in text or "注入记忆" in text
