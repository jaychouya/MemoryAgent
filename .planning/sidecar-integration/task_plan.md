# Sidecar 集成体验闭环

**Goal:** Cursor/Claude Code 近零配置 + HTTP 聊天与 MCP 同一套 workspace/git 作用域。

## Phase 1: MCP 零配置

**Status:** complete

- install-sidecar.sh、.cursor/mcp.json 模板、memory-sidecar.mdc
- MCP instructions、可选 user_id

## Phase 2: 作用域智能推导

**Status:** complete

- workspace.py：目录名 user_id、Git 根目录 project_id
- HTTP chat：anonymous → effective_chat_scope

## Phase 3: 读写路径原则

**Status:** complete

- 异步 observer、分级 LLM 提取、query rewrite
- architecture-decision.md

## Acceptance

- `scripts/check-complete.sh` 输出 ALL PHASES COMPLETE
- `pytest tests/test_mcp_workspace.py` 通过
