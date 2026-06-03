"""
Memory exclusion rules for MemoryAI Agent.

Implements Claude Code's principle: "记该记的，不记能推导的"
(Record what should be recorded, don't record what can be derived)

Excluded information:
- Code patterns, project architecture, file structure
- Git history and recent changes
- Debugging solutions and fixes
- Content already in CLAUDE.md
- Temporary task states
"""

from typing import List, Set
from enum import Enum


class ExclusionReason(str, Enum):
    """Reason for excluding a memory."""
    DERIVABLE = "derivable"          # Can be derived from code
    EPHEMERAL = "ephemeral"          # Temporary, will become stale
    DUPLICATE = "duplicate"          # Already documented elsewhere
    REDUNDANT = "redundant"          # Can be re-executed


# Patterns that should NOT be stored as memories
EXCLUSION_PATTERNS = {
    # Code structure (can be derived from codebase)
    "code_structure": [
        "文件结构",
        "目录结构",
        "项目架构",
        "代码组织",
        "file structure",
        "directory structure",
        "函数名",
        "变量名",
        "类名",
        "function name",
        "variable name",
    ],
    
    # Git history (use git log instead)
    "git_history": [
        "git log",
        "git blame",
        "最近提交",
        "提交历史",
        "commit history",
        "last commit",
        "git diff",
        "git status",
    ],
    
    # Debugging solutions (already in code/commits)
    "debugging": [
        "修复方案",
        "bug修复",
        "debug",
        "fix",
        "解决方案",
        "排查步骤",
        "调试方法",
    ],
    
    # Temporary states
    "temporary": [
        "当前状态",
        "进行中",
        "待完成",
        "in progress",
        "todo",
        "临时",
        "暂时",
    ],
    
    # CLAUDE.md content (already documented)
    "claude_md": [
        "项目规范",
        "编码规范",
        "开发规范",
        "coding style",
        "code style",
    ],
}


# Memory types that are always excluded
EXCLUDED_MEMORY_TYPES = {
    "conversation_context",  # Session-level, not cross-session
    "tool_output",          # Can be re-executed
    "error_log",            # Ephemeral
}


def should_exclude(content: str, memory_type: str = None) -> bool:
    """
    Check if content should be excluded from memory.
    
    Args:
        content: Memory content to check
        memory_type: Type of memory
        
    Returns:
        True if should be excluded
    """
    content_lower = content.lower()
    
    # Check excluded types
    if memory_type in EXCLUDED_MEMORY_TYPES:
        return True
    
    # Check exclusion patterns
    for category, patterns in EXCLUSION_PATTERNS.items():
        for pattern in patterns:
            if pattern in content_lower:
                return True
    
    stripped = content.strip()
    if len(stripped) < 6:
        return True
    
    # Check if content is too long (likely raw output)
    if len(content) > 10000:
        return True
    
    return False


def get_exclusion_reason(content: str) -> ExclusionReason:
    """
    Get the reason for excluding content.
    
    Args:
        content: Memory content
        
    Returns:
        ExclusionReason
    """
    content_lower = content.lower()
    
    for category, patterns in EXCLUSION_PATTERNS.items():
        for pattern in patterns:
            if pattern in content_lower:
                if category == "code_structure":
                    return ExclusionReason.DERIVABLE
                elif category == "git_history":
                    return ExclusionReason.DERIVABLE
                elif category == "debugging":
                    return ExclusionReason.DUPLICATE
                elif category == "temporary":
                    return ExclusionReason.EPHEMERAL
    
    return ExclusionReason.REDUNDANT


# Documentation for users
EXCLUSION_GUIDELINES = """
## 记忆排除清单

以下信息 **不应该** 存入记忆：

### 可推导的信息 (DERIVABLE)
- 代码模式、项目架构、文件结构
- 通过 grep、git、文档可以获取的信息
- 已经在代码中的内容

### 临时信息 (EPHEMERAL)
- 当前任务状态
- 进行中的工作
- 临时调试信息

### 已记录的信息 (DUPLICATE)
- Git 历史和最近改动
- commit 消息中的内容
- 已在文档中记录的信息

### 可重复获取的信息 (REDUNDANT)
- 工具输出（可以重新执行）
- 搜索结果（可以重新搜索）
- 文件内容（可以重新读取）

---

**核心原则**: 如果信息可以从当前代码推导出来，就不要存入记忆。
因为代码是"活的"，随时在变，但记忆是"死的"，存下来就定格了。
"""
