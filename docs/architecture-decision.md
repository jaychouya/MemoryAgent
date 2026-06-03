# Architecture Decision: Memory Sidecar

## Decision

MemoryAgent ships as a **memory sidecar**, not a full coding agent.

- **In scope**: durable user model (4 memory types), local Markdown storage, hybrid recall, SSE chat, export/recall HTTP API for external agents.
- **Out of scope (v1)**: shell, git, browser, MCP host runtime, Redis/PG/Chroma four-layer stack.

## Rationale

Coding agents (Cursor, Claude Code, Devin) optimize **Act + Perceive**. MemoryAgent optimizes **Remember + Align** (editable, local, explainable memory). Competing on code execution duplicates mature products without leverage.

## Integration

| Consumer | Integration |
|----------|-------------|
| Cursor / Claude Code | `GET /api/memory/export`, `POST /api/memory/recall` |
| Custom frontend | Next.js UI + `POST /api/chat/stream` |
| Future MCP server | Wrap recall/store tools over the HTTP API |

## Deferred (documented, not deleted)

The four-layer spec (Redis → PostgreSQL → Chroma → graph) remains in `docs/superpowers/specs/` as a **future scale path**. Runtime uses Markdown + SQLite FTS + in-memory vectors until multi-user scale requires infra.

## Success metrics

- Recall@5 on golden preferences > 90% — `POST /api/memory/metrics/run-eval`
- False memory injection < 5% — reported in `GET /api/memory/metrics`
- User can see which memories were used within 3 turns — ChatPanel memory citations UI
