# 第一性原理 × 竞品对照 × 优化路线

<!-- markdownlint-disable MD060 -->

## 1. 第一性原理：Agent 记忆到底解决什么？

无状态 LLM 只有 **context window**，没有 **跨会话状态**。记忆层的本质任务：

| 原子问题 | 成功标准 |
|----------|----------|
| **写入** | 从噪声对话中提取可复用事实，且不污染主链路延迟 |
| **存储** | 人类可审计、可纠错、可迁移 |
| **召回** | 当前意图相关、不过期、可解释「为何注入」 |
| **失效** | 偏好/事实变更时能 supersede，而非堆叠矛盾条目 |

MemoryAgent 的边界：**Remember + Align**，不替代 Coding Agent 的 **Act + Perceive**。

---

## 2. 市面同类产品（2026）

| 产品 | 架构 | 强项 | 弱项 / 与我们的差异 |
|------|------|------|---------------------|
| **Mem0** | 向量为主 + Pro 图 | 接入最快、生态大、多租户 | 云依赖、记忆黑盒、难 Obsidian 编辑 |
| **Zep / Graphiti** | 时序知识图 | 「此刻为真」、状态变迁、LongMemEval 高 | 商用为主、自托管重、非 Markdown 侧车 |
| **Letta (MemGPT)** | 自编辑 core memory | 长时自治 Agent | 重运行时，非「外挂记忆」 |
| **ChatGPT Memory** | 产品内黑盒 | 零配置 | 不可导出、不可审计、无项目 scope |
| **Cursor Rules** | 静态规则文件 | 项目约束 | 非动态召回、无对话沉淀 |
| **Headroom** | 上下文 CCR 代理 | 单次请求省 60–95% Token | 无跨会话用户模型 |

---

## 3. MemoryAgent 差异化（应守住）

1. **本地 Markdown 侧车** — 记忆 = 文件，不是只有 embedding
2. **四类型用户模型** — 比「一条 fact 一条向量」更可编排
3. **MCP 零配置** — `install-sidecar.sh` + workspace/git scope
4. **可解释召回** — Citation + L0 证据链（对标 Zep 的 audit，但更轻）
5. **CCR + Mermaid** — 对标 Headroom/Tencent 的「工作记忆」，但内置于侧车

---

## 4. 差距与已做优化（本轮）

### P0（已修）

| 问题 | 竞品通常怎么做 | 我们的修复 |
|------|----------------|------------|
| HTTP 读 `memories/`，MCP 写 `.memoryagent/` | 单一 storage endpoint | `default_storage_dir()` 统一 `MEMORYAGENT_STORAGE_DIR` |
| MCP 每次 new Manager | 连接池 / 单例 | `tools.get_manager` 按目录缓存 |
| 向量全局扫描 | metadata filter | `VectorStore.search(user_id=…)` |
| 中文关键词弱 | 分词 / 图遍历 | index 二字 gram OR 匹配 |
| Query rewrite 80–120 字无效 | LLM 压缩 query | 去掉「≤max_len 直接返回」 |
| UI 固定 demo-user | 与 IDE scope 一致 | `ChatPanel` 用 `getUserId()` |

### P1（本轮继续优化）

| 差距 | 对标 | 建议 |
|------|------|------|
| **时序失效** | Zep valid_until | ✅ 显式 `supersedes`：旧记忆写入 `superseded_by` / `valid_until`，召回过滤失效项 |
| **召回裁判器** | Mem0/Zep 二阶段检索 | ✅ `RecallJudge` 本地规则裁判：过滤失效/越权记忆，输出 `judge_score` / `judge_reason` |
| **记忆 CRUD UI** | Mem0 dashboard | ✅ MemoryPanel 支持 list / edit / delete / provenance / eval |
| **Eval 污染生产库** | Mem0 独立 tenant | ✅ `/memory/metrics/run-eval` 使用临时 `storage_dir` |
| **MCP store 无 provenance** | Zep episode | ✅ `memory_store` 支持 `source_session_id` / `source_turn` / `source_quote` |
| **自动冲突检测** | Zep valid_until | ✅ 同 scope 高置信替换自动写 `superseded_by` / `valid_until` / `conflict_reason` |
| **LLM extract 阈值** | Mem0 每轮 extract | 已降 `MEMORY_EXTRACT_LLM_MIN_CHARS` 200；可再加类型感知 |

### P2（规模化再考虑）

- 启用 Redis/PG/Chroma 四层（见 `architecture-decision.md` Deferred）
- `MemorySelector` LLM 二阶段精选（默认仍保持本地规则，避免额外成本）
- Rerank embedding 缓存
- SOC2 / 多租户计费（若做 SaaS）

---

## 5. 选型建议（给用户）

| 你的场景 | 选谁 |
|----------|------|
| Cursor 项目、要本地可改记忆 | **MemoryAgent** |
| 快速 SaaS、不管可解释性 | Mem0 Cloud |
| 金融/客服「当时为真」 | Zep |
| 7×24 自治 Agent | Letta |
| 只压单次上下文 | Headroom proxy + MemoryAgent MCP |

**推荐组合**：MemoryAgent（长期记忆）+ Cursor（执行）+ 可选 Headroom proxy（极限 CCR）。

---

## 6. 北极星指标（继续盯）

- Recall@5 ≥ 90%（黄金集）
- false_inject_rate ≤ 5%
- 3 轮内可见 Citation
- MCP 安装 → 首次 recall < 2s（冷启动后）
