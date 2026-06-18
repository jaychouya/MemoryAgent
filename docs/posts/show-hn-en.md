## Show HN: MemoryAgent – universal local memory for AI agents (chat, MCP, HTTP)

**URL**: https://github.com/jaychouya/MemoryAgent

A **memory layer** that isn't tied to one IDE. Same Markdown store, three ways in:

1. **Standalone web chat** — `make dev`, configure API key, talk + manage memories
2. **Any MCP host** — Cursor, Claude Code, Cline, Windsurf, custom agents
3. **HTTP API** — embed in your own app or bots (`/api/chat/stream`, `/api/memory/*`)

**Problem**: Every new session, you re-explain preferences and project context.

**Approach**:
- Local Markdown + SQLite (no required cloud)
- Explainable recall (citations, stale hints, Recall@5 in CI)
- One storage dir shared across all clients

**Not** another coding agent — only Remember + Align.

**Try**: clone → `make dev` for instant chat, or `bash scripts/onboard.sh .` for MCP.

Feedback welcome on HTTP vs MCP ergonomics and what you'd need to trust memory injection.
