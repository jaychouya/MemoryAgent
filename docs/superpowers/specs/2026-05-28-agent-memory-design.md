# Agent Memory System Design Spec

## 1. 项目概述

### 1.1 项目名称
**MemoMind** - 具有认知记忆架构的个人AI助手

### 1.2 项目定位
一个能"越用越懂你"的个人AI助手，通过仿人类记忆模型（工作记忆→短期记忆→长期记忆→情景记忆）实现真正的个性化服务，并提供完整的记忆可解释性和用户控制能力。

### 1.3 核心价值
- **对用户**：AI助手能记住你的偏好、习惯、历史，提供真正个性化的服务
- **对技术官**：展示对Agent记忆架构、自主性边界、可信AI的深度思考
- **对面试**：可交互的Demo + 完整产品思维，能讲清楚设计决策和技术权衡

### 1.4 目标用户
- 需要长期AI助手的个人用户
- 希望AI能记住自己偏好的重度用户
- 关注隐私和数据控制的技术用户

## 2. 架构设计

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      用户界面层 (Next.js)                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  对话界面    │  │ 记忆浏览器   │  │  偏好/设置面板      │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Agent核心引擎 (Python FastAPI)              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              记忆管理器 (Memory Manager)                  ││
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌─────────┐ ││
│  │  │ 工作记忆   │→│ 短期记忆   │→│ 长期记忆   │→│情景记忆 │ ││
│  │  │ (Redis)   │ │ (PG+向量) │ │ (向量库)   │ │(图结构) │ ││
│  │  └───────────┘ └───────────┘ └───────────┘ └─────────┘ ││
│  └─────────────────────────────────────────────────────────┘│
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ 自主决策引擎  │  │  工具调用层   │  │  可解释性模块    │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    基础设施层                                 │
│     Redis  │  PostgreSQL  │  Chroma向量库  │  OpenAI/Zhipu  │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 技术栈

| 层级 | 技术选型 | 理由 |
|------|---------|------|
| 前端 | Next.js 14 + TypeScript + Tailwind CSS | 成熟生态，SSR支持，开发效率高 |
| 后端 | Python 3.11 + FastAPI | 异步支持好，类型提示，文档自动生成 |
| Agent框架 | LangChain + LangGraph | 成熟的Agent编排，支持复杂工作流 |
| 工作记忆 | Redis | 高性能KV存储，支持TTL自动过期 |
| 短期记忆 | PostgreSQL + pgvector | 关系型存储+向量检索，事务支持 |
| 长期记忆 | Chroma / Milvus | 专业的向量数据库，支持元数据过滤 |
| 情景记忆 | NetworkX + PostgreSQL | 图结构存储事件关系，PG持久化 |
| LLM | OpenAI GPT-4 / Zhipu GLM-4 | 主力推理模型，支持中文 |
| 嵌入 | OpenAI text-embedding-3-small | 高质量向量化 |

### 2.3 目录结构

```
memo-mind/
├── src/
│   ├── backend/
│   │   ├── main.py              # FastAPI入口
│   │   ├── api/
│   │   │   ├── chat.py          # 对话API
│   │   │   ├── memory.py        # 记忆管理API
│   │   │   └── settings.py      # 设置API
│   │   ├── models/
│   │   │   ├── message.py       # 消息模型
│   │   │   ├── memory.py        # 记忆模型
│   │   │   └── user.py          # 用户模型
│   │   └── services/
│   │       ├── llm_service.py   # LLM调用封装
│   │       └── tool_service.py  # 工具调用服务
│   ├── memory/
│   │   ├── manager.py           # 记忆管理器主类
│   │   ├── layers/
│   │   │   ├── working.py       # 工作记忆层
│   │   │   ├── short_term.py    # 短期记忆层
│   │   │   ├── long_term.py     # 长期记忆层
│   │   │   └── episodic.py      # 情景记忆层
│   │   ├── consolidation.py     # 记忆整合/迁移
│   │   ├── forgetting.py        # 遗忘机制
│   │   └── retrieval.py         # 记忆检索
│   ├── agent/
│   │   ├── core.py              # Agent核心
│   │   ├── decision.py          # 自主决策引擎
│   │   ├── tools/
│   │   │   ├── base.py          # 工具基类
│   │   │   ├── search.py        # 搜索工具
│   │   │   └── memory_tool.py   # 记忆操作工具
│   │   └── prompts/
│   │       ├── system.py        # 系统提示词
│   │       └── templates.py     # 提示词模板
│   ├── explainability/
│   │   ├── tracer.py            # 决策追踪器
│   │   ├── visualizer.py        # 记忆可视化
│   │   └── report.py            # 解释报告生成
│   └── utils/
│       ├── config.py            # 配置管理
│       ├── embedding.py         # 向量化工具
│       └── logger.py            # 日志工具
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx         # 主页面
│   │   │   ├── layout.tsx       # 布局
│   │   │   └── globals.css      # 全局样式
│   │   ├── components/
│   │   │   ├── ChatPanel.tsx    # 对话面板
│   │   │   ├── MemoryBrowser.tsx # 记忆浏览器
│   │   │   ├── MemoryGraph.tsx  # 记忆图谱可视化
│   │   │   ├── SettingsPanel.tsx # 设置面板
│   │   │   └── ExplainPanel.tsx # 解释面板
│   │   ├── hooks/
│   │   │   └── useMemory.ts     # 记忆相关hook
│   │   └── lib/
│   │       └── api.ts           # API客户端
│   ├── package.json
│   └── next.config.js
├── tests/
│   ├── test_memory_layers.py    # 记忆层测试
│   ├── test_consolidation.py    # 整合测试
│   ├── test_retrieval.py        # 检索测试
│   └── test_agent.py            # Agent测试
├── docs/
│   └── superpowers/specs/       # 设计文档
├── docker-compose.yml           # 容器编排
├── requirements.txt             # Python依赖
└── README.md                    # 项目说明
```

## 3. 四层记忆模型详细设计

### 3.1 工作记忆 (Working Memory)

**人类类比**：当前在想什么，正在处理的信息

**存储内容**：
- 当前对话的上下文窗口
- 当前正在执行的任务状态
- 临时缓存的检索结果

**技术实现**：
```python
class WorkingMemory:
    def __init__(self, redis_client, ttl=3600):
        self.redis = redis_client
        self.ttl = ttl  # 1小时过期
    
    async def get_context(self, session_id: str) -> List[Message]:
        """获取当前会话上下文"""
        key = f"working:{session_id}"
        context = await self.redis.get(key)
        return json.loads(context) if context else []
    
    async def add_message(self, session_id: str, message: Message):
        """添加消息到工作记忆"""
        key = f"working:{session_id}"
        context = await self.get_context(session_id)
        context.append(message.to_dict())
        # 保持最近20条消息
        if len(context) > 20:
            context = context[-20:]
        await self.redis.setex(key, self.ttl, json.dumps(context))
```

**关键特性**：
- 高速读写（Redis内存存储）
- 自动过期（TTL机制）
- 容量限制（滑动窗口）

### 3.2 短期记忆 (Short-term Memory)

**人类类比**：昨天发生了什么，近期的事情

**存储内容**：
- 对话摘要（每轮对话的压缩版本）
- 待办事项和提醒
- 临时偏好（最近在关注什么）

**技术实现**：
```python
class ShortTermMemory:
    def __init__(self, db_session, embedding_service):
        self.db = db_session
        self.embedder = embedding_service
    
    async def store_summary(self, user_id: str, summary: ConversationSummary):
        """存储对话摘要"""
        # 生成嵌入向量
        embedding = await self.embedder.embed(summary.content)
        
        memory = ShortTermMemoryRecord(
            user_id=user_id,
            content=summary.content,
            embedding=embedding,
            memory_type="conversation_summary",
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=30),
            importance_score=summary.importance
        )
        self.db.add(memory)
        await self.db.commit()
    
    async def search(self, user_id: str, query: str, top_k=5) -> List[Memory]:
        """语义搜索短期记忆"""
        query_embedding = await self.embedder.embed(query)
        
        results = await self.db.execute(
            select(ShortTermMemoryRecord)
            .where(ShortTermMemoryRecord.user_id == user_id)
            .where(ShortTermMemoryRecord.expires_at > datetime.now())
            .order_by(
                ShortTermMemoryRecord.embedding.cosine_distance(query_embedding)
            )
            .limit(top_k)
        )
        return results.scalars().all()
```

**关键特性**：
- 语义检索（向量相似度）
- 自动过期（时间衰减）
- 重要性评分（影响保留优先级）

### 3.3 长期记忆 (Long-term Memory)

**人类类比**：我的习惯、稳定偏好、学到的知识

**存储内容**：
- 用户画像（年龄、职业、兴趣等）
- 稳定偏好（喜欢的食物、常去的地方）
- 学习到的模式（用户的行为规律）

**技术实现**：
```python
class LongTermMemory:
    def __init__(self, chroma_client, embedding_service):
        self.collection = chroma_client.get_or_create_collection("long_term")
        self.embedder = embedding_service
    
    async def store(self, user_id: str, memory: LongTermMemoryItem):
        """存储长期记忆"""
        embedding = await self.embedder.embed(memory.content)
        
        self.collection.add(
            ids=[memory.id],
            embeddings=[embedding],
            documents=[memory.content],
            metadatas=[{
                "user_id": user_id,
                "category": memory.category,
                "confidence": memory.confidence,
                "last_accessed": datetime.now().isoformat(),
                "access_count": 0
            }]
        )
    
    async def retrieve(self, user_id: str, query: str, top_k=10) -> List[Memory]:
        """检索相关长期记忆"""
        query_embedding = await self.embedder.embed(query)
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where={"user_id": user_id}
        )
        
        # 更新访问计数
        for memory_id in results['ids'][0]:
            self._update_access(memory_id)
        
        return self._parse_results(results)
```

**关键特性**：
- 持久化存储
- 高维向量检索
- 元数据过滤
- 访问频率追踪

### 3.4 情景记忆 (Episodic Memory)

**人类类比**：特殊经历、重要事件、关键时刻

**存储内容**：
- 重要事件（生日、纪念日、关键决策）
- 情感标记（用户当时的情绪状态）
- 事件关联（这个事件和哪些其他事件有关）

**技术实现**：
```python
class EpisodicMemory:
    def __init__(self, db_session, embedding_service):
        self.db = db_session
        self.embedder = embedding_service
        self.graph = nx.DiGraph()  # 内存中的图结构
    
    async def store_episode(self, user_id: str, episode: Episode):
        """存储情景记忆"""
        # 1. 存储到数据库
        embedding = await self.embedder.embed(episode.description)
        
        db_episode = EpisodicMemoryRecord(
            user_id=user_id,
            episode_id=episode.id,
            description=episode.description,
            embedding=embedding,
            emotional_state=episode.emotion,
            importance=episode.importance,
            timestamp=episode.timestamp
        )
        self.db.add(db_episode)
        
        # 2. 更新图结构
        self.graph.add_node(episode.id, **episode.to_dict())
        
        # 3. 建立与已有事件的关联
        related_episodes = await self._find_related(user_id, episode)
        for related in related_episodes:
            self.graph.add_edge(episode.id, related.id, 
                              relation=related.relation_type)
        
        await self.db.commit()
    
    async def recall_by_emotion(self, user_id: str, emotion: str) -> List[Episode]:
        """按情感状态回忆"""
        results = await self.db.execute(
            select(EpisodicMemoryRecord)
            .where(EpisodicMemoryRecord.user_id == user_id)
            .where(EpisodicMemoryRecord.emotional_state == emotion)
            .order_by(EpisodicMemoryRecord.importance.desc())
        )
        return results.scalars().all()
```

**关键特性**：
- 图结构存储事件关系
- 情感标记支持
- 重要性排序
- 关联推理

## 4. 自主决策引擎设计

### 4.1 决策边界定义

Agent的自主性需要明确的边界，这是可信AI的核心：

```python
class DecisionBoundary:
    """定义Agent可以自主决策的范围"""
    
    # 可以自主执行（不需要询问用户）
    AUTONOMOUS = [
        "memory_search",        # 搜索记忆
        "context_retrieval",    # 获取上下文
        "response_generation",  # 生成回复
        "memory_consolidation", # 整合记忆
    ]
    
    # 需要确认后执行（重要操作）
    CONFIRM_REQUIRED = [
        "memory_delete",        # 删除记忆
        "preference_update",    # 更新偏好
        "external_api_call",    # 调用外部API
        "file_operation",       # 文件操作
    ]
    
    # 禁止自主执行（必须用户明确指示）
    FORBIDDEN = [
        "financial_transaction", # 金融交易
        "personal_data_export",  # 导出个人数据
        "account_modification",  # 修改账户
    ]
```

### 4.2 决策流程

```python
class DecisionEngine:
    def __init__(self, memory_manager, llm_service):
        self.memory = memory_manager
        self.llm = llm_service
        self.boundary = DecisionBoundary()
    
    async def decide(self, user_input: str, context: Dict) -> Decision:
        """核心决策流程"""
        
        # 1. 意图识别
        intent = await self._classify_intent(user_input)
        
        # 2. 检查决策边界
        boundary_type = self.boundary.get_type(intent)
        
        if boundary_type == "FORBIDDEN":
            return Decision(
                action="refuse",
                reason="此操作需要用户明确授权",
                suggestion="请直接告诉我您想做什么"
            )
        
        if boundary_type == "CONFIRM_REQUIRED":
            # 收集相关信息，但不执行
            info = await self._gather_info(intent, context)
            return Decision(
                action="confirm",
                info=info,
                question=f"我准备执行：{intent.description}，确认吗？"
            )
        
        # 3. 自主执行
        if boundary_type == "AUTONOMOUS":
            # 检索相关记忆
            relevant_memories = await self.memory.retrieve(
                query=user_input,
                user_id=context['user_id']
            )
            
            # 生成执行计划
            plan = await self._make_plan(intent, relevant_memories, context)
            
            return Decision(
                action="execute",
                plan=plan,
                memories_used=relevant_memories
            )
```

### 4.3 自主性展示

在Demo中，用户可以：
1. 调整每个操作的自主性级别
2. 查看Agent的决策日志
3. 回滚Agent的自主决策

## 5. 可解释性模块设计

### 5.1 记忆追溯

```python
class MemoryTracer:
    """追踪Agent使用了哪些记忆来做出决策"""
    
    async def trace(self, decision: Decision) -> Explanation:
        """生成决策解释"""
        
        explanation = Explanation(
            decision=decision.action,
            timestamp=datetime.now(),
            factors=[]
        )
        
        # 1. 列出使用的记忆
        for memory in decision.memories_used:
            explanation.factors.append({
                "type": "memory",
                "content": memory.content,
                "source": memory.source,
                "confidence": memory.confidence,
                "how_obtained": memory.retrieval_method
            })
        
        # 2. 说明决策逻辑
        explanation.reasoning = await self._explain_reasoning(decision)
        
        # 3. 提供反事实：如果没有这些记忆，会怎样？
        explanation.counterfactual = await self._generate_counterfactual(decision)
        
        return explanation
```

### 5.2 可视化界面

前端提供：
1. **记忆图谱**：可视化Agent记住了什么，以及记忆之间的关联
2. **决策日志**：每次决策的完整追溯
3. **记忆来源**：每个记忆是如何获得的（用户主动告诉/Agent推断/从对话中提取）

## 6. 前端界面设计

### 6.1 主要页面

1. **对话页面**：与Agent对话，右侧面板显示实时记忆使用情况
2. **记忆浏览器**：浏览、搜索、编辑Agent的记忆
3. **设置面板**：调整自主性边界、隐私设置、遗忘策略

### 6.2 核心组件

```typescript
// 记忆浏览器组件
const MemoryBrowser = () => {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [activeLayer, setActiveLayer] = useState<string>('all');
  
  return (
    <div className="memory-browser">
      {/* 记忆层选择器 */}
      <LayerSelector 
        layers={['working', 'short-term', 'long-term', 'episodic']}
        active={activeLayer}
        onChange={setActiveLayer}
      />
      
      {/* 记忆列表 */}
      <MemoryList 
        memories={memories}
        onEdit={handleEdit}
        onDelete={handleDelete}
      />
      
      {/* 记忆图谱可视化 */}
      <MemoryGraph 
        memories={memories}
        onSelect={handleSelect}
      />
    </div>
  );
};
```

## 7. 数据流设计

### 7.1 对话流程

```
用户输入
    ↓
意图识别
    ↓
决策边界检查
    ↓
记忆检索（工作→短期→长期→情景）
    ↓
上下文组装
    ↓
LLM生成回复
    ↓
记忆更新（提取新记忆、更新旧记忆）
    ↓
返回响应 + 记忆使用说明
```

### 7.2 记忆整合流程

```
定时任务触发（每小时）
    ↓
扫描短期记忆（过期、重要性低）
    ↓
评估是否值得保留
    ↓
如果值得 → 提炼核心信息 → 存入长期记忆
    ↓
删除已整合的短期记忆
    ↓
更新记忆统计
```

## 8. API设计

### 8.1 对话API

```python
# POST /api/chat
{
    "message": "我喜欢吃川菜",
    "session_id": "abc123"
}

# Response
{
    "response": "好的，我记住了你喜欢吃川菜。下次推荐餐厅时会优先考虑川菜馆。",
    "memory_updates": [
        {
            "type": "preference",
            "content": "喜欢川菜",
            "layer": "short-term",
            "action": "created"
        }
    ],
    "decision_explanation": {
        "action": "store_preference",
        "confidence": 0.95,
        "reasoning": "用户明确表达了饮食偏好"
    }
}
```

### 8.2 记忆管理API

```python
# GET /api/memories?layer=long-term&category=food
# PUT /api/memories/{memory_id}
# DELETE /api/memories/{memory_id}
# POST /api/memories/search
```

## 9. 非功能需求

### 9.1 性能
- 对话响应时间 < 2秒
- 记忆检索时间 < 500ms
- 支持10万条记忆的检索

### 9.2 隐私
- 所有数据本地存储（可选云同步）
- 用户可随时导出/删除所有记忆
- 记忆加密存储

### 9.3 可扩展性
- 记忆层可插拔（可以添加新的记忆类型）
- LLM可替换（支持OpenAI/智谱/本地模型）
- 工具可扩展（添加新工具只需实现接口）

## 10. 演示场景

### 场景1：记忆的形成
用户："我喜欢喝美式咖啡，不要太热"
Agent记住了这个偏好，下次推荐咖啡时自动考虑

### 场景2：记忆的检索
用户："我上次说想买的那个耳机是什么来着？"
Agent从情景记忆中检索到相关对话

### 场景3：记忆的遗忘
用户可以查看Agent的记忆，手动删除不想保留的

### 场景4：决策可解释
用户问："你为什么推荐这家餐厅？"
Agent展示：因为你3月说喜欢川菜 + 上周说想尝试新店 + 这家评分高

---

**文档版本**: v1.0
**创建日期**: 2026-05-28
**作者**: MemoMind Team
