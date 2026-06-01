# MemoryAgent

<div align="center">

🧠 **具备认知记忆架构的 AI Agent，让 AI 记住你的偏好，越用越懂你**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14.1-black.svg)](https://nextjs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[功能特性](#功能特性) • [架构设计](#架构设计) • [快速开始](#快速开始) • [API文档](#api文档) • [测试](#测试)

</div>

---

## 📖 项目简介

MemoryAgent 是一个具备**认知记忆架构**的智能 AI Agent，让 AI 记住你的偏好，越用越懂你。

### 🎯 核心特性

- **四类型记忆系统** - 用户画像、行为反馈、项目动态、外部引用
- **跨会话记忆共享** - 记住你的偏好，下次对话继续使用
- **基于 Claude Code 的 Agent Loop 架构** - 智能决策循环
- **支持 15+ 大模型** - OpenAI、百炼、小米MiMo、智谱等

---

## ✨ 功能特性

### 🧠 Agent Loop (智能决策循环)

```python
while True:
    1. 压缩上下文 (5步策略)
    2. 调用 LLM API
    3. If end_turn → break
    4. 执行工具调用
    5. 更新状态 → continue
```

### 📚 四类型记忆系统

| 类型 | 用途 | 示例 |
|------|------|------|
| **用户画像 (User)** | 用户偏好、角色、知识水平 | "我喜欢Python" |
| **行为反馈 (Feedback)** | 该做什么、不该做什么 | "不要用mock数据库" |
| **项目动态 (Project)** | 截止日期、重要决策 | "周五前完成API" |
| **外部引用 (Reference)** | 去哪找什么信息 | "Grafana看板地址" |

### 🗜️ 五步上下文压缩

1. **大结果存磁盘** - 工具结果 >50KB 存盘，保留预览
2. **清理旧消息** - 移除过时的对话开头
3. **裁剪老工具输出** - 时间衰减，清理可重新获取的结果
4. **上下文折叠** - 90% 阈值触发，动态压缩视图
5. **全量摘要** - 95% 阈值触发，生成结构化摘要

### 🔧 语义化代码理解

使用 tree-sitter 进行 AST 解析，实现代码的语义匹配：

```python
from src.agent.semantic import SemanticPatcher

patcher = SemanticPatcher()
result = patcher.find_and_replace(
    file_content="def hello():\n    print('world')",
    old_pattern="def hello():\n    print('world')",
    new_pattern="def greet():\n    print('greet')",
    language="python"
)
```

### 📊 技能知识图谱

基于 networkx 构建技能图谱，支持：
- 前置条件匹配 (框架、Node版本、数据库类型)
- 依赖关系追踪
- 成功/失败反馈学习
- 跨项目技能迁移

### 🔄 执行轨迹自动抽象

自动从执行轨迹中发现可复用模式，生成技能初稿：

```python
from src.agent.reflection import ExecutionTracer, SkillGenerator

tracer = ExecutionTracer()
generator = SkillGenerator()

# 记录执行轨迹
tracer.start_trace("Deploy to Vercel")
tracer.record_tool_call("npm", {"args": "install"}, result)
tracer.record_tool_call("vercel", {"args": "deploy"}, result)
tracer.end_trace(success=True)

# 自动生成技能
skills = generator.generate_from_traces(tracer.get_traces())
```

---

## 🏗️ 架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                        前端 (Next.js + Tailwind)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │  ChatPanel   │  │ MemoryPanel  │  │   SettingsPanel      │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Agent 核心引擎 (FastAPI)                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    Agent Loop                              │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐   │   │
│  │  │ LLM调用 │→│ 工具执行 │→│ 记忆检索 │→│ 上下文压缩  │   │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────────┘   │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐      │
│  │ 工具注册表    │  │ 记忆管理器    │  │ 技能图谱         │      │
│  │ (11个工具)    │  │ (4类型记忆)   │  │ (networkx)       │      │
│  └──────────────┘  └──────────────┘  └──────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

### 核心模块

```
src/
├── agent/                    # Agent 核心
│   ├── loop.py              # Agent Loop (while true 循环)
│   ├── tools/               # 工具系统
│   │   ├── base.py          # 工具基类
│   │   ├── registry.py      # 工具注册表
│   │   ├── builtin.py       # 内置工具
│   │   └── advanced.py      # 高级工具
│   ├── prompts/             # 动态 System Prompt
│   │   ├── sections.py      # Prompt Section 定义
│   │   └── assembler.py     # 动态组装器
│   ├── context/             # 上下文压缩
│   ├── semantic/            # 语义化代码理解
│   │   ├── parser.py        # AST 解析器 (tree-sitter)
│   │   ├── matcher.py       # AST 匹配器
│   │   └── patcher.py       # 语义 Patcher
│   ├── reflection/          # 执行轨迹抽象
│   │   ├── tracer.py        # 轨迹记录器
│   │   ├── analyzer.py      # 序列分析器
│   │   └── generator.py     # 技能生成器
│   └── plans/               # Plan Mode
├── memory/                  # 记忆系统
│   ├── types/               # 四类型记忆定义
│   ├── storage.py           # 文件存储 (markdown + YAML)
│   ├── retrieval.py         # LLM-based 召回
│   └── exclusions.py        # 排除规则
├── skills/                  # 技能知识图谱
│   ├── node.py              # 技能节点
│   ├── graph.py             # 图谱 (networkx)
│   └── matcher.py           # 技能匹配器
└── backend/                 # 后端服务
    ├── main.py              # FastAPI 入口
    ├── api/                 # API 路由
    └── services/            # LLM 服务
```

---

## 🚀 快速开始

### 环境要求

- Python 3.9+
- Node.js 18+
- npm 或 yarn

### 安装步骤

1. **克隆仓库**
```bash
git clone https://github.com/yourusername/memoryai.git
cd memoryai
```

2. **后端设置**
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

3. **前端设置**
```bash
cd frontend
npm install
cd ..
```

4. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，添加你的 API Key
```

5. **启动服务**
```bash
# 启动后端 (终端1)
source venv/bin/activate
uvicorn src.backend.main:app --host 0.0.0.0 --port 8000 --reload

# 启动前端 (终端2)
cd frontend
npm run dev
```

6. **访问应用**
- 前端界面: http://localhost:3000
- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

---

## 📡 API 文档

### 对话 API

```bash
# 发送消息
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "你好", "session_id": "test", "user_id": "user1"}'
```

### 配置 API

```bash
# 保存模型配置
curl -X POST http://localhost:8000/api/config \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "your-api-key",
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-4"
  }'
```

### 会话管理

```bash
# 获取会话列表
curl http://localhost:8000/api/sessions?user_id=demo-user

# 删除会话
curl -X DELETE http://localhost:8000/api/sessions/{session_id}
```

### 记忆统计

```bash
# 获取记忆统计
curl http://localhost:8000/api/memory/stats
```

---

## 🧪 测试

### 运行测试

```bash
# 运行所有测试
source venv/bin/activate
python -m pytest tests/ -v

# 运行特定测试
python -m pytest tests/test_semantic_patch.py -v
python -m pytest tests/test_skill_graph.py -v
python -m pytest tests/test_trace_to_skill.py -v
```

### 测试覆盖

```
tests/test_api.py             - 4 tests   ✅ API 测试
tests/test_config.py          - 4 tests   ✅ 配置测试
tests/test_decision_engine.py - 7 tests   ✅ 决策引擎测试
tests/test_embedding.py       - 4 tests   ✅ 向量化测试
tests/test_memory_manager.py  - 4 tests   ✅ 记忆管理测试
tests/test_models.py          - 7 tests   ✅ 模型测试
tests/test_semantic_patch.py  - 14 tests  ✅ 语义补丁测试
tests/test_short_term_memory.py - 3 tests ✅ 短期记忆测试
tests/test_skill_graph.py     - 15 tests  ✅ 技能图谱测试
tests/test_trace_to_skill.py  - 12 tests  ✅ 执行轨迹测试
tests/test_working_memory.py  - 5 tests   ✅ 工作记忆测试
----------------------------------------------
Total: 79 tests passed
```

---

## 🛠️ 技术栈

### 后端

| 技术 | 用途 |
|------|------|
| Python 3.9+ | 主要语言 |
| FastAPI | Web 框架 |
| OpenAI SDK | LLM 调用 |
| tree-sitter | AST 解析 |
| networkx | 知识图谱 |
| Redis | 工作记忆 (可选) |

### 前端

| 技术 | 用途 |
|------|------|
| Next.js 14 | React 框架 |
| TypeScript | 类型安全 |
| Tailwind CSS | 样式系统 |

### 支持的 LLM 厂商

| 厂商 | 模型 |
|------|------|
| OpenAI | GPT-4, GPT-4.1, o3, o4-mini |
| 百炼 (阿里云) | qwen-max, qwen-plus, deepseek-v4-pro |
| 小米 (MiMo) | mimo-v2.5-pro, mimo-v2.5 |
| 智谱 (GLM) | glm-5.1, glm-5, glm-4-plus |
| DeepSeek | deepseek-v4-pro, deepseek-r1 |
| 月之暗面 (Kimi) | kimi-k2, kimi-k2-mini |
| 字节 (豆包) | doubao-seed-1-8-251228 |
| MiniMax | MiniMax-M2.7, MiniMax-M2.5 |
| 讯飞 (星火) | spark-5.0-ultra |
| 零一万物 (Yi) | yi-lightning, yi-large |
| 硅基流动 | Qwen/Qwen3-235B-A22B |
| OpenRouter | 多模型聚合 |
| 自定义 | 任何 OpenAI 兼容 API |

---

## 📁 项目结构

```
memoryai/
├── src/                          # 源代码
│   ├── agent/                    # Agent 核心
│   ├── memory/                   # 记忆系统
│   ├── skills/                   # 技能图谱
│   └── backend/                  # 后端服务
├── frontend/                     # 前端代码
│   ├── src/
│   │   ├── app/                  # Next.js 页面
│   │   └── components/           # React 组件
│   └── package.json
├── tests/                        # 测试文件
├── docs/                         # 文档
├── memories/                     # 记忆存储
├── skills/                       # 技能存储
├── traces/                       # 执行轨迹
├── requirements.txt              # Python 依赖
├── pyproject.toml                # 项目配置
└── README.md                     # 本文件
```

---

## 🔧 配置

### 环境变量

创建 `.env` 文件：

```env
# OpenAI
OPENAI_API_KEY=your-openai-api-key

# 百炼 (阿里云)
DASHSCOPE_API_KEY=your-dashscope-api-key

# 小米 MiMo
XIAOMI_API_KEY=your-xiaomi-api-key

# 智谱
ZHIPU_API_KEY=your-zhipu-api-key
```

### 模型配置

在前端界面点击「配置」按钮，选择厂商并填写 API Key 即可。

---

## 🤝 贡献

欢迎贡献！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/your-feature`)
3. 提交更改 (`git commit -m 'Add your feature'`)
4. 推送到分支 (`git push origin feature/your-feature`)
5. 创建 Pull Request

### 开发规范

- 遵循 PEP 8 代码规范
- 添加单元测试
- 更新文档
- 使用中文注释

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

- [Claude Code](https://www.anthropic.com/) - 架构设计灵感
- [FastAPI](https://fastapi.tiangolo.com/) - Web 框架
- [Next.js](https://nextjs.org/) - 前端框架
- [tree-sitter](https://tree-sitter.github.io/) - AST 解析
- [networkx](https://networkx.org/) - 图数据库

---

## 📧 联系方式

如有问题或建议，请创建 [Issue](https://github.com/yourusername/memoryai/issues)

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给个 Star！⭐**

</div>
