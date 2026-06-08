# Recall Quality CRUD Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add local recall judging, automatic memory conflict expiry, and a UI correction loop.

**Architecture:** Keep the default path local and deterministic. Retrieval produces candidates, `RecallJudge` filters and explains them, storage auto-expires high-confidence conflicts, and MemoryPanel exposes list/edit/delete/eval.

**Tech Stack:** Python, FastAPI, pytest, Next.js React components.

---

### Task 1: Recall Judge

**Files:**
- Create: `src/memory/recall_judge.py`
- Modify: `src/memory/retrieval.py`
- Modify: `src/memory/sidecar.py`
- Test: `tests/test_recall_judge.py`

- [x] Write tests for superseded filtering, Chinese relevance, and scope mismatch.
- [x] Implement rule-based `judge_memories()`.
- [x] Call judge from `MemoryRetrieval.retrieve()`.
- [x] Export `judge_score`, `judge_reason`, `dropped_reason`.
- [x] Run `python3 -m pytest tests/test_recall_judge.py tests/test_recall_eval.py -q`.

### Task 2: Automatic Conflict Detection

**Files:**
- Create: `src/memory/conflicts.py`
- Modify: `src/memory/manager.py`
- Test: `tests/test_memory_conflicts.py`

- [x] Write a failing test for `Python` preference superseded by `now mainly use Rust`.
- [x] Implement same-scope, high-confidence conflict detection.
- [x] Mark old memory with `superseded_by`, `valid_until`, `conflict_reason`.
- [x] Remove old memory from active vector search.
- [x] Run `python3 -m pytest tests/test_memory_conflicts.py tests/test_memory_manager.py -q`.

### Task 3: Ownership-Safe CRUD

**Files:**
- Modify: `src/mcp_server/tools.py`
- Modify: `src/backend/api/memory.py`
- Modify: `src/memory/manager.py`
- Test: `tests/test_memory_crud_permissions.py`

- [x] Write tests that another user cannot update/delete a memory.
- [x] Add ownership checks before update/delete.
- [x] Ensure list/export include provenance and supersede metadata.
- [x] Run `python3 -m pytest tests/test_memory_crud_permissions.py tests/test_mcp_crud.py -q`.

### Task 4: MemoryPanel CRUD UI

**Files:**
- Modify: `frontend/src/components/MemoryPanel.tsx`
- Modify: `frontend/src/lib/api.ts`

- [x] Load memories with the current user id.
- [x] Add edit and delete controls.
- [x] Show provenance and supersede metadata.
- [x] Wire eval button to `/api/memory/metrics/run-eval`.
- [x] Run lint diagnostics on edited frontend files.

### Task 5: Regression

- [x] Run `python3 -m pytest tests/test_recall_eval.py tests/test_rerank.py tests/test_store_schema.py tests/test_write_pipeline.py tests/test_mcp_crud.py tests/test_mcp_tools.py -q --tb=short`.
- [x] Run targeted CRUD/Judge/conflict tests.
- [x] Update docs if behavior differs from spec.
