# 开源中国投稿内容

## 项目名称
MemoryAgent — AI Agent 长期记忆系统

## 项目简介

MemoryAgent 是一个为 AI Coding Agent（如 Cursor、Claude Code）提供长期记忆的开源系统。

**核心功能：**
- 四类型记忆系统（用户画像/行为反馈/项目动态/外部引用）
- 跨会话记忆共享
- 本地优先，隐私可控
- Obsidian 兼容，记忆可编辑
- 支持 15+ 大模型

**技术栈：**
- 后端：Python 3.9 + FastAPI
- 前端：Next.js 14 + TypeScript
- 存储：Markdown + SQLite
- 协议：MCP (Model Context Protocol)

**项目地址：** https://github.com/jaychouya/MemoryAgent

## 核心亮点

1. **Claude Code 架构** - 参考 Claude Code 源码设计，用 LLM 选择器替代向量检索
2. **本地优先** - 所有数据存储在本地，不上传云端
3. **Obsidian 兼容** - 记忆文件可直接在 Obsidian 中编辑
4. **MCP 协议** - 支持 Cursor、Claude Code 等工具一键集成

## 适用人群

- 使用 Cursor / Claude Code 的开发者
- 需要 AI 记住偏好的用户
- 关注隐私的数据敏感用户
- 喜欢用 Obsidian 管理知识的用户
