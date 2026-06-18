# MemoryAgent Growth Playbook（C 方案：国内先行 + 全球跟进）

目标：让陌生人 **30 秒内跑通** `onboard.sh`，觉得有用后 **Star + 转发**。

## 仓库侧（已完成 / 维护）

- [x] README 首屏：英文钩子 + 一条命令 `onboard.sh`
- [x] vs Mem0 对比表 + 一句话传播
- [ ] GitHub **About** 描述（手动在仓库 Settings 填）：
  - Description: `Universal local memory for AI — standalone chat, any MCP host, HTTP API. Markdown on disk.`
  - Topics: `cursor`, `mcp`, `memory`, `rag`, `claude`, `ai-agent`, `local-first`, `markdown`
- [ ] Social preview图：1200×630，文案「Cursor remembers you — locally」
- [ ] 15s 录屏 GIF 替换 `docs/assets/demo.svg`（首胜：记住 Python → 新会话召回）

## 阶段一（第 1–4 周）：国内 Cursor 用户

**渠道**：掘金、V2EX、即刻、微信群、知乎（Cursor 话题）

**标题模板（中文）**：
- 《Cursor 终于能跨会话记住我了：开源记忆侧车 MemoryAgent》
- 《一套本地记忆：网页能聊、Cursor 能接、你自己的 App 也能调 API》

**正文结构（复制改写）**：
1. 痛点：每个 Agent 会话都要重讲「用 Python、别 mock」
2. 30 秒演示：`bash scripts/onboard.sh .` → 重载 MCP → 两句话验证
3. 差异化：记忆是 `.memoryagent/memories/*.md`，Obsidian 能改
4. 链接仓库 + **求 Star 如果对你有用**

**首发节奏**：
- 第 1 天：掘金长文 + 仓库 Release v1.0.x
- 第 3 天：V2EX「分享创造」
- 第 7 天：根据 Issue/评论改 README FAQ

## 阶段二（第 5–12 周）：全球 MCP / Cursor 社区

**渠道**（按转化排序）：
1. [awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers) PR
2. Hacker News **Show HN**（周二–周四 9am US Eastern）
3. Reddit: r/cursor, r/LocalLLaMA, r/MachineLearning
4. X/Twitter: 带 15s GIF + `@cursor_ai` 无关 tag 堆砌

**Show HN 标题（英文）**：
`Show HN: MemoryAgent – local Markdown memory sidecar for Cursor via MCP`

**HN 正文要点**：
- Not another coding agent; only Remember + Align
- One command onboard; memories are auditable Markdown
- Recall@5 eval in CI; compare to Mem0 cloud black box
- Ask: feedback on MCP tool design

**awesome-mcp 提交条目**：
```markdown
- [MemoryAgent](https://github.com/jaychouya/MemoryAgent) - Local Markdown memory sidecar for Cursor/Claude Code. Recall, store, export via MCP; zero-config workspace scope.
```

## 阶段三（持续）：留存与二次传播

- 每个大版本：**GitHub Release** + 中英文 changelog 各一段
- 收集 **用户原话** 放进 README「Used by / Quotes」（征得同意）
- Issue 模板：Installation / Recall not working / Feature request
- 每月 1 条推文：**数字**（Recall@5、测试数、下载量）

## 不要做的事

- 不要同时主打 Web 聊天和侧车（路人会懵）
- 不要长 README 当首页（细节放 `docs/`）
- 不要买 Star / 刷榜（GitHub 会反噬）
- 未跑通 `onboard.sh --verify` 不要大规模发帖

## 成功指标（3 个月）

| 指标 | 保守 | 进取 |
|------|------|------|
| GitHub Stars | 200+ | 1k+ |
| onboard 相关 Issue | <5% 安装失败 | <2% |
| 外链 | 3 篇中文 + 1 次 HN 首页 | + awesome 合并 |

## 你今天就能做的 3 件事

1. 仓库 Settings 填好 Description + Topics（见上）
2. 在**一个**国内社区发掘金/V2EX（用上面模板）
3. 录 15 秒首胜 GIF，替换 README 演示区
