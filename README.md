# MemoryAgent

<div align="center">

🧠 **本地记忆侧车 — 让 Cursor / Claude Code 越用越懂你**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14.1-black.svg)](https://nextjs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-400+-brightgreen.svg)](#测试)

**每次新会话都要重讲偏好？MemoryAgent 做长期记忆与可解释召回，Coding Agent 专注写代码——分工清晰、数据留在本地。**

[核心优势](#核心优势) • [功能亮点](#功能亮点) • [快速开始](#快速开始) • [架构设计](#架构设计) • [API 文档](#api-文档)

</div>

---

## 演示

<div align="center">
  <img src="docs/marketing/demo.svg" alt="MemoryAgent Demo" width="100%">
</div>

**场景 1**: 用户告诉 AI 自己的偏好 → AI 记住

**场景 2**: 新对话 → AI 自动使用记忆，用 Python 写排序函数

---

## 核心优势

### 1. 定位清晰：记忆侧车，不抢 Coding Agent 的活

不做终端、Git、浏览器自动化；专注 **Remember + Align**。与 [Cursor](https://cursor.com) / Claude Code **互补**：它们执行，MemoryAgent 记住你是谁、项目禁忌与决策。

### 2. 本地可控、人类可读

- 记忆 = **Markdown + YAML**，可用 Obsidian 直接改
- 默认 **本地文件 + SQLite**，无强制云向量库
- 可选 `MEMORYAGENT_API_KEY` 保护 HTTP 侧车

### 3. 召回靠谱且可解释

- **FTS + 持久向量 + Rerank**（候选 20 → Top5），长问句 **Query Rewrite**
- 对话展示 **Memory Citation**（分数、类型、陈旧提示）
- **L0→L1 证据链**：原子记忆可追溯到原会话片段（`memories/l0/`）
- **Recall@5** 黄金集评估 + CI 门禁（目标 ≥90%）

### 4. 接 Cursor 接近「零配置」

```bash
bash /path/to/MemoryAgent/scripts/install-sidecar.sh .
```

自动写入 `.cursor/mcp.json`、规则「每轮先 recall」、`user_id` / `project_id` 由 **工作区 + Git 仓库名** 推导。MCP v2：`recall` / `store` / `update` / `delete` / `list` / `export`。

### 5. 上下文更省 Token（借鉴 Headroom / Tencent 思路）

- **CCR 可逆压缩**：大段 tool 输出 落盘 + 类型化预览（JSON 骨架 / 代码截断），`memory_retrieve_blob` 按需取回
- **Mermaid 符号化工作记忆**：多步 tool 时注入任务拓扑图
- 五层 **ContextCompressor**，异步 **记忆沉淀**（不拖慢首包/尾包）

### 6. 工程可验证

400+ pytest、流式 SSE、多厂商 LLM 配置、架构决策文档化 → 适合二次开发与私有化部署。

---

## 功能亮点

### 🧠 四类型记忆系统

不只是简单的"记住对话"，而是结构化的认知记忆：

| 类型 | 用途 | 示例 |
|------|------|------|
| **用户画像** | 你的偏好、角色、知识水平 | "我喜欢 Python" |
| **行为反馈** | AI 该做什么、不该做什么 | "不要用 mock 数据库" |
| **项目动态** | 截止日期、重要决策 | "周五前完成 API" |
| **外部引用** | 去哪找什么信息 | "Grafana 看板地址" |

### 🔄 跨会话记忆共享

```
会话 1: 用户喜欢 Python，讨厌 Java
会话 2: 帮我写排序 → AI 自动用 Python（记住你的偏好）
会话 3: 推荐框架 → AI 推荐 FastAPI（知道你喜欢 Python）
```

### 🗜️ 智能上下文压缩

多层策略，兼顾 **省 Token** 与 **可恢复**：

| 机制 | 作用 |
|------|------|
| CCR + ContentRouter | 大 tool/JSON/日志：预览进上下文，全文 `ccr_*` 落盘 |
| Mermaid 任务图 | 多步 tool 时保留拓扑，细节按节点 ID 取回 |
| 5 层 ContextCompressor | 磁盘卸载 → 裁剪 → 折叠 → 摘要 |
| 异步 Observer | 对话后自动写入记忆，不阻塞流式 `done` |

详见 [Headroom 思路对照](docs/headroom-integration.md)、[架构决策](docs/architecture-decision.md)。

### 🔌 MCP 记忆侧车 v2

| 工具 | 用途 |
|------|------|
| `memory_recall` | 按 query 召回（`user_id` 可省略） |
| `memory_store` / `update` / `delete` | 沉淀与纠错 |
| `memory_list` / `memory_export` | 浏览与 `prompt_block` 注入 |
| `memory_retrieve_blob` | CCR 压缩后取回完整 tool 输出 |

### 📊 质量可观测

- `GET /api/memory/metrics` — Recall@5、误注入率、向量条数
- `POST /api/memory/metrics/run-eval` — 重跑黄金集

### 📝 Obsidian 兼容

记忆以 Markdown 文件存储，可直接在 Obsidian 中编辑：

```yaml
---
name: user_abc123
description: 用户偏好
type: user
tags:
  - preference
  - python
---
#preference #python

用户喜欢 Python，讨厌 Java
```

### 🔧 15+ 大模型支持

一键切换，无需改代码：

| 厂商 | 模型 |
|------|------|
| OpenAI | GPT-4, GPT-4o, o3, o4-mini |
| 阿里云百炼 | qwen-max, qwen-plus, deepseek-v4-pro |
| 小米 MiMo | mimo-v2.5-pro, mimo-v2.5 |
| 智谱 GLM | glm-5.1, glm-5, glm-4-plus |
| DeepSeek | deepseek-v4-pro, deepseek-r1 |
| 月之暗面 | kimi-k2, kimi-k2-mini |
| 字节豆包 | doubao-seed-1-8-251228 |
| 更多... | OpenRouter, 自定义 API |

---

## 与常见方案对比

| 维度 | ChatGPT 记忆 | Cursor Rules | 仅向量记忆库 | **MemoryAgent** |
|------|-------------|--------------|--------------|-----------------|
| 跨会话偏好 | 黑盒 | 项目规则 | 碎片难检索 | ✅ 四类型结构化 |
| 可编辑 | ❌ | 部分 | 难 | ✅ Markdown / Obsidian |
| 召回可解释 | ❌ | 有限 | 弱 | ✅ Citation + L0 溯源 |
| 接外部 Agent | ❌ | IDE 内置 | 需自建 | ✅ MCP + HTTP 侧车 |
| 大上下文/tool 输出 | 提供商压缩 | 部分 | — | ✅ CCR + Mermaid + 五层压缩 |
| 本地/隐私 | ❌ | 视配置 | 视部署 | ✅ 默认本地 |
| 写代码/跑 CI | — | ✅ | — | ❌ 刻意不做 |

**适合**：长期偏好、项目禁忌、可审计记忆、Cursor/Claude Code 用户。  
**不适合**：替代 Devin/Cursor 完成端到端交付。

---

## 快速开始

### 方式一：一键安装（推荐）

**macOS:**
```bash
# 下载 DMG 安装包
open https://github.com/jaychouya/MemoryAgent/releases
```

**Windows:**
```powershell
# 下载 ZIP 安装包
Start-Process "https://github.com/jaychouya/MemoryAgent/releases"
```

### 方式二：从源码运行

```bash
# 克隆仓库
git clone https://github.com/jaychouya/MemoryAgent.git
cd MemoryAgent

# 安装后端依赖
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 安装前端依赖
cd frontend && npm install && cd ..

# 启动
python src/main.py
```

访问 http://localhost:3000，点击「配置」按钮设置 API Key。

### 方式三：Cursor / Claude Code 侧车（一条命令）

在**你的业务项目**目录执行（将路径换成本仓库位置）：

```bash
bash /path/to/MemoryAgent/scripts/install-sidecar.sh .
```

自动写入 `.cursor/mcp.json`、规则「每轮先 `memory_recall` 再回答」、记忆目录 `.memoryagent/memories/`。`user_id` / `project_id` 由工作区与 **Git 仓库名** 自动推导。详见 [Cursor 接入](docs/cursor-integration.md)。

### 系统要求

- Python 3.11+
- Node.js 18+
- 网络连接（用于 API 调用）

---

## 架构设计

**运行时主路径**：会话历史 `sessions/*.json` + 长期记忆 `memories/*.md` + `index.db`（FTS + 持久向量）。`src/memory/layers/` 下 Redis/PostgreSQL 实现仅用于测试与未来扩展，见 [架构决策](docs/architecture-decision.md)。

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
│  │  │ LLM调用 │→│ 工具执行 │→│ Hybrid召回 │→│ CCR+压缩   │   │   │
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
│   ├── prompts/             # 动态 System Prompt
│   ├── context/             # 上下文压缩
│   ├── semantic/            # 语义化代码理解
│   └── reflection/          # 执行轨迹抽象
├── memory/                  # 记忆系统
│   ├── types/               # 四类型记忆定义
│   ├── storage.py           # 文件存储 (markdown + YAML)
│   ├── retrieval.py         # Hybrid FTS + 向量 + Rerank
│   ├── provenance.py        # L0 证据链
│   ├── persistent_vector.py # 持久化向量
│   ├── quality.py           # 记忆质量管理
│   └── vector_store.py      # 向量搜索
├── skills/                  # 技能知识图谱
└── backend/                 # 后端服务
    ├── main.py              # FastAPI 入口
    └── api/                 # API 路由
```

---

## API 文档

### 发送消息

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "我喜欢 Python", "session_id": "test", "user_id": "user1"}'
```

### 快速配置

```bash
curl -X POST http://localhost:8000/api/config/quick-setup \
  -H "Content-Type: application/json" \
  -d '{"provider": "openai", "api_key": "your-key"}'
```

### 获取记忆

```bash
curl http://localhost:8000/api/memory/stats
```

更多 API 文档访问：http://localhost:8000/docs

---

## 测试

```bash
# 运行所有测试
python -m pytest tests/ -v

# 测试结果
# 400+ passed, 7 skipped
```

---

## 技术栈

| 层级 | 技术 |
|------|------|
| **前端** | Next.js 14, TypeScript, Tailwind CSS |
| **后端** | Python 3.9, FastAPI, OpenAI SDK |
| **记忆** | Markdown + YAML, SQLite, 向量搜索 |
| **图谱** | networkx, tree-sitter |
| **测试** | pytest, 400+ 测试用例 |

---

## 贡献

欢迎贡献！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/your-feature`)
3. 提交更改 (`git commit -m 'Add your feature'`)
4. 推送到分支 (`git push origin feature/your-feature`)
5. 创建 Pull Request

---

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 相关文档

- [架构决策](docs/architecture-decision.md) — 侧车边界与读写路径
- [Cursor 接入](docs/cursor-integration.md) — 一条命令安装 MCP
- [Headroom 思路对照](docs/headroom-integration.md) — CCR 与可选 proxy

## 致谢

- [Claude Code](https://www.anthropic.com/) — Agent Loop / 记忆类型灵感
- [TencentDB Agent Memory](https://github.com/TencentCloud/TencentDB-Agent-Memory) — 分层记忆与证据链思路
- [Headroom](https://github.com/chopratejas/headroom) — 可逆上下文压缩思路
- [FastAPI](https://fastapi.tiangolo.com/) · [Next.js](https://nextjs.org/) · [tree-sitter](https://tree-sitter.github.io/) · [networkx](https://networkx.org/)

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给个 Star！⭐**

[![Star History Chart](https://api.star-history.com/svg?repos=jaychouya/MemoryAgent&type=Date)](https://star-history.com/#jaychouya/MemoryAgent&Date)

</div>
