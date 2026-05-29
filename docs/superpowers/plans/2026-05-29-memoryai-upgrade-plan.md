# MemoryAI 架构升级计划

基于 Claude Code 源码分析的架构优化方案

---

## 📋 执行摘要

本计划将 MemoryAI 从简单的请求-响应模式升级为专业的 Agent 架构，参考 Claude Code 的核心设计原则：

1. **Tool-Use Loop** - 替代简单请求-响应
2. **动态 System Prompt** - 分段组装 + 缓存优化
3. **四类型记忆系统** - user/feedback/project/reference
4. **五步上下文压缩** - 从轻到重的渐进式压缩
5. **Plan Mode** - 先规划后执行的工作流

---

## 🏗️ 架构对比

### 当前架构
```
用户消息 → LLM → 回复
           ↓
       简单记忆存储
```

### 目标架构 (Claude Code 风格)
```
用户消息 → Agent Loop → Tool Calls → 回复
              ↓
         ┌────┴────┐
         │ 记忆检索 │ ← Sonnet 预取
         └────┬────┘
              ↓
         ┌────┴────┐
         │ 上下文压缩 │ ← 5步渐进式
         └────┬────┘
              ↓
         ┌────┴────┐
         │ System Prompt │ ← 动态组装
         └─────────┘
```

---

## 📝 详细任务清单

### Phase 1: Agent Loop 核心 (Tool-Use Loop)

**目标**: 实现 Claude Code 的核心 while(true) 循环

#### Task 1.1: 定义工具接口规范
- **文件**: `src/agent/tools/base.py`
- **内容**:
  ```python
  from abc import ABC, abstractmethod
  from typing import Any, Dict, Optional
  from enum import Enum
  
  class ToolPermission(Enum):
      READ_ONLY = "read_only"
      READ_WRITE = "read_write"
      DESTRUCTIVE = "destructive"
  
  class BaseTool(ABC):
      name: str
      description: str
      permission: ToolPermission
      requires_confirmation: bool
      
      @abstractmethod
      async def execute(self, **kwargs) -> Dict[str, Any]:
          pass
  ```

#### Task 1.2: 实现工具注册表
- **文件**: `src/agent/tools/registry.py`
- **内容**: 工具发现、权限检查、并发执行编排

#### Task 1.3: 实现 Agent Loop
- **文件**: `src/agent/loop.py`
- **内容**:
  ```python
  async def agent_loop(messages, tools, max_turns=50):
      turn_count = 0
      
      while turn_count < max_turns:
          # 1. 压缩上下文 (5步策略)
          messages = await compress_context(messages)
          
          # 2. 调用 LLM
          response = await llm.chat(messages, tools)
          
          # 3. 检查终止条件
          if response.stop_reason == "end_turn":
              return response.content
          
          # 4. 执行工具调用
          tool_results = await execute_tools(response.tool_calls)
          
          # 5. 更新消息列表
          messages.extend(tool_results)
          turn_count += 1
  ```

#### Task 1.4: 更新 Chat API 使用 Agent Loop
- **文件**: `src/backend/api/chat.py`
- **改动**: 替换直接 LLM 调用为 Agent Loop

---

### Phase 2: 动态 System Prompt

**目标**: 实现 System Prompt 的分段组装和缓存优化

#### Task 2.1: 定义 Prompt Section 结构
- **文件**: `src/agent/prompts/sections.py`
- **内容**:
  ```python
  from dataclasses import dataclass
  from typing import Optional
  
  @dataclass
  class PromptSection:
      name: str
      content: str
      is_static: bool  # True = 所有用户相同, False = 因人而异
      cache_priority: int  # 越小越靠前，优先缓存
  ```

#### Task 2.2: 实现 Prompt 组装器
- **文件**: `src/agent/prompts/assembler.py`
- **内容**:
  - 角色定义 (静态)
  - 行为准则 (静态)
  - 安全约束 (静态)
  - Git 安全协议 (静态)
  - --- 分割线 ---
  - 环境信息 (动态)
  - 记忆索引 (动态)
  - MCP 指令 (动态)

#### Task 2.3: 实现 Prompt 缓存
- **文件**: `src/agent/prompts/cache.py`
- **内容**: 三级缓存体系 (全局/组织/会话)

---

### Phase 3: 四类型记忆系统

**目标**: 实现 Claude Code 的记忆分类体系

#### Task 3.1: 定义记忆类型
- **文件**: `src/memory/types.py`
- **内容**:
  ```python
  from enum import Enum
  
  class MemoryType(Enum):
      USER = "user"          # 用户画像
      FEEDBACK = "feedback"  # 行为反馈
      PROJECT = "project"    # 项目动态
      REFERENCE = "reference"  # 外部指针
  ```

#### Task 3.2: 重构记忆存储格式
- **文件**: `src/memory/storage.py`
- **内容**:
  - 每条记忆独立 .md 文件
  - YAML frontmatter 元信息
  - MEMORY.md 索引文件 (200行上限)

#### Task 3.3: 实现记忆召回机制
- **文件**: `src/memory/retrieval.py`
- **内容**:
  - 扫描记忆文件头部 (前30行)
  - Sonnet 侧查询选择
  - 陈旧度检测 (>1天警告)

#### Task 3.4: 实现记忆排除清单
- **文件**: `src/memory/exclusions.py`
- **内容**: 明确不存储的信息类型

---

### Phase 4: 五步上下文压缩

**目标**: 实现渐进式上下文管理

#### Task 4.1: 第1层 - 大结果存磁盘
- **文件**: `src/agent/context/layer1_persist.py`
- **内容**: 工具结果 >50KB 时存磁盘，保留 2KB 预览

#### Task 4.2: 第2层 - 砍掉远古消息
- **文件**: `src/agent/context/layer2_snip.py`
- **内容**: 移除对话开头的过时消息

#### Task 4.3: 第3层 - 裁剪老工具输出
- **文件**: `src/agent/context/layer3_micro_compact.py`
- **内容**: 时间衰减，清理可重新获取的工具结果

#### Task 4.4: 第4层 - 读时投影压缩
- **文件**: `src/agent/context/layer4_context_collapse.py`
- **内容**: 90%/95% 阈值触发，动态压缩视图

#### Task 4.5: 第5层 - 全量摘要
- **文件**: `src/agent/context/layer5_auto_compact.py`
- **内容**:
  - 触发阈值计算
  - 结构化摘要生成
  - 压缩后恢复 (最近5个文件)

---

### Phase 5: Plan Mode

**目标**: 实现先规划后执行的工作流

#### Task 5.1: 实现 Plan Mode 工具
- **文件**: `src/agent/tools/plan_mode.py`
- **内容**:
  - EnterPlanMode 工具
  - ExitPlanMode 工具
  - 权限降级为只读

#### Task 5.2: 实现 Plan 存储
- **文件**: `src/agent/plans/storage.py`
- **内容**: .claude/plans/ 目录管理

#### Task 5.3: 集成到 Agent Loop
- **文件**: `src/agent/loop.py`
- **改动**: 支持 Plan Mode 状态切换

---

### Phase 6: 前端升级

**目标**: 展示 Agent 工作过程

#### Task 6.1: 显示工具调用过程
- **文件**: `frontend/src/components/ChatPanel.tsx`
- **内容**: 展示工具调用、记忆检索、压缩事件

#### Task 6.2: 显示记忆系统状态
- **文件**: `frontend/src/components/MemoryPanel.tsx`
- **内容**: 四类型记忆可视化

#### Task 6.3: Plan Mode UI
- **文件**: `frontend/src/components/PlanModePanel.tsx`
- **内容**: 计划查看、审批界面

---

## 🔧 技术栈

| 组件 | 技术选型 |
|------|---------|
| Agent Loop | Python asyncio |
| 工具系统 | Abstract Base Class |
| 记忆存储 | Markdown + YAML |
| 上下文压缩 | 分层处理器 |
| 前端 | React + TypeScript |

---

## 📊 预期效果

| 指标 | 当前 | 升级后 |
|------|------|--------|
| Agent 能力 | 单轮问答 | 多轮工具调用 |
| 记忆精度 | 关键词匹配 | 语义检索 + 类型分类 |
| 上下文利用 | 简单截断 | 5步渐进压缩 |
| 响应质量 | 基础 | 专业级 |

---

## 🚀 执行顺序

```
Phase 1 (Agent Loop) 
    ↓
Phase 2 (System Prompt) 
    ↓
Phase 3 (记忆系统) 
    ↓
Phase 4 (上下文压缩) 
    ↓
Phase 5 (Plan Mode) 
    ↓
Phase 6 (前端升级)
```

每个 Phase 完成后进行测试验证，确保功能正常后再进入下一阶段。

---

## ⚠️ 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| API 调用成本增加 | 高 | 实施缓存优化，使用廉价模型做记忆检索 |
| 响应延迟增加 | 中 | 并行预取记忆，优化压缩策略 |
| 系统复杂度增加 | 中 | 模块化设计，完善测试覆盖 |

---

## 📚 参考资料

- Claude Code 源码分析文章
- Anthropic 官方文档
- Agent 架构最佳实践

---

*计划创建时间: 2026-05-29*
*预计完成时间: 分阶段实施*
