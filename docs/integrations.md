# 接入方式总览

MemoryAgent 是**独立记忆层**，不绑定 Cursor。同一套记忆可被多种客户端读写。

## 三种用法（选一或组合）

| 用法 | 适合谁 | 入口 |
|------|--------|------|
| **独立对话** | 不想装 IDE，要自带聊天 + 记忆面板 | `make dev` → Web 控制台 |
| **MCP 侧车** | 任意支持 MCP 的 Agent（Cursor、Claude Code、Cline、Windsurf…） | `scripts/onboard.sh` 或下方通用配置 |
| **HTTP API** | 自研 App、脚本、飞书/钉钉机器人、LangChain 等 | `POST /v1/chat/completions`、`/api/chat/stream` |

记忆落盘：`MEMORYAGENT_STORAGE_DIR`（默认项目下 `.memoryagent/memories/`），**所有接入方式共用同一目录**。

---

## 1. 独立对话（Web 控制台）

```bash
git clone https://github.com/jaychouya/MemoryAgent.git && cd MemoryAgent
pip install -r requirements.txt
cd frontend && npm install && cd ..
make dev
```

浏览器打开终端提示的地址，配置模型 API Key 后即可聊天；右侧面板管理记忆、导出、飞书/钉钉通知。

无需 Cursor / MCP。

---

## 2. MCP（任意 MCP 宿主）

### Cursor / 项目级（推荐）

```bash
bash /path/to/MemoryAgent/scripts/onboard.sh /path/to/your/project
```

### Claude Code

```bash
bash /path/to/MemoryAgent/scripts/install-sidecar.sh /path/to/project --claude
```

### 通用 MCP 配置

任何能读 `mcp.json` 的客户端，添加：

```json
{
  "mcpServers": {
    "memoryagent": {
      "command": "python3",
      "args": ["-m", "src.mcp_server.server"],
      "cwd": "/absolute/path/to/MemoryAgent",
      "env": {
        "MEMORYAGENT_STORAGE_DIR": "/absolute/path/to/.memoryagent/memories",
        "MEMORYAGENT_WORKSPACE_DIR": "/absolute/path/to/your/project"
      }
    }
  }
}
```

工具：`memory_recall` / `memory_store` / `memory_update` / `memory_delete` / `memory_list` / `memory_export`。

验证：`bash scripts/verify-sidecar.sh --storage /path/to/.memoryagent/memories`

---

## 3. HTTP API（任意软件）

Base URL 默认 `http://localhost:8000`（先 `python -m uvicorn src.backend.main:app` 或 `make dev`）。

### OpenAI 兼容（SDK 零改）

```python
from openai import OpenAI
client = OpenAI(base_url="http://localhost:8000/v1", api_key="optional-if-set")
r = client.chat.completions.create(
    model="memoryagent",
    messages=[{"role": "user", "content": "记住我喜欢 Python"}],
    user="alice",  # 映射为 memory user_id
)
```

| 端点 | 说明 |
|------|------|
| `POST /v1/chat/completions` | OpenAI 格式，支持 `stream: true` |
| `GET /v1/models` | 返回 `memoryagent` |

扩展字段：`session_id`（可选，会话隔离）。

### 原生 API

| 能力 | 端点 |
|------|------|
| 流式对话 + 记忆注入 | `POST /api/chat/stream` |
| 召回 | `POST /api/memory/recall` |
| 写入 / 列表 / 删除 | `/api/memories/*` |
| 导出 prompt 块 | `GET /api/memory/export` |
| 健康与 scope | `GET /api/sidecar/health` |

可选鉴权：环境变量 `MEMORYAGENT_API_KEY`，请求头 `X-API-Key` 或 `Authorization: Bearer`。

---

## 4. IM 入站 Webhook（飞书 / 钉钉）

**出站**（已有）：对话沉淀后推送到群机器人 Webhook。  
**入站**（新增）：用户在群里 @ 机器人发消息 → MemoryAgent 对话 → 同 Webhook 回覆。

### 配置步骤

1. 设置页「飞书/钉钉」保存 **出站 Webhook**（与通知共用）
2. 在飞书开放平台 / 钉钉机器人配置 **事件回调 URL**：
   - 飞书：`POST http://<你的主机>:8000/api/webhooks/feishu`
   - 钉钉：`POST http://<你的主机>:8000/api/webhooks/dingtalk`
3. （推荐）设置入站密钥：
   - 环境变量 `MEMORYAGENT_WEBHOOK_INBOUND_TOKEN=your-secret`
   - 回调 URL 加 `?token=your-secret`
4. 飞书事件订阅：连接时可在凭证里填 `verification_token`（与平台「Verification Token」一致）

### 本地测试

```bash
curl -X POST 'http://localhost:8000/api/webhooks/feishu/test-inbound?token=your-secret' \
  -H 'Content-Type: application/json' \
  -d '{"text":"你好","user_id":"u1","session_id":"s1"}'
```

需先连接对应平台的出站 Webhook，测试接口才会把回复发回群里。

---

## 选型建议

```
要自带 UI、最快体验        → 独立对话（make dev）
已在用某 IDE 的 Agent      → MCP 侧车（onboard.sh）
要嵌入自己的产品           → HTTP API
```

---

## 相关文档

- [Cursor / Claude Code 细节](cursor-integration.md)
- [架构决策](architecture-decision.md)
- [竞品与定位](competitive-first-principles.md)
