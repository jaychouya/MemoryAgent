from src.memory.inject import format_mandatory_memory_block
from src.agent.prompts.scene import detect_scene
from src.memory.sidecar import build_cursor_rules_block


def test_mandatory_memory_block_lists_ids():
    block = format_mandatory_memory_block([
        {"memory_id": "u1", "memory_type": "user", "content": "喜欢用 Python"},
    ])
    assert "强制记忆注入" in block
    assert "id=u1" in block
    assert "喜欢用 Python" in block


def test_mandatory_memory_empty_forbids_guessing():
    block = format_mandatory_memory_block([])
    assert "禁止引用" in block


def test_detect_scene_exam():
    assert detect_scene("求二重积分 $\\int$") == "exam"
    assert detect_scene("你好") == "general"


def test_cursor_rules_block():
    block = build_cursor_rules_block(
        [{"memory_type": "user", "content": "用 TypeScript"}],
        "demo",
    )
    assert "alwaysApply: true" in block
    assert "TypeScript" in block
