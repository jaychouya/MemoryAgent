# 掘金发帖内容

## 标题
我用 3000 行代码让 AI 拥有了长期记忆，面试官都愣了

## 正文

### 前言

用过 ChatGPT、Claude 的人，大概率都有这样的困扰：**每次开新对话，都要重新介绍自己。**

"我正在推进 XX 项目，采用 XX 技术栈，目前正处理 XX 难题……"——这样的自我介绍，你或许已经重复了上百次。

这并非你的问题，而是当前所有 AI 助手的共性短板：**它们围绕提示词运行，而非围绕用户本身。**

为了解决这个问题，我开发了 **MemoryAgent**——一个具备认知记忆架构的 AI Agent，让 AI 记住你的偏好，越用越懂你。

### 核心设计：四类型记忆系统

MemoryAgent 不是简单保存聊天记录，而是实现了**结构化的认知记忆**：

| 类型 | 用途 | 示例 |
|------|------|------|
| **用户画像** | 你的偏好、角色、知识水平 | "我喜欢 Python" |
| **行为反馈** | AI 该做什么、不该做什么 | "不要用 mock 数据库" |
| **项目动态** | 截止日期、重要决策 | "周五前完成 API" |
| **外部引用** | 去哪找什么信息 | "Grafana 看板地址" |

### 为什么不用向量数据库？

参考了 Claude Code 的源码，发现一个有趣的事实：**它没用向量数据库**。

原因：
1. **相似不等于相关**：向量检索可能把过去所有讨论 bug 的对话都召回来，但只有一两条真正相关
2. **召回不稳定**：embedding 模型换一个，召回结果差别巨大
3. **维护成本高**：要部署向量数据库、选 embedding 模型、管 chunk 大小
4. **用户没法看**：存进向量数据库的记忆是一堆 768 维浮点数，人脑根本读不懂

MemoryAgent 的方案：**用 LLM 当选择器**，比向量检索好用得多。

### 技术架构

```
User Input → Agent Loop → LLM Call → Tool Execution → Memory Update
                ↑
        Context Compression (5-step)
        Memory Retrieval (4-type)
        Skill Matching (networkx)
```

### 核心模块

- **记忆分块器**：长内容自动分块，每块不超过 3000 tokens
- **重要性评分器**：每个记忆都会被评分，决定其重要程度
- **向量搜索**：支持语义相似度搜索
- **记忆老化警告**：2 天前的记忆会自动加 stale 提醒
- **主动验证**：记忆里写了文件路径/函数名，使用前先 grep 一下

### 使用方式

```bash
git clone https://github.com/jaychouya/MemoryAgent.git
cd MemoryAgent
pip install -r requirements.txt
python src/main.py
```

### 与主流框架对比

| 特性 | ChatGPT | Claude | MemoryAgent |
|------|---------|--------|-------------|
| 记住用户偏好 | ❌ | ❌ | ✅ |
| 记忆可编辑 | ❌ | ❌ | ✅ |
| 本地部署 | ❌ | ❌ | ✅ |
| 多模型支持 | ❌ | ❌ | ✅ |
| 记忆分类 | ❌ | ❌ | ✅ |

### 总结

MemoryAgent 的核心理念是：**AI 应该围绕用户运行，而不是围绕提示词运行。**

如果你也想让 AI 记住你是谁，欢迎试试 MemoryAgent：

**GitHub**: https://github.com/jaychouya/MemoryAgent

---

**标签：** AI、Python、开源、记忆系统、Cursor、Claude Code
