# MemoryAgent 核心问题修复实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复 MemoryAgent 的 5 个核心问题，提升记忆系统质量和用户体验

**Architecture:** 基于现有代码结构，修复记忆存储、检索、会话管理等模块的 bug 和设计缺陷

**Tech Stack:** Python, FastAPI, tree-sitter, networkx

---

## 问题分析

1. **记忆存储问题** - 只存储描述，没有存储实际内容
2. **记忆检索问题** - 没有按 user_id 过滤，跨会话记忆混乱
3. **会话历史问题** - 缺少工具调用的完整信息
4. **输出格式问题** - Markdown 后处理是治标不治本
5. **记忆质量问题** - 记忆内容过于简单，缺乏上下文

---

## Task 1: 修复记忆存储 - 保存完整内容

**Files:**
- Modify: `src/memory/types/__init__.py:79-100`
- Modify: `src/memory/storage.py:40-70`
- Test: `tests/test_memory_storage.py`

- [ ] **Step 1: 检查当前记忆存储逻辑**

```python
# 当前问题：MemoryItem.to_markdown() 只保存 description
def to_markdown(self) -> str:
    return f"""---
name: {self.id}
description: {self.description}
type: {self.type.value}
created: {self.created_at.isoformat()}
updated: {self.updated_at.isoformat()}
---

{self.description}  # 问题：只保存了 description，没有保存 content
"""
```

- [ ] **Step 2: 修复 to_markdown 方法，保存完整内容**

```python
def to_markdown(self) -> str:
    """Convert memory to markdown format for storage."""
    metadata_yaml = ""
    if self.metadata:
        import yaml
        metadata_yaml = yaml.dump(self.metadata, allow_unicode=True)
    
    return f"""---
name: {self.id}
description: {self.description}
type: {self.type.value}
created: {self.created_at.isoformat()}
updated: {self.updated_at.isoformat()}
metadata:
{metadata_yaml}
---

{self.content}
"""
```

- [ ] **Step 3: 修复 from_markdown 方法，正确解析内容**

```python
@classmethod
def from_markdown(cls, content: str, memory_id: str = None) -> "MemoryItem":
    """Parse memory from markdown format."""
    import yaml
    
    lines = content.split("\n")
    metadata = {}
    content_start = 0
    in_frontmatter = False
    
    for i, line in enumerate(lines):
        if line.strip() == "---":
            if in_frontmatter:
                content_start = i + 1
                break
            in_frontmatter = True
            continue
        
        if in_frontmatter and ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            
            if key == "name":
                memory_id = value
            elif key == "description":
                description = value
            elif key == "type":
                memory_type = MemoryType(value)
            elif key == "created":
                created_at = datetime.fromisoformat(value)
            elif key == "updated":
                updated_at = datetime.fromisoformat(value)
    
    # 提取实际内容（跳过 frontmatter）
    actual_content = "\n".join(lines[content_start:]).strip()
    
    return cls(
        id=memory_id or "unknown",
        type=memory_type or MemoryType.USER,
        content=actual_content,  # 使用实际内容，而不是 description
        description=description or actual_content[:50],
        metadata=metadata,
        created_at=created_at or datetime.now(),
        updated_at=updated_at or datetime.now()
    )
```

- [ ] **Step 4: 运行测试验证修复**

```bash
cd /Users/tmind/Desktop/work/github/test2
source venv/bin/activate
python -c "
from src.memory.types import MemoryItem, MemoryType

# 测试创建和保存
memory = MemoryItem.create(
    memory_type=MemoryType.USER,
    content='用户喜欢Python，讨厌Java',
    description='用户编程语言偏好'
)

# 测试 to_markdown
md = memory.to_markdown()
print('=== Markdown 输出 ===')
print(md)

# 测试 from_markdown
parsed = MemoryItem.from_markdown(md)
print('=== 解析结果 ===')
print(f'Content: {parsed.content}')
print(f'Description: {parsed.description}')
print(f'Type: {parsed.type}')
"
```

Expected: Content 应该是 "用户喜欢Python，讨厌Java"，而不是 description

- [ ] **Step 5: 提交修复**

```bash
cd /Users/tmind/Desktop/work/github/test2
git add src/memory/types/__init__.py
git commit -m "fix: 修复记忆存储，保存完整内容而不是只有描述"
```

---

## Task 2: 修复记忆检索 - 添加 user_id 过滤

**Files:**
- Modify: `src/memory/storage.py:96-141`
- Modify: `src/memory/retrieval.py:41-91`
- Test: `tests/test_memory_retrieval.py`

- [ ] **Step 1: 检查当前检索逻辑**

```python
# 当前问题：search 方法没有 user_id 参数
async def search(
    self,
    query: str = None,
    memory_type: MemoryType = None,
    limit: int = 10
) -> List[MemoryItem]:
    # 没有 user_id 过滤，会搜索所有用户的记忆
```

- [ ] **Step 2: 修改 storage.py 的 search 方法，添加 user_id 参数**

```python
async def search(
    self,
    query: str = None,
    memory_type: MemoryType = None,
    user_id: str = None,
    limit: int = 10
) -> List[MemoryItem]:
    """
    Search memories with optional user_id filter.
    
    Args:
        query: Search query (matches description)
        memory_type: Filter by type
        user_id: Filter by user ID (for cross-session memory)
        limit: Maximum results
        
    Returns:
        List of matching MemoryItems
    """
    results = []
    
    types_to_search = [memory_type] if memory_type else list(MemoryType)
    
    for mt in types_to_search:
        type_dir = self.base_dir / mt.value
        if not type_dir.exists():
            continue
        
        for file_path in type_dir.glob("*.md"):
            try:
                content = file_path.read_text(encoding="utf-8")
                memory = MemoryItem.from_markdown(content, file_path.stem)
                
                # user_id 过滤：检查文件名或元数据中的 user_id
                if user_id:
                    # 方案1：检查文件名是否包含 user_id
                    # 方案2：检查 metadata 中的 user_id
                    # 这里使用方案1：文件名格式为 {user_id}_{hash}.md
                    if not file_path.stem.startswith(user_id):
                        continue
                
                # Simple text matching
                if query:
                    query_lower = query.lower()
                    if (query_lower in memory.description.lower() or 
                        query_lower in memory.content.lower()):
                        results.append(memory)
                else:
                    results.append(memory)
                    
            except Exception as e:
                logger.warning(f"Failed to parse {file_path}: {e}")
    
    # Sort by update time, most recent first
    results.sort(key=lambda m: m.updated_at, reverse=True)
    return results[:limit]
```

- [ ] **Step 3: 修改 retrieval.py 的 retrieve 方法，传递 user_id**

```python
async def retrieve(
    self,
    query: str,
    user_id: str = None,
    limit: int = 5
) -> List[Dict]:
    """
    Retrieve relevant memories for a query.
    
    Args:
        query: User's query
        user_id: User identifier (for cross-session memory)
        limit: Maximum memories to return
        
    Returns:
        List of memory dicts with content and staleness info
    """
    # Step 1: Get memories filtered by user_id
    all_memories = await self.storage.search(
        limit=100,
        user_id=user_id  # 添加 user_id 过滤
    )
    
    if not all_memories:
        return []
    
    # Step 2: Select relevant memories using LLM
    if self.llm and len(all_memories) > limit:
        selected = await self._select_with_llm(query, all_memories, limit)
    else:
        # Simple keyword matching fallback
        selected = self._select_with_keywords(query, all_memories, limit)
    
    # Step 3: Format results with staleness info
    results = []
    for memory in selected:
        result = {
            "id": memory.id,
            "type": memory.type.value,
            "content": memory.content,
            "description": memory.description,
            "age_days": memory.age_days(),
            "is_stale": memory.is_stale(max_days=1),
            "staleness_warning": None
        }
        
        if result["is_stale"]:
            result["staleness_warning"] = self.STALENESS_WARNING_TEMPLATE.format(
                days=result["age_days"]
            )
        
        results.append(result)
    
    return results
```

- [ ] **Step 4: 运行测试验证 user_id 过滤**

```bash
cd /Users/tmind/Desktop/work/github/test2
source venv/bin/activate
python -c "
import asyncio
from src.memory.storage import MemoryStorage
from src.memory.types import MemoryType

async def test():
    storage = MemoryStorage()
    
    # 创建两个不同用户的记忆
    mem1 = await storage.store(
        content='用户A喜欢Python',
        memory_type=MemoryType.USER,
        user_id='user_a'
    )
    
    mem2 = await storage.store(
        content='用户B喜欢Java',
        memory_type=MemoryType.USER,
        user_id='user_b'
    )
    
    # 搜索 user_a 的记忆
    results_a = await storage.search(user_id='user_a')
    print(f'user_a memories: {len(results_a)}')
    for m in results_a:
        print(f'  - {m.content}')
    
    # 搜索 user_b 的记忆
    results_b = await storage.search(user_id='user_b')
    print(f'user_b memories: {len(results_b)}')
    for m in results_b:
        print(f'  - {m.content}')

asyncio.run(test())
"
```

Expected: user_a 只看到自己的记忆，user_b 只看到自己的记忆

- [ ] **Step 5: 提交修复**

```bash
cd /Users/tmind/Desktop/work/github/test2
git add src/memory/storage.py src/memory/retrieval.py
git commit -m "fix: 修复记忆检索，添加 user_id 过滤支持跨会话记忆"
```

---

## Task 3: 修复会话历史 - 保存完整的工具调用链

**Files:**
- Modify: `src/backend/api/chat.py:162-176`
- Test: `tests/test_session_history.py`

- [ ] **Step 1: 检查当前会话保存逻辑**

```python
# 当前问题：只保存 user 和 assistant 消息，没有保存工具调用和结果
sessions[session_key].append({
    "role": "user",
    "content": request.message,
    "timestamp": datetime.now().isoformat()
})
sessions[session_key].append({
    "role": "assistant",
    "content": result.content,
    "timestamp": datetime.now().isoformat()
})
```

- [ ] **Step 2: 修改 AgentLoop 返回完整的消息历史**

```python
# 在 src/agent/loop.py 中，修改 run 方法返回完整历史
async def run(self, user_message, system_prompt=None, context_messages=None, session_id=None, user_id=None):
    # ... 现有代码 ...
    
    # 返回结果时，包含完整的消息历史
    return AgentResult(
        content=final_content,
        stop_reason=stop_reason,
        state=state,
        messages=state.messages  # 添加完整的消息历史
    )
```

- [ ] **Step 3: 修改 chat.py 保存完整的消息链**

```python
# 保存完整的消息历史，包括工具调用
if result.messages:
    # 保存所有消息（包括工具调用和结果）
    for msg in result.messages:
        sessions[session_key].append({
            "role": msg.get("role"),
            "content": msg.get("content", ""),
            "timestamp": datetime.now().isoformat(),
            "tool_calls": msg.get("tool_calls"),
            "tool_call_id": msg.get("tool_call_id"),
            "name": msg.get("name")
        })
else:
    # 降级方案：只保存 user 和 assistant 消息
    sessions[session_key].append({
        "role": "user",
        "content": request.message,
        "timestamp": datetime.now().isoformat()
    })
    sessions[session_key].append({
        "role": "assistant",
        "content": result.content,
        "timestamp": datetime.now().isoformat()
    })
```

- [ ] **Step 4: 运行测试验证完整历史保存**

```bash
cd /Users/tmind/Desktop/work/github/test2
source venv/bin/activate
# 启动后端，发送一个会触发工具调用的消息
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "记住我喜欢Python", "session_id": "test_history", "user_id": "user1"}'

# 检查会话文件
cat sessions/user1_test_history.json | python -m json.tool
```

Expected: 会话文件包含 user、assistant、tool_calls、tool 等完整消息链

- [ ] **Step 5: 提交修复**

```bash
cd /Users/tmind/Desktop/work/github/test2
git add src/backend/api/chat.py src/agent/loop.py
git commit -m "fix: 修复会话历史，保存完整的工具调用链"
```

---

## Task 4: 改进输出格式 - 增强 System Prompt

**Files:**
- Modify: `src/agent/prompts/sections.py:1-50`
- Test: `tests/test_output_format.py`

- [ ] **Step 1: 检查当前 System Prompt**

```python
# 当前问题：虽然有格式要求，但示例不够具体
OUTPUT_STYLE = PromptSection(
    name="output_style",
    content=(
        "【输出格式 - 最高优先级指令】\n\n"
        "你是纯文本输出助手。你的回复只能包含普通文字、数字和标点符号。\n\n"
        # ... 其他内容
    ),
    section_type=SectionType.STATIC,
    cache_priority=40
)
```

- [ ] **Step 2: 增强 System Prompt，添加更多具体示例**

```python
OUTPUT_STYLE = PromptSection(
    name="output_style",
    content=(
        "【输出格式 - 最高优先级指令】\n\n"
        "你是纯文本输出助手。你的回复只能包含普通文字、数字和标点符号。\n\n"
        "绝对禁止的符号：\n"
        "# 井号（标题）\n"
        "* 星号（加粗/列表）\n"
        "` 反引号（代码块）\n"
        "| 竖线（表格）\n"
        "> 大于号（引用）\n"
        "- 减号（列表）\n"
        "~ 波浪号（删除线）\n"
        "_ 下划线（斜体）\n\n"
        
        "正确的输出示例：\n\n"
        "用户问：什么是Python？\n"
        "你的回答：\n"
        "Python 是一种高级编程语言，由吉多·范罗苏姆于 1991 年创建。\n\n"
        "Python 的主要特点包括：\n\n"
        "1. 语法简洁易读，使用缩进表示代码块\n"
        "2. 动态类型系统，变量无需声明类型\n"
        "3. 丰富的标准库和第三方生态系统\n"
        "4. 支持面向对象、函数式和过程式编程\n\n"
        "Python 广泛应用于 Web 开发、数据科学、人工智能、自动化脚本等领域。\n\n"
        
        "用户问：帮我写一个排序函数\n"
        "你的回答：\n"
        "以下是几种常见的排序算法实现：\n\n"
        "1. 冒泡排序\n"
        "原理：重复比较相邻元素，将较大的元素交换到后面\n"
        "时间复杂度：O(n²)\n"
        "适用场景：小规模数据排序\n\n"
        "2. 快速排序\n"
        "原理：选择基准元素，将数组分为两部分递归排序\n"
        "时间复杂度：平均 O(n log n)\n"
        "适用场景：大规模数据排序\n\n"
        
        "代码示例（不要用代码块，直接写在文本中）：\n"
        "def bubble_sort(arr):\n"
        "    n = len(arr)\n"
        "    for i in range(n):\n"
        "        for j in range(0, n-i-1):\n"
        "            if arr[j] > arr[j+1]:\n"
        "                arr[j], arr[j+1] = arr[j+1], arr[j]\n"
        "    return arr\n\n"
        
        "回复结构要求：\n"
        "1. 先给出核心答案\n"
        "2. 展开说明原因和背景\n"
        "3. 提供实际案例或代码示例\n"
        "4. 列出注意事项\n\n"
        "回复长度要求：\n"
        "- 简单问题：至少 200 字\n"
        "- 中等复杂度：300-500 字\n"
        "- 复杂问题：500-1000 字"
    ),
    section_type=SectionType.STATIC,
    cache_priority=40
)
```

- [ ] **Step 3: 运行测试验证输出格式**

```bash
cd /Users/tmind/Desktop/work/github/test2
source venv/bin/activate
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "帮我写一个Python函数计算斐波那契数列", "session_id": "test_format", "user_id": "user1"}'
```

Expected: 输出应该是纯文本格式，没有 Markdown 符号

- [ ] **Step 4: 提交改进**

```bash
cd /Users/tmind/Desktop/work/github/test2
git add src/agent/prompts/sections.py
git commit -m "feat: 增强 System Prompt，添加更多格式示例"
```

---

## Task 5: 改进记忆质量 - 保存更有意义的内容

**Files:**
- Modify: `src/agent/tools/builtin.py:76-120`
- Modify: `src/agent/loop.py:124-150`
- Test: `tests/test_memory_quality.py`

- [ ] **Step 1: 检查当前记忆存储逻辑**

```python
# 当前问题：memory_store 工具只保存 content，没有保存上下文
async def execute(self, content: str, memory_type: str, importance: float = 0.5, **kwargs):
    memory = MemoryItem.create(
        memory_type=MemoryType(memory_type),
        content=content,
        description=content[:50]
    )
```

- [ ] **Step 2: 增强 memory_store 工具，保存更多上下文**

```python
async def execute(self, content: str, memory_type: str, importance: float = 0.5, **kwargs):
    """Store memory with enhanced context."""
    user_id = kwargs.get("user_id", "anonymous")
    session_id = kwargs.get("session_id")
    
    # 生成更有意义的描述
    description = self._generate_description(content, memory_type)
    
    # 添加元数据
    metadata = {
        "user_id": user_id,
        "session_id": session_id,
        "importance": importance,
        "source": "user_conversation"
    }
    
    memory = MemoryItem.create(
        memory_type=MemoryType(memory_type),
        content=content,
        description=description,
        metadata=metadata
    )
    
    # 存储时使用 user_id 作为文件名前缀
    memory.id = f"{user_id}_{memory.id}"
    
    await self.memory.storage.store(memory)
    
    return ToolResult(
        success=True,
        content=f"已记住：{description}"
    )

def _generate_description(self, content: str, memory_type: str) -> str:
    """Generate a meaningful description for the memory."""
    if memory_type == "user":
        return f"用户偏好：{content[:30]}"
    elif memory_type == "feedback":
        return f"行为反馈：{content[:30]}"
    elif memory_type == "project":
        return f"项目动态：{content[:30]}"
    elif memory_type == "reference":
        return f"外部引用：{content[:30]}"
    else:
        return content[:50]
```

- [ ] **Step 3: 修改 AgentLoop，自动提取记忆**

```python
# 在 AgentLoop 中，对话结束后自动提取记忆
async def run(self, user_message, system_prompt=None, context_messages=None, session_id=None, user_id=None):
    # ... 现有代码 ...
    
    # 对话结束后，自动提取记忆
    if user_id and final_content:
        await self._extract_memories(user_message, final_content, user_id, session_id)
    
    return result

async def _extract_memories(self, user_message, assistant_response, user_id, session_id):
    """Extract memories from conversation."""
    # 提取用户偏好
    if any(keyword in user_message.lower() for keyword in ["喜欢", "讨厌", "偏好", "习惯"]):
        await self.memory.store(
            content=user_message,
            memory_type="user",
            user_id=user_id,
            session_id=session_id
        )
    
    # 提取项目动态
    if any(keyword in user_message.lower() for keyword in ["截止", "deadline", "任务", "计划"]):
        await self.memory.store(
            content=user_message,
            memory_type="project",
            user_id=user_id,
            session_id=session_id
        )
```

- [ ] **Step 4: 运行测试验证记忆质量**

```bash
cd /Users/tmind/Desktop/work/github/test2
source venv/bin/activate
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "我喜欢Python，讨厌Java", "session_id": "test_quality", "user_id": "user1"}'

# 检查记忆文件
cat memories/user/user1_*.md
```

Expected: 记忆文件包含完整内容、有意义的描述、用户ID等元数据

- [ ] **Step 5: 提交改进**

```bash
cd /Users/tmind/Desktop/work/github/test2
git add src/agent/tools/builtin.py src/agent/loop.py
git commit -m "feat: 改进记忆质量，保存更有意义的内容和上下文"
```

---

## Task 6: 集成测试 - 验证所有修复

**Files:**
- Test: `tests/test_integration.py`

- [ ] **Step 1: 创建集成测试脚本**

```python
#!/usr/bin/env python3
"""Integration test for all fixes."""
import asyncio
import requests
import json

BASE_URL = "http://localhost:8000"

async def test_memory_storage():
    """Test 1: 记忆存储保存完整内容"""
    print("=== 测试 1: 记忆存储 ===")
    
    # 存储记忆
    response = requests.post(f"{BASE_URL}/api/chat", json={
        "message": "记住我喜欢Python，讨厌Java",
        "session_id": "test_integration",
        "user_id": "user1"
    })
    
    result = response.json()
    print(f"Response: {result['response'][:100]}...")
    
    # 检查记忆文件
    import glob
    memory_files = glob.glob("memories/user/user1_*.md")
    if memory_files:
        with open(memory_files[-1]) as f:
            content = f.read()
            print(f"Memory file content:\n{content}")
            
            # 验证包含完整内容
            if "喜欢Python" in content and "讨厌Java" in content:
                print("✅ 测试 1 通过: 记忆保存了完整内容")
            else:
                print("❌ 测试 1 失败: 记忆没有保存完整内容")
    else:
        print("❌ 测试 1 失败: 没有找到记忆文件")

async def test_user_id_filter():
    """Test 2: 记忆检索按 user_id 过滤"""
    print("\n=== 测试 2: user_id 过滤 ===")
    
    # user1 存储记忆
    requests.post(f"{BASE_URL}/api/chat", json={
        "message": "我喜欢Python",
        "session_id": "test_user1",
        "user_id": "user1"
    })
    
    # user2 存储记忆
    requests.post(f"{BASE_URL}/api/chat", json={
        "message": "我喜欢Java",
        "session_id": "test_user2",
        "user_id": "user2"
    })
    
    # user1 查询记忆
    response = requests.post(f"{BASE_URL}/api/chat", json={
        "message": "我喜欢什么编程语言？",
        "session_id": "test_user1_query",
        "user_id": "user1"
    })
    
    result = response.json()
    if "Python" in result['response'] and "Java" not in result['response']:
        print("✅ 测试 2 通过: user1 只看到自己的记忆")
    else:
        print(f"❌ 测试 2 失败: {result['response'][:100]}")

async def test_session_history():
    """Test 3: 会话历史保存完整工具调用链"""
    print("\n=== 测试 3: 会话历史 ===")
    
    # 发送会触发工具调用的消息
    requests.post(f"{BASE_URL}/api/chat", json={
        "message": "记住我喜欢Python",
        "session_id": "test_history",
        "user_id": "user1"
    })
    
    # 检查会话文件
    import os
    session_file = "sessions/user1_test_history.json"
    if os.path.exists(session_file):
        with open(session_file) as f:
            session = json.load(f)
            
            # 检查是否有工具调用
            has_tool_calls = any(
                msg.get("tool_calls") or msg.get("role") == "tool"
                for msg in session.get("messages", [])
            )
            
            if has_tool_calls:
                print("✅ 测试 3 通过: 会话历史包含工具调用")
            else:
                print("❌ 测试 3 失败: 会话历史缺少工具调用")
    else:
        print("❌ 测试 3 失败: 没有找到会话文件")

async def test_output_format():
    """Test 4: 输出格式是纯文本"""
    print("\n=== 测试 4: 输出格式 ===")
    
    response = requests.post(f"{BASE_URL}/api/chat", json={
        "message": "帮我写一个排序函数",
        "session_id": "test_format",
        "user_id": "user1"
    })
    
    result = response.json()
    content = result['response']
    
    # 检查是否包含 Markdown 符号
    markdown_symbols = ["#", "**", "```", "|", ">", "- ", "~", "_"]
    has_markdown = any(symbol in content for symbol in markdown_symbols)
    
    if not has_markdown:
        print("✅ 测试 4 通过: 输出是纯文本格式")
    else:
        print(f"❌ 测试 4 失败: 输出包含 Markdown 符号")
        print(f"Content preview: {content[:200]}")

async def main():
    """运行所有测试"""
    print("开始集成测试...\n")
    
    await test_memory_storage()
    await test_user_id_filter()
    await test_session_history()
    await test_output_format()
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 2: 运行集成测试**

```bash
cd /Users/tmind/Desktop/work/github/test2
source venv/bin/activate

# 启动后端
uvicorn src.backend.main:app --host 0.0.0.0 --port 8000 &

# 等待后端启动
sleep 3

# 运行测试
python tests/test_integration.py
```

Expected: 所有测试都应该通过

- [ ] **Step 3: 提交集成测试**

```bash
cd /Users/tmind/Desktop/work/github/test2
git add tests/test_integration.py
git commit -m "test: 添加集成测试验证所有修复"
```

---

## 最终验证

完成所有任务后，运行以下命令验证：

```bash
cd /Users/tmind/Desktop/work/github/test2
source venv/bin/activate

# 运行所有测试
python -m pytest tests/ -v

# 启动后端
uvicorn src.backend.main:app --host 0.0.0.0 --port 8000 --reload

# 在另一个终端运行集成测试
python tests/test_integration.py
```

---

## 总结

这个实现计划解决了 MemoryAgent 的 5 个核心问题：

1. ✅ **记忆存储** - 保存完整内容，不只是描述
2. ✅ **记忆检索** - 添加 user_id 过滤，支持跨会话记忆
3. ✅ **会话历史** - 保存完整的工具调用链
4. ✅ **输出格式** - 增强 System Prompt，提供更具体的示例
5. ✅ **记忆质量** - 保存更有意义的内容和上下文

每个任务都包含：
- 详细的代码修改示例
- 测试验证步骤
- 提交命令

按照这个计划执行，MemoryAgent 的核心问题将得到彻底修复。
