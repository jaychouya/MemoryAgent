# Architecture Decision: Memory Sidecar

## Decision

MemoryAgent ships as a **memory sidecar**, not a full coding agent.

- **In scope**: durable user model (4 memory types), local Markdown storage, hybrid recall, SSE chat, export/recall HTTP API for external agents.
- **Out of scope (v1)**: shell, git, browser, MCP host runtime, Redis/PG/Chroma four-layer stack.

## Rationale

Coding agents (Cursor, Claude Code, Devin) optimize **Act + Perceive**. MemoryAgent optimizes **Remember + Align** (editable, local, explainable memory). Competing on code execution duplicates mature products without leverage.

## Read path (runtime)

| Layer | Mechanism | Purpose |
|-------|-----------|---------|
| L1 Working | `sessions/*.json` recent turns in chat | Current topic continuity |
| L2 Long-term | SQLite FTS + persistent vectors, hybrid merge | Precision recall |
| L2b Rewrite | `query_rewrite.py` when query ≥ 80 chars | Reduce noise in FTS/embedding |
| Top-K | Default 5, rerank pool 20 → 5 | Token budget & signal-to-noise |

**Rejected**: load N-day summary blobs into every prompt; vector-only without keyword/metadata filter.

## Write path (runtime)

| Step | Mechanism |
|------|-----------|
| L1 Fast | Regex / rules (`auto_write`) on every turn |
| L2 Deep | LLM extract only if user+assistant ≥ `MEMORY_EXTRACT_LLM_MIN_CHARS` (default 400) |
| Persist | Markdown + per-item vector upsert |
| Delivery | **Eventual consistency** — `MEMORY_OBSERVER_ASYNC=true` fires `observe_turn` via `asyncio.create_task` after chat returns |

**Rejected**: block main chat on LLM extract + vector write; sync small-model extract on critical path before first token.

## Integration

| Consumer | Integration |
|----------|-------------|
| Cursor / Claude Code | MCP v2: `memory_recall/store/update/delete/list/export` — see [cursor-integration.md](cursor-integration.md) |
| HTTP sidecar | Same ops + `PATCH /api/memories/{id}`, `GET /api/memory/audit` (optional `MEMORYAGENT_API_KEY`) |
| Custom frontend | Next.js UI + `POST /api/chat/stream` (OpenAI token streaming when no tools) |

## Headroom-inspired (CCR + ContentRouter)

- 大 tool 输出：`content_router` 分类型压缩 + `ccr_blobs/` 可逆存储
- MCP：`memory_retrieve_blob(ref_id)` 取回全文
- 可选外挂 [Headroom](https://github.com/chopratejas/headroom) proxy — 见 `docs/headroom-integration.md`

## Tencent-inspired (D 方案)

- **L0→L1 证据链**：`memories/l0/{user}/` jsonl 原话 + L1 记忆 frontmatter 溯源字段；citation 透传 `source_quote` / `source_session_id`
- **符号化工作记忆**：tool 轮次 ≥3 时注入 Mermaid 任务图 + 节点→落盘路径（`SYMBOLIC_MEMORY_*`）

## Deferred (documented, not deleted)

A four-layer scale path (Redis → PostgreSQL → Chroma → graph) is **deferred**. Runtime uses Markdown + SQLite FTS + persistent vectors until multi-user scale requires infra.

When scale demands: message queue for writes, batch vector upsert, Redis L1 for hot sessions.

## Success metrics

- Recall@5 on golden preferences > 90% — `POST /api/memory/metrics/run-eval`
- False memory injection < 5% — decoy cases in golden eval (`false_inject_rate`), `GET /api/memory/metrics`
- User can see which memories were used within 3 turns — ChatPanel memory citations UI

## Config reference

| Env / setting | Default | Role |
|---------------|---------|------|
| `MEMORY_OBSERVER_ASYNC` | true | Background memory write after chat |
| `MEMORY_EXTRACT_LLM_MIN_CHARS` | 400 | Tiered LLM extract threshold |
| `MEMORY_QUERY_REWRITE_*` | on, 80/120 | Retrieval query shortening |
| `RERANK_ENABLED` | true | Candidate pool rerank |
