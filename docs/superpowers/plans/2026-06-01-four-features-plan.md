# MemoryAgent 四大特性实现计划

> **目标:** 实现流式响应、向量搜索、错误重试、多 Agent 协作

---

## Task 1: 实现流式响应 (Streaming)

**Files:**
- Create: `src/agent/streaming.py`
- Modify: `src/backend/api/chat.py`
- Modify: `src/agent/loop.py`
- Create: `tests/test_streaming.py`

**目标:**
1. 实现 Token 级流式输出
2. 实现工具调用流式通知
3. 支持 SSE (Server-Sent Events)
4. 前端实时显示

**接口设计:**
```python
class StreamEvent:
    type: str  # "token", "tool_call", "tool_result", "error", "done"
    content: str
    metadata: Dict[str, Any]

class StreamingManager:
    async def stream_response(self, generator) -> AsyncGenerator[str, None]:
        yield f"data: {json.dumps(event)}\n\n"
```

**测试:**
- test_streaming_creates_events
- test_streaming_handles_token
- test_streaming_handles_tool_call
- test_streaming_handles_error

---

## Task 2: 实现向量搜索 (Vector Search)

**Files:**
- Create: `src/memory/vector_store.py`
- Modify: `src/memory/retrieval.py`
- Create: `tests/test_vector_store.py`

**目标:**
1. 实现向量嵌入存储
2. 实现语义相似度搜索
3. 与现有 LLM 检索集成
4. 支持 FAISS 或内存向量存储

**接口设计:**
```python
class VectorStore:
    def add(self, id: str, text: str, metadata: Dict) -> None
    def search(self, query: str, top_k: int = 5) -> List[Dict]
    def delete(self, id: str) -> None

class HybridRetriever:
    async def retrieve(self, query: str, user_id: str, limit: int) -> List[Dict]:
        # 1. 向量搜索
        # 2. LLM 检索
        # 3. 合并排序
```

**测试:**
- test_vector_store_adds_embedding
- test_vector_store_searches_similar
- test_hybrid_retriever_combines_results

---

## Task 3: 实现错误重试机制 (Error Retry)

**Files:**
- Create: `src/agent/retry.py`
- Modify: `src/agent/loop.py`
- Create: `tests/test_retry.py`

**目标:**
1. 实现指数退避重试
2. 实现断路器模式
3. 支持可配置重试策略
4. 集成到 Agent Loop

**接口设计:**
```python
class RetryPolicy:
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    exponential_base: float = 2.0

class CircuitBreaker:
    failure_threshold: int = 5
    recovery_timeout: float = 60.0

class RetryManager:
    async def execute_with_retry(self, func, policy: RetryPolicy) -> Any
```

**测试:**
- test_retry_succeeds_on_first_try
- test_retry_retries_on_failure
- test_retry_exponential_backoff
- test_circuit_breaker_opens_on_failures

---

## Task 4: 实现多 Agent 协作 (Multi-Agent)

**Files:**
- Create: `src/agent/multi_agent.py`
- Create: `src/agent/subagent.py`
- Create: `tests/test_multi_agent.py`

**目标:**
1. 实现 Agent 间通信
2. 实现任务委派
3. 实现角色定义
4. 支持 Orchestrator-Worker 模式

**接口设计:**
```python
class AgentRole:
    name: str
    capabilities: List[str]
    system_prompt: str

class SubAgent:
    def __init__(self, role: AgentRole, llm_service)
    async def execute(self, task: str) -> str

class MultiAgentOrchestrator:
    def __init__(self, agents: List[SubAgent])
    async def delegate(self, task: str, agent_name: str) -> str
    async def coordinate(self, task: str) -> str
```

**测试:**
- test_subagent_executes_task
- test_orchestrator_delegates_task
- test_multi_agent_coordination

---

## 执行顺序

1. Task 1: 流式响应 (独立，不影响其他)
2. Task 2: 向量搜索 (独立，不影响其他)
3. Task 3: 错误重试 (独立，不影响其他)
4. Task 4: 多 Agent 协作 (依赖 Task 3 的重试机制)

---

## 验证标准

所有任务完成后：
- 所有测试通过
- 没有 lint 错误
- 代码符合项目风格
- 文档更新
