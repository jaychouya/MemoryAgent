# Cursor / Claude Code 接入（近零配置）

## 一条命令安装（推荐）

在 **你的项目目录** 执行（`MemoryAgent` 为本仓库绝对路径）：

```bash
bash /path/to/MemoryAgent/scripts/install-sidecar.sh .
# Claude Code 同时写 .mcp.json：
bash /path/to/MemoryAgent/scripts/install-sidecar.sh . --claude
```

自动完成：

| 产物 | 作用 |
|------|------|
| `.cursor/mcp.json` | Cursor 项目级 MCP，无需手抄 example |
| `.cursor/rules/memory-sidecar.mdc` | 侧车 prompt：权威层级 + 行动前检查（每轮最多 recall 一次） |
| `.memoryagent/memories/` | 记忆落在当前仓库，可 Git 忽略 |

安装后：**重载 Cursor MCP** 或重启 IDE。

## 自动推导（不用手填 user_id）

MCP 进程环境：

- `MEMORYAGENT_WORKSPACE_DIR` → 当前打开的项目根目录
- `user_id` / `project_id` 默认 = **工作区文件夹名**（可覆盖见下）

工具调用示例：

```
memory_recall(query="用户当前问题")
memory_store(content="用户讨厌 mock 数据库", memory_type="feedback")
```

可选覆盖：

```bash
export MEMORYAGENT_USER_ID=my-team
export MEMORYAGENT_PROJECT_ID=my-repo
```

## MCP Server 内置说明

`python3 -m src.mcp_server.server` 启动后，MCP `instructions` 含：

1. **权威层级**：已注入记忆优先于主观假设
2. **行动前检查**：上下文已有记忆块 → 禁止重复 `memory_recall`
3. 未覆盖时再 `memory_recall`（每轮最多一次）
4. 回答后按需 `memory_store`；整段上下文用 `memory_export` → `prompt_block`

详见 [memory-os-layer7-adaptation.md](memory-os-layer7-adaptation.md)。

## 工具（v2）

| 工具 | 用途 |
|------|------|
| `memory_recall` | 按 query 召回（`user_id` 可选） |
| `memory_store` | 写入四类型记忆 |
| `memory_update` / `memory_delete` | 纠错、遗忘 |
| `memory_list` | 浏览 |
| `memory_export` | sidecar-v2 `prompt_block` |

## 插件清单（仓库内）

`integrations/cursor/plugin.json` — 描述与安装命令，供团队文档或后续上架 Cursor 市场。

## 手动配置（备选）

仅当无法运行安装脚本时，合并 `mcp-config.example.json`，并设置：

```json
"env": {
  "MEMORYAGENT_STORAGE_DIR": "/your/project/.memoryagent/memories",
  "MEMORYAGENT_WORKSPACE_DIR": "/your/project"
}
```

## HTTP 鉴权（可选）

```bash
export MEMORYAGENT_API_KEY=your-secret
```

请求头：`X-API-Key: your-secret`（仅 HTTP API，MCP stdio 不走此鉴权）
