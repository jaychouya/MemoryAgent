# Recall Quality, Conflict Resolution, and Memory CRUD Design

## Goal

Improve MemoryAgent's core memory loop across three gaps:

- Recall quality: reduce wrong recall, missed recall, and stale memory injection.
- Automatic conflict handling: expire outdated memories when a newer preference or fact supersedes them.
- User correction loop: let users view, edit, and delete memories from the UI.

This keeps MemoryAgent focused as a local memory sidecar: Remember + Align, not Act + Perceive.

## Scope

In scope:

- Add a local, rule-based `RecallJudge`.
- Add lightweight automatic conflict detection during memory store.
- Expand MemoryPanel with list, edit, delete, provenance, and eval actions.
- Add tests for recall filtering, automatic supersede, and CRUD lifecycle.

Out of scope:

- LLM-based judging by default.
- Graph database or Zep-style full temporal graph.
- Batch background cleanup jobs.
- Multi-tenant SaaS administration.

## Approach

Use a local-first pipeline:

1. Existing hybrid retrieval produces candidates.
2. Rerank keeps the strongest candidates.
3. `RecallJudge` applies explicit rules and returns visible reasons.
4. Store path checks same-scope memories for obvious replacement patterns.
5. UI exposes the resulting state so users can correct mistakes.

## A. Recall Judge

Add `src/memory/recall_judge.py`.

Inputs:

- `query`
- candidate memory rows
- optional `user_id`
- optional `project_id`

Outputs per memory:

- `judge_score`
- `judge_reason`
- `dropped_reason`

Rules:

- Drop memories with `superseded_by`.
- Drop memories outside `user_id` / `project_id` scope.
- Boost query keyword and CJK bigram overlap.
- Boost `feedback` and `user` memories for preference queries.
- Penalize stale low-overlap memories.
- Preserve `reference` memories when query asks where/link/docs/path.

Integration:

- Call after hybrid/rerank in `MemoryRetrieval.retrieve()`.
- Return judge fields in citations and sidecar export.

## B. MemoryPanel CRUD

Extend `frontend/src/components/MemoryPanel.tsx`.

Features:

- List memories by current user/project.
- Edit `content` and `description`.
- Delete memory.
- Show `source_quote`, `source_session_id`, `superseded_by`, `valid_until`, `judge_reason`.
- Run eval from the panel.

API usage:

- `GET /api/memories`
- `PATCH /api/memories/{memory_id}`
- `DELETE /api/memories/{memory_id}`
- `POST /api/memory/metrics/run-eval`

Backend gaps to close:

- Ensure update/delete verify memory ownership before mutation.
- Ensure list returns provenance and supersede metadata.

## C. Automatic Conflict Detection

Add lightweight conflict detection in the store path.

Trigger only for same:

- `user_id`
- `project_id` when present
- `memory_type`

Replacement signals:

- "现在", "改成", "不再", "以后", "主要使用"
- English equivalents: "now", "instead", "no longer", "prefer", "mainly use"

Behavior:

- If a new memory overlaps the old memory topic but contains replacement signals, mark old memory:
  - `superseded_by`
  - `valid_until`
  - `conflict_reason`
- Remove old memory vector from active vector search.
- Do not delete old Markdown files.

Safety:

- Only auto-supersede high-confidence conflicts.
- Low-confidence conflicts stay active and can be corrected in UI.

## Testing

Add or extend tests:

- `RecallJudge` drops superseded memories.
- `RecallJudge` keeps relevant Chinese preference memories.
- Scope mismatch memories are dropped.
- Store path auto-supersedes "Python" after "now mainly use Rust".
- MemoryPanel API lifecycle: list, patch, delete.
- Existing Memory Eval still passes.

## Success Criteria

- Recall@5 remains >= 0.9.
- false_inject_rate remains <= 0.05.
- Superseded memories do not enter prompt blocks.
- User can correct a bad memory without editing Markdown manually.
- No LLM call is required for the default path.
