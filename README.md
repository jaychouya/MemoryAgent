# MemoMind

Personal AI Assistant with Cognitive Memory Architecture

## Overview

MemoMind is a personal AI assistant that uses a four-layer memory system inspired by human cognition:

- **Working Memory**: Current session context (Redis)
- **Short-term Memory**: Recent conversations and temporary info (PostgreSQL)
- **Long-term Memory**: Stable preferences and knowledge (Chroma)
- **Episodic Memory**: Important events and experiences (PostgreSQL + Graph)

## Architecture

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
```

## Tech Stack

- **Backend**: Python 3.11 + FastAPI
- **Frontend**: Next.js 14 + TypeScript + Tailwind CSS
- **Database**: Redis + PostgreSQL + Chroma
- **LLM**: OpenAI GPT-4 / Zhipu GLM-4
- **Agent Framework**: LangChain + LangGraph

## Project Structure

```
memo-mind/
├── src/
│   ├── backend/
│   │   ├── main.py              # FastAPI入口
│   │   ├── api/
│   │   │   ├── chat.py          # 对话API
│   │   │   └── memory.py        # 记忆管理API
│   │   └── models/
│   │       ├── message.py       # 消息模型
│   │       └── memory.py        # 记忆模型
│   ├── memory/
│   │   ├── manager.py           # 记忆管理器
│   │   └── layers/
│   │       ├── working.py       # 工作记忆层
│   │       └── short_term.py    # 短期记忆层
│   ├── agent/
│   │   └── decision.py          # 决策引擎
│   └── utils/
│       ├── config.py            # 配置管理
│       └── embedding.py         # 向量化服务
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx         # 主页面
│   │   │   └── layout.tsx       # 布局
│   │   └── components/
│   │       └── ChatPanel.tsx    # 对话组件
│   └── package.json
├── tests/
│   ├── test_working_memory.py
│   ├── test_short_term_memory.py
│   ├── test_memory_manager.py
│   ├── test_decision_engine.py
│   └── test_api.py
├── docs/
│   └── superpowers/
│       ├── specs/               # 设计文档
│       └── plans/               # 实现计划
├── requirements.txt
└── README.md
```

## Key Features

### 1. Four-Layer Memory Architecture
- **Working Memory**: Redis-based, high-speed, auto-expiring
- **Short-term Memory**: PostgreSQL with vector search
- **Long-term Memory**: Chroma vector database
- **Episodic Memory**: Graph-based event relationships

### 2. Autonomous Decision Engine
- Clear boundaries for autonomous actions
- User confirmation for important operations
- Forbidden actions for safety

### 3. Memory Explainability
- Decision tracing
- Memory source tracking
- Confidence scoring

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- Redis
- PostgreSQL

### Installation

1. **Backend Setup**
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. **Frontend Setup**
```bash
cd frontend
npm install
```

3. **Environment Variables**
```bash
cp .env.example .env
# Edit .env with your API keys
```

### Running the Application

1. **Start Backend**
```bash
uvicorn src.backend.main:app --reload
```

2. **Start Frontend**
```bash
cd frontend
npm run dev
```

3. **Access the Application**
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

## API Endpoints

### Chat API
- `POST /api/chat` - Send a message and get response

### Memory API
- `GET /api/memories` - List memories
- `DELETE /api/memories/{memory_id}` - Delete a memory

## Demo Scenarios

### Scenario 1: Memory Formation
User: "I like coffee, not too hot"
Agent remembers the preference, considers it for future recommendations

### Scenario 2: Memory Retrieval
User: "What was that headphone I mentioned?"
Agent retrieves from episodic memory

### Scenario 3: Decision Explanation
User: "Why did you recommend this restaurant?"
Agent shows: "Because you said you like Sichuan food in March + wanted to try new places last week + this one has high ratings"

## Contributing

This project is designed for interview demonstration. Key areas for extension:

1. **Add Long-term Memory Layer** (Chroma integration)
2. **Add Episodic Memory Layer** (Graph database)
3. **Implement Memory Consolidation** (Automatic memory migration)
4. **Add LLM Integration** (Real intent classification)
5. **Build Memory Visualization** (Interactive memory graph)

## License

MIT

---

**Built for AI Product Manager & Agent Developer interviews**
