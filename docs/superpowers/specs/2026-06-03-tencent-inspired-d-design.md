# D 方案：证据链 + 符号化工作记忆

**Goal:** 借鉴 TencentDB Agent Memory 的可追溯与短期拓扑思路，保持 MemoryAgent 侧车定位。

## 1. 证据链（L0 → L1）

- **L0**：每轮对话追加 `memories/l0/{user_id}/{session_id}.jsonl`（user/assistant 原文片段）。
- **L1**：`MemoryItem.metadata` 写入 `evidence_level=L1`、`source_session_id`、`source_quote`、`l0_path`。
- **Citation**：召回时从 Markdown 合并溯源字段；API/SSE 透传 `source_quote`、`source_session_id`。

不做 L2 聚类、L3 自动画像（YAGNI）。

## 2. 符号化工作记忆（Mermaid）

- 当单轮累计 tool 消息 ≥ `SYMBOLIC_MEMORY_MIN_TOOLS`（默认 3），生成 `flowchart TD` 任务图。
- 大 tool 输出仍走 Layer1 落盘；图中节点 ID 映射 `symbolic_{n}` → 文件路径。
- 在 `query_loop` tool 轮结束后注入一条 `system` 消息（可配置关闭）。

## 3. 配置

| 变量 | 默认 |
|------|------|
| `PROVENANCE_ENABLED` | true |
| `SYMBOLIC_MEMORY_ENABLED` | true |
| `SYMBOLIC_MEMORY_MIN_TOOLS` | 3 |

## 4. 非目标

- 四层晋升流水线、自动用户画像、RRF 重写。
