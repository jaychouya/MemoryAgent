# MemoryAgent：不绑 Cursor 的长期记忆层

## 它是什么

**独立运行的记忆系统** + 可选接入任意客户端：

- 打开网页就能聊（自带对话体）
- 任意 MCP 宿主（Cursor、Claude、Cline…）
- HTTP API 给自研软件、机器人

记忆全是本地 Markdown，一套数据多端共用。

## 三种上手方式

### 1. 只要对话（最简单）

```bash
git clone https://github.com/jaychouya/MemoryAgent.git
cd MemoryAgent && pip install -r requirements.txt
cd frontend && npm i && cd .. && make dev
```

浏览器打开 → 配 API Key → 开聊。不需要 Cursor。

### 2. 给 IDE / Agent 加记忆

```bash
bash MemoryAgent/scripts/onboard.sh /你的项目
```

支持 Cursor、Claude Code 等 MCP 客户端。

### 3. 接到自己的 App

启动后端 `uvicorn src.backend.main:app`，调 `/api/chat/stream` 和 `/api/memory/*`。

## 和 Mem0 比

| | MemoryAgent | Mem0 |
|---|-------------|------|
| 独立 UI | ✅ | 偏云 |
| 任意 MCP | ✅ | SDK |
| 自研 HTTP | ✅ | ✅ |
| 本地 Markdown | ✅ | 弱 |

## 仓库

https://github.com/jaychouya/MemoryAgent

有用请 Star，欢迎 Issue 说你用什么客户端接入。
