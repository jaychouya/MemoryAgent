# Headroom 思路对照与集成

[Headroom](https://github.com/chopratejas/headroom) 专注 **进 LLM 前的上下文压缩**；MemoryAgent 专注 **跨会话长期记忆**。互补，不替代。

## 已内置（无需安装 headroom-ai）

| Headroom 能力 | MemoryAgent 实现 |
|---------------|------------------|
| ContentRouter（按类型压缩） | `src/agent/content_router.py` — JSON 骨架 / 代码截断 / 文本首尾 |
| CCR 可逆压缩 | `src/agent/ccr_store.py` — `memories/ccr_blobs/ccr_*.txt` |
| tool 输出瘦身 | `query_loop` + `ContextCompressor` Layer1 |
| MCP 按需取回 | `memory_retrieve_blob(ref_id)` |

配置：

```bash
CCR_ENABLED=true
CCR_OFFLOAD_THRESHOLD=8192   # 超过则落盘+预览
CCR_PREVIEW_CHARS=4096
CCR_STORAGE_DIR=memories
```

压缩后的 tool 消息尾部含 `ref=ccr_…`，Agent 可调用 `memory_retrieve_blob` 取全文。

## 可选：外挂 Headroom（更强压缩）

需要 60–95% 极限压缩时，可与侧车并行：

```bash
pip install "headroom-ai[proxy]"
headroom proxy --port 8787
# 将 Agent 的 LLM base_url 指向 proxy
```

侧车仍负责 `memory_recall` / `memory_store`；Headroom 负责 **单次请求上下文**。

## 分工

- **MemoryAgent**：记住偏好、项目事实、可解释 citation、L0 证据链  
- **Headroom**：单次任务里的大段 log/JSON/文件内容压缩  
- **符号化 Mermaid**（本仓库）：多步 tool 的任务拓扑（Tencent D 方案）
