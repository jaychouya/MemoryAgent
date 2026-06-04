# Tencent-inspired D 方案 Implementation Plan

> **Goal:** L0→L1 证据链 + Mermaid 符号化工作记忆，不做法 L2/L3 自动画像。

**Status:** implemented in codebase (2026-06-03).

## Delivered

- `src/memory/provenance.py` — L0 jsonl + L1 metadata
- `src/agent/symbolic_memory.py` — Mermaid inject after tool rounds
- `write_pipeline` / `citations` / `retrieval` / `query_loop` / `ContextCompressor`
- Spec: `docs/superpowers/specs/2026-06-03-tencent-inspired-d-design.md`
- Tests: `test_provenance.py`, `test_symbolic_memory.py`

## Config

`PROVENANCE_ENABLED`, `SYMBOLIC_MEMORY_ENABLED`, `SYMBOLIC_MEMORY_MIN_TOOLS`
