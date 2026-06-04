# MemoryAgent

<div align="center">

🧠 **让 ChatGPT 记住你是谁 — 具备认知记忆架构的 AI Agent**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14.1-black.svg)](https://nextjs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-370+-brightgreen.svg)](#测试)

**每次开新对话都要重新介绍自己？MemoryAgent 让 AI 记住你的偏好，越用越懂你。**

[功能亮点](#功能亮点) • [快速开始](#快速开始) • [为什么选择 MemoryAgent](#为什么选择-memoryagent) • [架构设计](#架构设计) • [API 文档](#api-文档)

</div>

---

## 演示

<div align="center">
  <img src="docs/marketing/demo.svg" alt="MemoryAgent Demo" width="100%">
</div>

**场景 1**: 用户告诉 AI 自己的偏好 → AI 记住

**场景 2**: 新对话 → AI 自动使用记忆，用 Python 写排序函数

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

5 步压缩策略，解决长对话"忘记前面说过什么"的问题：
- 大结果存磁盘
- 清理旧消息
- 裁剪老工具输出
- 上下文折叠（90% 阈值）
- 全量摘要（95% 阈值）

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

## 为什么选择 MemoryAgent

MemoryAgent 是 **记忆侧车（Memory Sidecar）**，不是全能 coding agent。与 Cursor / Claude Code 搭配使用，或单独作为「越用越懂你」的本地助手。

| 维度 | ChatGPT 记忆 | Cursor Rules | MemoryAgent |
|------|-------------|--------------|-------------|
| 跨会话偏好 | 产品内黑盒 | 项目级规则 | ✅ 四类型用户模型 |
| 记忆可编辑 | ❌ | 部分（规则文件） | ✅ Obsidian Markdown |
| 本地/隐私 | ❌ | 视配置 | ✅ 默认本地文件 |
| 召回可解释 | ❌ | 有限 | ✅ 显示用到的记忆 |
| 接外部 Agent | ❌ | 内置 IDE | ✅ `/api/memory/export` + `/api/memory/recall` |
| 写代码/跑终端 | — | ✅ | ❌（刻意不做，见 [架构决策](docs/architecture-decision.md)） |

**适合**：需要长期一致偏好、禁忌、项目决策记录的用户。  
**不适合**：替代 Cursor/Devin 完成修 bug、提 PR、跑 CI 等执行任务。

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
│   ├── prompts/             # 动态 System Prompt
│   ├── context/             # 上下文压缩
│   ├── semantic/            # 语义化代码理解
│   └── reflection/          # 执行轨迹抽象
├── memory/                  # 记忆系统
│   ├── types/               # 四类型记忆定义
│   ├── storage.py           # 文件存储 (markdown + YAML)
│   ├── retrieval.py         # LLM-based 召回
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
# 290+ passed, 7 skipped
```

---

## 技术栈

| 层级 | 技术 |
|------|------|
| **前端** | Next.js 14, TypeScript, Tailwind CSS |
| **后端** | Python 3.9, FastAPI, OpenAI SDK |
| **记忆** | Markdown + YAML, SQLite, 向量搜索 |
| **图谱** | networkx, tree-sitter |
| **测试** | pytest, 290+ 测试用例 |

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

## 致谢

- [Claude Code](https://www.anthropic.com/) - 架构设计灵感
- [FastAPI](https://fastapi.tiangolo.com/) - Web 框架
- [Next.js](https://nextjs.org/) - 前端框架
- [tree-sitter](https://tree-sitter.github.io/) - AST 解析
- [networkx](https://networkx.org/) - 图数据库

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给个 Star！⭐**

[![Star History Chart](https://api.star-history.com/svg?repos=jaychouya/MemoryAgent&type=Date)](https://star-history.com/#jaychouya/MemoryAgent&Date)

</div>
