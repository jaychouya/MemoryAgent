from src.mcp_server.workspace import scope_summary

_PROMPT_SNIPPET = """
## MemoryAgent 侧车（每轮必做）

1. **回答前**：调用 `memory_recall`，`query` = 用户当前问题（可省略 `user_id`/`project_id`，服务端从工作区自动推导）。
2. **回答时**：只引用 recall 结果；陈旧记忆先核实再当事实。
3. **回答后**：用户明确偏好/禁忌/项目决策/链接时，调用 `memory_store`（`memory_type`: user|feedback|project|reference）。
4. 需要整段注入系统提示时：调用 `memory_export` 取 `prompt_block`。
5. 上下文里出现 `memory_retrieve_blob(ref_id=ccr_…)` 时，用该工具取回完整 tool 输出再分析。
""".strip()


def get_mcp_instructions() -> str:
    return (
        "MemoryAgent memory sidecar v2. "
        f"Default scope: {scope_summary()}. "
        + _PROMPT_SNIPPET
    )


def get_cursor_rule_body() -> str:
    return f"""# MemoryAgent 侧车

当前作用域（MCP 自动推导，无需手填 user_id）：`{scope_summary()}`

{_PROMPT_SNIPPET}

### 工具速查

| 工具 | 何时用 |
|------|--------|
| memory_recall | 每轮回答前 |
| memory_store | 用户透露可长期保存的事实 |
| memory_update / memory_delete | 纠错、遗忘 |
| memory_list | 浏览已有记忆 |
| memory_export | 需要 sidecar-v2 prompt_block |
"""
