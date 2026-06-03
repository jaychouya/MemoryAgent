# 记忆信任可解释 + 记忆质量（A+C）实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让用户看见记忆引用与 Recall 指标（A），并持久化向量 + 对话后自动写回（C）。

**Architecture:** 结构化 `MemoryCitation` 贯穿 AgentLoop→API→前端；向量写入 SQLite `memory_vectors` 表；`MemoryObserver` 在 chat 结束后规则提取写回。Spec: [2026-06-03-trust-and-memory-quality-design.md](../specs/2026-06-03-trust-and-memory-quality-design.md)

**Tech Stack:** Python 3.9+, FastAPI, SQLite, numpy, Next.js, pytest

---

## Task A1: MemoryCitation 模型与构建器

**Files:**
- Create: `src/memory/citations.py`
- Test: `tests/test_memory_citations.py`

- [ ] **Step 1: 失败测试** — `build_citations` 从 retrieve dict 生成带 score/type/id 的列表
- [ ] **Step 2: 实现** `MemoryCitation` dataclass + `build_citations(results, reason)`
- [ ] **Step 3: pytest 通过**

---

## Task A2: AgentLoop 与 Chat API 输出 citations

**Files:**
- Modify: `src/agent/loop.py` — `AgentState.memories_used` 改为 citations
- Modify: `src/backend/api/chat.py` — `ChatResponse.memory_citations`, SSE done metadata
- Test: `tests/test_api.py` — 断言 `memory_citations` 字段

- [ ] **Step 1: 更新 loop retrieve 后调用 `build_citations`**
- [ ] **Step 2: `_memory_updates_from_result` 兼容 + 新字段**
- [ ] **Step 3: `/chat/stream` done 事件带 citations**
- [ ] **Step 4: 测试通过**

---

## Task A3: ChatPanel 记忆引用 UI

**Files:**
- Modify: `frontend/src/components/ChatPanel.tsx`

- [ ] **Step 1: 解析 `memory_citations` / SSE metadata**
- [ ] **Step 2: 折叠卡片 UI（类型、score、陈旧警告）**
- [ ] **Step 3: 无 citation 时显示「未使用记忆」**

---

## Task A4: Recall 评估与 metrics API

**Files:**
- Create: `tests/fixtures/golden_memories.json`
- Create: `src/memory/eval.py`
- Modify: `src/backend/api/memory.py` — `GET /memory/metrics`, `POST /memory/metrics/run-eval`
- Test: `tests/test_recall_eval.py`, `tests/test_api_memory_metrics.py`

- [ ] **Step 1: 黄金集 fixture（≥10 cases）**
- [ ] **Step 2: `run_recall_eval` 实现**
- [ ] **Step 3: API 端点**
- [ ] **Step 4: 断言 recall_at_5 >= 0.9**

---

## Task A5: MemoryPanel 指标 Tab

**Files:**
- Modify: `frontend/src/components/MemoryPanel.tsx`

- [ ] **Step 1: 拉取 `/api/memory/metrics`**
- [ ] **Step 2: 展示 Recall@5、误注入率、重跑按钮**

---

## Task C1: PersistentVectorStore

**Files:**
- Create: `src/memory/persistent_vector.py`
- Modify: `src/memory/index.py` — 建表 migration
- Modify: `src/memory/manager.py` — 启动加载、store/delete 同步
- Test: `tests/test_persistent_vector_store.py`

- [ ] **Step 1: `memory_vectors` 表 + blob 读写**
- [ ] **Step 2: 启动 load + backfill**
- [ ] **Step 3: 重启后检索 E2E 仍命中**

---

## Task C2: MemoryObserver 自动写回

**Files:**
- Create: `src/memory/observer.py`
- Modify: `src/backend/api/chat.py` — `_execute_chat` 结束后调用 observer
- Test: `tests/test_memory_observer.py`

- [ ] **Step 1: 规则提取（喜欢/讨厌/记住/不要用）**
- [ ] **Step 2: 去重 + should_exclude**
- [ ] **Step 3: E2E「我喜欢 Kotlin」→ 下轮 retrieve 命中**

---

## Task C3: 集成验证

**Files:**
- Test: `tests/test_memory_cross_session_e2e.py`（扩展重启场景）

- [ ] **Step 1: 全量 `pytest tests/test_memory_* tests/test_recall_* tests/test_persistent_* tests/test_api*`**
- [ ] **Step 2: 更新 `docs/architecture-decision.md` Success metrics 为「已实现评估入口」**

---

## 建议执行顺序

```
A1 → A2 → C1 → C2 → A4 → A3 → A5 → C3
```

C1 在 A4 前完成，确保 eval 测的是持久向量路径。
