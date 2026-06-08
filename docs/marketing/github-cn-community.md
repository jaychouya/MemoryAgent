# GitHub 中文社区投稿

## 标题
[开源] MemoryAgent — 让 Cursor / Claude Code 记住你偏好的 AI 记忆系统

## 正文

大家好，我做了一个开源项目：**MemoryAgent**

### 解决什么问题？

用 Cursor / Claude Code 写代码时，每次开新会话都要重新告诉 AI：
- "我喜欢 Python，不要用 Java"
- "不要用 mock 数据库"
- "API 截止日期是周五"

MemoryAgent 让 AI 记住这些偏好，下次自动使用。

### 核心功能

1. **四类型记忆**
   - 用户画像：你是谁、擅长什么
   - 行为偏好：你喜欢/不喜欢什么
   - 项目动态：截止日期、重要决策
   - 外部引用：去哪查什么

2. **跨会话记忆**
   - 第一次："我喜欢 Python"
   - 第二次："帮我写排序" → 自动用 Python

3. **本地优先**
   - 所有数据存本地
   - 记忆是 Markdown，可用 Obsidian 编辑
   - 不上传云端

4. **支持 15+ 大模型**
   - OpenAI、DeepSeek、通义千问、小米 MiMo、智谱等

### 技术栈

- 后端：Python 3.9 + FastAPI
- 前端：Next.js 14 + TypeScript
- 存储：Markdown + SQLite
- 协议：MCP (Model Context Protocol)

### 为什么不用向量数据库？

参考 Claude Code 源码，发现它没用向量数据库，而是用结构化文件 + LLM 选择器。

原因：
- 向量相似度 ≠ 相关性
- embedding 模型换一个，结果差别大
- 维护成本高
- 用户看不懂向量数据

### 项目地址

https://github.com/jaychouya/MemoryAgent

欢迎大家试用、提 Issue、Star！
