from src.mcp_server.workspace import scope_summary
from src.memory.authority import GROUND_TRUTH, PRE_ACTION

_GROUND_TRUTH = GROUND_TRUTH
_PRE_ACTION = PRE_ACTION + (
    "\n\n（MCP 侧：未覆盖时调用一次 `memory_recall(query=用户当前问题)`。）"
)

_WORKFLOW = """
### 每轮流程

1. 按上文「行动前检查」决定是否需要 `memory_recall`（可省略 `user_id` / `project_id`，服务端从工作区自动推导）。
2. **回答时**：只引用 recall 结果；标记 `is_stale` 的记忆先核实再当事实。
3. **回答后**：用户明确偏好/禁忌/项目决策/链接时，调用 `memory_store`（`memory_type`: user | feedback | project | reference）。
4. **纠错**：用户说「记错了」「忘记…」→ `memory_delete` / `memory_update`，复述 `ide_notice`。
5. 需要整段注入系统提示时：`memory_export` → 使用 `prompt_block` 或 `cursor_rules_block`。
6. 上下文里出现 `memory_retrieve_blob(ref_id=ccr_…)` 时，用该工具取回完整 tool 输出再分析。

### IDE 内可感知

- 工具返回的 **`ide_notice`**：用一行中文告诉用户召回/写入结果。
- `.memoryagent/status.json` 记录最近一次操作；写入或召回后在回复末尾复述 `ide_notice`。
""".strip()

_PROMPT_SNIPPET = f"""
## MemoryAgent 侧车（任意 MCP 宿主）

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
