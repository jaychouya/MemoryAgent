from src.mcp_server.workspace import scope_summary

_GROUND_TRUTH = """
### 权威层级（Ground Truth）

| 优先级 | 来源 | 用途 |
| --- | --- | --- |
| 1 | 本轮已注入的记忆块（`memory_recall` / `memory_export` 的 `prompt_block`） | 用户偏好、项目决策、禁忌、可复用事实 |
| 2 | 当前工作区代码、终端输出、用户附件 | 运行时状态 |
| 3 | 官方文档、README | API、版本、配置细节 |
| 4 | 模型训练知识 | 仅参考，须与 1-3 核对 |

**冲突规则：** 运行时状态以 2 为准；偏好与历史决策以 1 为准；版本敏感细节以 3 为准。注入记忆与主观假设冲突时，**注入记忆优先**。
""".strip()

_PRE_ACTION = """
### 行动前检查（每轮最多 recall 一次）

1. **清点**：上下文中是否已有 `[user]` / `[feedback]` / `[project]` / `[reference]` 记忆块？
2. **匹配**：当前问题是否已被这些记忆覆盖？
3. **决策**：已覆盖 → 直接引用并回答，**禁止**为「验证」再调 `memory_recall`、搜仓库或读文件重找同一事实。
4. **未覆盖**或话题已切换 → 调用一次 `memory_recall(query=用户当前问题)`。
""".strip()

_WORKFLOW = """
### 每轮流程

1. 按上文「行动前检查」决定是否需要 `memory_recall`（可省略 `user_id` / `project_id`，服务端从工作区自动推导）。
2. **回答时**：只引用 recall 结果；标记 `is_stale` 的记忆先核实再当事实。
3. **回答后**：用户明确偏好/禁忌/项目决策/链接时，调用 `memory_store`（`memory_type`: user | feedback | project | reference）。
4. 需要整段注入系统提示时：`memory_export` → 使用 `prompt_block` 或 `cursor_rules_block`。
5. 上下文里出现 `memory_retrieve_blob(ref_id=ccr_…)` 时，用该工具取回完整 tool 输出再分析。
""".strip()

_PROMPT_SNIPPET = f"""
## MemoryAgent 侧车

{_GROUND_TRUTH}

{_PRE_ACTION}

{_WORKFLOW}
""".strip()


def get_mcp_instructions() -> str:
    return (
        "MemoryAgent memory sidecar v2 (Layer-7 authority). "
        f"Default scope: {scope_summary()}. "
        + _PROMPT_SNIPPET
    )


def get_cursor_rule_body() -> str:
    return f"""# MemoryAgent 侧车

当前作用域（MCP 自动推导，无需手填 user_id）：`{scope_summary()}`

{_PROMPT_SNIPPET}

### 工具速查

| 工具 | 何时用 |
| --- | --- |
| memory_recall | 行动前检查判定「未覆盖」时，每轮最多一次 |
| memory_store | 用户透露可长期保存的事实 |
| memory_update / memory_delete | 纠错、遗忘 |
| memory_list | 浏览已有记忆 |
| memory_export | 需要 sidecar-v2 prompt_block |
"""


def get_sidecar_rule_mdc_body() -> str:
    return f"""---
description: MemoryAgent sidecar — authority hierarchy and surgical recall
alwaysApply: true
---

# MemoryAgent 侧车

MCP 已配置时，`user_id` / `project_id` 由工作区目录名自动推导（无需手填）。

{_PROMPT_SNIPPET}

## 安装（本仓库未装时）

在 MemoryAgent 仓库根目录执行：

```bash
bash scripts/install-sidecar.sh /path/to/your/project
```
"""
