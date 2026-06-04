from src.agent.symbolic_memory import (
    build_mermaid_task_graph,
    inject_symbolic_message,
    should_inject_symbolic,
)


def test_build_mermaid_from_tools():
    messages = [
        {"role": "user", "content": "查 bug"},
        {"role": "tool", "content": "log line 1\n" * 100, "tool_name": "grep"},
        {"role": "tool", "content": "file ok", "tool_name": "read"},
        {"role": "tool", "content": "done", "tool_name": "run"},
    ]
    mermaid, refs = build_mermaid_task_graph(messages, "/tmp/sym_test")
    assert "flowchart TD" in mermaid
    assert "n1" in mermaid
    assert should_inject_symbolic(messages, 3)


def test_inject_dedupes():
    messages = [
        {"role": "tool", "content": "a", "tool_name": "t1"},
        {"role": "tool", "content": "b", "tool_name": "t2"},
        {"role": "tool", "content": "c", "tool_name": "t3"},
    ]
    out = inject_symbolic_message(messages, "/tmp/sym_test2", min_tools=3)
    assert len(out) == len(messages) + 1
    assert "mermaid" in out[-1]["content"]
    out2 = inject_symbolic_message(out, "/tmp/sym_test2", min_tools=3)
    assert len(out2) == len(out)
