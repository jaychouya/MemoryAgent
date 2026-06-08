# V2EX 发帖内容

## 标题
[分享创造] 我做了一个让 AI 记住你偏好的本地记忆系统，开源了

## 正文

各位 V2EX 的朋友们好！

最近在用 Cursor 和 Claude Code 写代码的时候，发现一个很烦的问题：每次开新会话，都要重新告诉 AI 我的偏好、项目背景、技术栈……

"我喜欢 Python，不要用 mock 数据库" 说了不下 50 遍。

为了解决这个问题，我做了一个开源项目：**MemoryAgent**

### 它能做什么？

1. **四类型记忆系统**
   - 用户画像（你是谁、擅长什么）
   - 行为偏好（你喜欢/不喜欢什么）
   - 项目动态（截止日期、重要决策）
   - 外部引用（去哪查什么）

2. **跨会话记忆共享**
   - 第一次说"我喜欢 Python"
   - 第二次问"帮我写排序" → 自动用 Python

3. **本地优先**
   - 所有数据存在本地
   - 记忆文件是 Markdown，可以用 Obsidian 编辑
   - 不上传到任何云端

4. **支持 15+ 大模型**
   - OpenAI、DeepSeek、通义千问、小米 MiMo、智谱 GLM 等

### 技术栈

- 后端：Python 3.9 + FastAPI
- 前端：Next.js 14 + TypeScript + Tailwind CSS
- 记忆存储：Markdown + SQLite
- 向量搜索：内存向量存储

### 为什么不用向量数据库？

参考了 Claude Code 的源码，发现一个有趣的事实：它没用向量数据库，而是用结构化文件 + LLM 选择器。

原因：
- 向量相似度 ≠ 相关性
- embedding 模型换一个，结果差别大
- 维护成本高
- 用户看不懂向量数据

MemoryAgent 也走了这条路：用 LLM 当选择器，比向量检索好用。

### 项目地址

https://github.com/jaychouya/MemoryAgent

欢迎大家试用、提 Issue、Star！

---

**标签：** 开源、AI、Python、Cursor、Claude Code、记忆系统
