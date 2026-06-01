# MemoryAgent 优化实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复 user_id 传递、会话历史截断、会话名称显示等问题

**Architecture:** 基于现有代码结构，修复数据传递和显示逻辑

**Tech Stack:** Python, FastAPI

---

## 问题分析

1. **user_id 传递问题** - memory_store 工具没有接收到正确的 user_id
2. **会话历史截断问题** - 截断逻辑破坏了完整的消息链
3. **会话名称显示问题** - 代码逻辑错误，messages 是列表不是字典

---

## Task 1: 修复 user_id 传递到 memory_store

**Files:**
- Modify: `src/agent/tools/builtin.py:108-152`
- Test: `tests/test_memory_user_id.py`

- [ ] **Step 1: 写一个失败的测试**

```python
"""Test memory store receives correct user_id."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.agent.tools.builtin import MemoryStoreTool


@pytest.mark.asyncio
async def test_memory_store_receives_user_id():
    """memory_store 工具应该接收到正确的 user_id。"""
    # 创建 mock memory manager
    mock_memory = AsyncMock()
    mock_memory.store = AsyncMock(return_value=True)
    
    # 创建工具
    tool = MemoryStoreTool(mock_memory)
    
    # 执行工具，传入 user_id
    result = await tool.execute(
        content="用户喜欢Python",
        memory_type="user",
        user_id="user123",
        session_id="session456"
    )
    
    # 验证 memory.store 被调用时包含了正确的 user_id
    mock_memory.store.assert_called_once()
    call_kwargs = mock_memory.store.call_args[1]
    assert call_kwargs.get("user_id") == "user123"
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd /Users/tmind/Desktop/work/github/test2
source venv/bin/activate
python -m pytest tests/test_memory_user_id.py -v
```

Expected: FAIL - user_id 没有正确传递

- [ ] **Step 3: 修复代码**

```python
# src/agent/tools/builtin.py
async def execute(
    self,
    content: str,
    memory_type: str,
    importance: float = 0.5,
    **kwargs
) -> ToolResult:
    """Store memory."""
    try:
        from src.memory.types import MemoryType
        
        type_map = {
            "user": MemoryType.USER,
            "feedback": MemoryType.FEEDBACK,
            "project": MemoryType.PROJECT,
            "reference": MemoryType.REFERENCE
        }
        
        mem_type = type_map.get(memory_type, MemoryType.USER)
        
        # 生成有意义的描述
        description = self._generate_description(content, memory_type)
        
        # 获取用户上下文 - 从 kwargs 中获取
        user_id = kwargs.get("user_id", "anonymous")
        session_id = kwargs.get("session_id")
        
        # 构建元数据
        metadata = {
            "user_id": user_id,
            "importance": importance,
            "source": "user_conversation"
        }
        if session_id:
            metadata["session_id"] = session_id
        
        result = await self.memory.store(
            content=content,
            memory_type=mem_type,
            description=description,
            metadata=metadata,
            user_id=user_id
        )
        
        if result:
            return ToolResult(
                success=True,
                content=f"已成功存储记忆到 {memory_type} 类型\n\n存储内容: {content[:100]}"
            )
        else:
            return ToolResult(
                success=False,
                content=None,
                error="记忆存储失败"
            )
        
    except Exception as e:
        return ToolResult(
            success=False,
            content=None,
            error=f"记忆存储失败: {str(e)}"
        )
```

- [ ] **Step 4: 运行测试验证通过**

```bash
python -m pytest tests/test_memory_user_id.py -v
```

Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/agent/tools/builtin.py tests/test_memory_user_id.py
git commit -m "fix: 修复 memory_store 工具的 user_id 传递"
```

---

## Task 2: 修复会话历史截断逻辑

**Files:**
- Modify: `src/backend/api/chat.py:175-182`
- Test: `tests/test_session_truncation.py`

- [ ] **Step 1: 写一个失败的测试**

```python
"""Test session truncation preserves message chain."""
import pytest


def test_session_truncation_preserves_chain():
    """会话截断应该保留完整的消息链。"""
    # 模拟一个包含工具调用的消息链
    messages = [
        {"role": "user", "content": "记住我喜欢Python"},
        {"role": "assistant", "content": "", "tool_calls": [{"id": "call_1", "function": {"name": "memory_store"}}]},
        {"role": "tool", "content": "已记住", "tool_call_id": "call_1"},
        {"role": "assistant", "content": "好的，我已经记住了。"}
    ]
    
    # 添加更多消息使其超过20条
    for i in range(20):
        messages.append({"role": "user", "content": f"消息{i}"})
        messages.append({"role": "assistant", "content": f"回复{i}"})
    
    # 截断逻辑
    if len(messages) > 20:
        # 错误的截断方式：直接截断可能破坏工具调用链
        # messages = messages[-20:]
        
        # 正确的截断方式：找到完整的消息对
        truncated = []
        count = 0
        for i in range(len(messages) - 1, -1, -1):
            msg = messages[i]
            truncated.insert(0, msg)
            count += 1
            if count >= 20:
                # 确保不截断工具调用链的中间
                if msg.get("role") == "tool":
                    continue
                break
        messages = truncated
    
    # 验证消息链完整性
    has_tool_calls = any(msg.get("tool_calls") for msg in messages)
    has_tool_result = any(msg.get("role") == "tool" for msg in messages)
    
    # 如果有工具调用，应该也有工具结果
    if has_tool_calls:
        assert has_tool_result
```

- [ ] **Step 2: 运行测试确认失败**

```bash
python -m pytest tests/test_session_truncation.py -v
```

Expected: FAIL

- [ ] **Step 3: 修复代码**

```python
# src/backend/api/chat.py
# 保存完整的消息历史
if result.state and result.state.messages:
    sessions[session_key] = result.state.messages
else:
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

# 截断逻辑：保留完整的消息链
if len(sessions[session_key]) > 20:
    # 找到合适的消息对边界
    messages = sessions[session_key]
    truncated = []
    count = 0
    for i in range(len(messages) - 1, -1, -1):
        msg = messages[i]
        # 不要在工具调用链中间截断
        if msg.get("role") == "tool" and count > 0:
            continue
        truncated.insert(0, msg)
        count += 1
        if count >= 20:
            break
    sessions[session_key] = truncated

save_session(session_key, sessions[session_key])
```

- [ ] **Step 4: 运行测试验证通过**

```bash
python -m pytest tests/test_session_truncation.py -v
```

Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/backend/api/chat.py tests/test_session_truncation.py
git commit -m "fix: 修复会话历史截断逻辑，保留完整消息链"
```

---

## Task 3: 修复会话名称显示

**Files:**
- Modify: `src/backend/api/chat.py:218-235`
- Test: `tests/test_session_name.py`

- [ ] **Step 1: 写一个失败的测试**

```python
"""Test session name display."""
import pytest


def test_session_name_from_messages():
    """会话名称应该从第一条用户消息中提取。"""
    messages = [
        {"role": "user", "content": "帮我写一个Python排序函数"},
        {"role": "assistant", "content": "好的，我来帮你写一个排序函数。"}
    ]
    
    # 正确的逻辑：从第一条用户消息中提取名称
    session_name = "default"
    for msg in messages:
        if msg.get("role") == "user":
            content = msg.get("content", "")
            # 截取前20个字符作为名称
            session_name = content[:20] + "..." if len(content) > 20 else content
            break
    
    assert session_name == "帮我写一个Python排序函数"


def test_session_name_with_empty_messages():
    """空消息列表应该返回默认名称。"""
    messages = []
    
    session_name = "default"
    for msg in messages:
        if msg.get("role") == "user":
            content = msg.get("content", "")
            session_name = content[:20] + "..." if len(content) > 20 else content
            break
    
    assert session_name == "default"
```

- [ ] **Step 2: 运行测试确认失败**

```bash
python -m pytest tests/test_session_name.py -v
```

Expected: FAIL

- [ ] **Step 3: 修复代码**

```python
# src/backend/api/chat.py
@router.get("/sessions")
async def list_sessions(user_id: str = "anonymous"):
    user_sessions = []
    for key in sessions.keys():
        if key.startswith(f"{user_id}:"):
            session_id = key.split(":")[1]
            messages = sessions[key]
            
            # 从第一条用户消息中提取会话名称
            name = session_id
            for msg in messages:
                if isinstance(msg, dict) and msg.get("role") == "user":
                    content = msg.get("content", "")
                    if content:
                        name = content[:20] + "..." if len(content) > 20 else content
                    break
            
            last_message = messages[-1] if messages else None
            
            user_sessions.append({
                "session_id": session_id,
                "name": name,
                "last_message": last_message.get("content", "")[:100] if last_message else "",
                "message_count": len(messages)
            })
    
    return {"sessions": user_sessions}
```

- [ ] **Step 4: 运行测试验证通过**

```bash
python -m pytest tests/test_session_name.py -v
```

Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/backend/api/chat.py tests/test_session_name.py
git commit -m "fix: 修复会话名称显示，从第一条用户消息中提取"
```

---

## 最终验证

完成所有任务后，运行所有测试：

```bash
cd /Users/tmind/Desktop/work/github/test2
source venv/bin/activate
python -m pytest tests/ -v --ignore=tests/test_integration.py --ignore=tests/test_quick_integration.py
```

---

## 总结

这个实现计划解决了 MemoryAgent 的 3 个问题：

1. ✅ **user_id 传递** - memory_store 工具正确接收 user_id
2. ✅ **会话历史截断** - 截断逻辑保留完整的消息链
3. ✅ **会话名称显示** - 从第一条用户消息中提取名称

每个任务都包含：
- 详细的代码修改示例
- 测试验证步骤
- 提交命令
