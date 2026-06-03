# 技术博客：我用 3000 行代码让 AI 拥有了长期记忆

> 适合发布平台：掘金、知乎、CSDN、Medium

---

## 前言

用过 ChatGPT、Claude 的人，大概率都有这样的困扰：

**每次开启新对话，都要反复交代相关背景。**

"我正在推进 XX 项目，采用 XX 技术栈，目前正处理 XX 难题……"——这样的自我介绍，你或许已经重复了上百次。

这并非你的问题，而是当前所有 AI 助手的共性短板：**它们围绕提示词运行，而非围绕用户本身**。每一次对话都是全新冷启动。

为了解决这个问题，我开发了 **MemoryAgent**——一个具备认知记忆架构的 AI Agent，让 AI 记住你的偏好，越用越懂你。

---

## 核心设计：四类型记忆系统

MemoryAgent 不是简单保存聊天记录，而是实现了**结构化的认知记忆**：

### 1. 用户画像（User Profile）

```markdown
---
type: user
tags:
  - preference
  - python
---
#preference #python

用户喜欢 Python，讨厌 Java，因为 Python 语法简洁
```

### 2. 行为反馈（Behavioral Feedback）

```markdown
---
type: feedback
tags:
  - rule
  - database
---
#rule #database

不要用 mock 数据库，应该用真实的测试数据库
```

### 3. 项目动态（Project Context）

```markdown
---
type: project
tags:
  - deadline
  - api
---
#deadline #api

API 接口周五前必须完成，目前进度 60%
```

### 4. 外部引用（External References）

```markdown
---
type: reference
tags:
  - grafana
  - monitoring
---
#grafana #monitoring

Grafana 看板地址：http://grafana.internal/d/api-monitor
```

---

## 技术架构

### Agent Loop（智能决策循环）

MemoryAgent 基于 Claude Code 的 Agent Loop 架构：

```python
while True:
    1. 压缩上下文（5步策略）
    2. 调用 LLM API
    3. If end_turn → break
    4. 执行工具调用
    5. 更新状态 → continue
```

### 记忆存储

记忆以 Markdown 文件存储，兼容 Obsidian：

```
memories/
├── user/
│   └── user_abc123.md      # 用户偏好
├── feedback/
│   └── feedback_def456.md  # 行为规则
├── project/
│   └── project_ghi789.md   # 项目动态
└── reference/
    └── reference_jkl012.md # 外部引用
```

每个记忆文件包含：
- **YAML frontmatter**：元数据（类型、标签、创建时间）
- **Markdown 内容**：记忆详情
- **Hashtags**：Obsidian 兼容标签

### SQLite 索引

为了快速检索，MemoryAgent 维护了一个 SQLite 索引：

```sql
CREATE TABLE memories (
    memory_id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    memory_type TEXT NOT NULL,
    user_id TEXT,
    importance REAL DEFAULT 0.5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE VIRTUAL TABLE memories_fts USING fts5(
    memory_id, content, memory_type, user_id
);
```

---

## 实现细节

### 1. 记忆分块器（Chunker）

长内容会自动分块，每块不超过 3000 tokens：

```python
class MemoryChunker:
    def __init__(self, max_tokens: int = 3000):
        self.max_chars = max_tokens * 2  # 1 token ≈ 2 字符
    
    def chunk(self, content: str) -> List[str]:
        if len(content) <= self.max_chars:
            return [content]
        
        chunks = []
        current_chunk = ""
        
        # 按句子分割
        sentences = re.split(r'([。！？.!?])', content)
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) > self.max_chars:
                chunks.append(current_chunk)
                current_chunk = sentence
            else:
                current_chunk += sentence
        
        return chunks
```

### 2. 重要性评分器（Scorer）

每个记忆都会被评分，决定其重要程度：

```python
class MemoryScorer:
    TYPE_WEIGHTS = {
        "feedback": 0.9,  # 行为反馈最重要
        "user": 0.8,      # 用户偏好次之
        "project": 0.7,   # 项目动态
        "reference": 0.6  # 外部引用
    }
    
    def score(self, content: str, memory_type: str) -> float:
        score = 0.0
        
        # 类型基础分
        score += self.TYPE_WEIGHTS.get(memory_type, 0.5) * 0.3
        
        # 关键词分
        keywords = ["喜欢", "讨厌", "不要", "必须", "重要"]
        for keyword in keywords:
            if keyword in content:
                score += 0.1
        
        # 具体性分
        if re.search(r'\d+', content):  # 包含数字
            score += 0.2
        
        return min(1.0, score)
```

### 3. 向量搜索（Vector Store）

支持语义相似度搜索：

```python
class VectorStore:
    def search(self, query_embedding: List[float], top_k: int = 5):
        similarities = []
        for doc_embedding in self.embeddings:
            similarity = cosine_similarity(query_embedding, doc_embedding)
            similarities.append(similarity)
        
        # 返回最相似的结果
        return sorted(similarities, reverse=True)[:top_k]
```

---

## 使用方式

### 1. 一键安装

```bash
git clone https://github.com/jaychouya/MemoryAgent.git
cd MemoryAgent
pip install -r requirements.txt
python src/main.py
```

### 2. 配置模型

访问 http://localhost:3000，点击「配置」按钮，选择模型厂商并填写 API Key。

### 3. 开始对话

AI 会自动记住你的偏好，下次对话会自动使用。

---

## 与主流框架对比

| 特性 | ChatGPT | Claude | MemoryAgent |
|------|---------|--------|-------------|
| 记住用户偏好 | ❌ 每次重来 | ❌ 每次重来 | ✅ 跨会话记忆 |
| 记忆可编辑 | ❌ | ❌ | ✅ Obsidian 兼容 |
| 本地部署 | ❌ | ❌ | ✅ 数据在本地 |
| 多模型支持 | ❌ 单一模型 | ❌ 单一模型 | ✅ 15+ 厂商 |
| 记忆分类 | ❌ | ❌ | ✅ 四类型系统 |
| 技能学习 | ❌ | ❌ | ✅ 自动学习 |

---

## 总结

MemoryAgent 的核心理念是：**AI 应该围绕用户运行，而不是围绕提示词运行**。

通过四类型记忆系统、Obsidian 兼容存储、SQLite 索引、向量搜索等技术，MemoryAgent 实现了真正的"长期记忆"。

如果你也想让 AI 记住你是谁，欢迎试试 MemoryAgent：

**GitHub**: https://github.com/jaychouya/MemoryAgent

---

## 标签

`#AI` `#Agent` `#记忆系统` `#LLM` `#Python` `#开源`
