# Memory OS Layer 7 借鉴 — 方案 A（指令层增强）

## 背景

[memory-os](https://github.com/ClaudioDrews/memory-os) 的核心发现：记忆**注入**不等于记忆**使用**。Agent 常在 prompt 已有记忆时仍调用工具重复发现（memory-zero 行为）。

## 方案 A 范围

| 做 | 不做 |
| --- | --- |
| MCP instructions 权威层级 | Docker / Qdrant 全栈 |
| Cursor rule 同步更新 | Wiki 自策展管线 |
| `prompt_block` / `cursor_rules_block` 脚注 | Trust score 反馈环（方案 B） |
| 行动前检查（每轮最多 recall 一次） | 4 级检索降级（方案 B） |

## 权威层级

1. 已注入记忆块 → 偏好与项目决策
2. 代码/终端/附件 → 运行时状态
3. 官方文档 → 版本细节
4. 训练知识 → 仅参考

## 改动文件

- `src/mcp_server/instructions.py`
- `integrations/cursor/memory-sidecar.mdc`
- `src/memory/sidecar.py`（export 块脚注）
- `docs/cursor-integration.md`

## 验收

- MCP `instructions` 含层级 + 禁止重复 recall
- `install-sidecar.sh` 安装的 rule 与 MCP 一致
- `tests/test_mcp_instructions.py` 通过
