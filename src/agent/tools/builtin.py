"""
Built-in tools for MemoryAI Agent.

These tools provide core functionality:
- Memory search
- Memory store
- Context retrieval
"""

from typing import Any, Dict, List
from src.agent.tools.base import ReadOnlyTool, ReadWriteTool, ToolResult


class MemorySearchTool(ReadOnlyTool):
    """Search through memory system."""
    
    name = "memory_search"
    description = "搜索记忆系统，查找相关信息"
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "搜索关键词或问题"
            },
            "top_k": {
                "type": "integer",
                "description": "返回结果数量",
                "default": 5
            }
        },
        "required": ["query"]
    }
    
    def __init__(self, memory_manager):
        self.memory = memory_manager
    
    async def execute(self, query: str, top_k: int = 5, **kwargs) -> ToolResult:
        """Search memories."""
        try:
            # Get user_id from context if available
            user_id = kwargs.get("user_id", "anonymous")
            
            results = await self.memory.retrieve(
                user_id=user_id,
                query=query,
                top_k=top_k
            )
            
            if not results:
                return ToolResult(
                    success=True,
                    content="暂无相关记忆。这是新对话，请直接回答用户的问题。"
                )
            
            # Format results
            content = "找到以下相关记忆：\n\n"
            for i, result in enumerate(results[:top_k], 1):
                # result 是 dict，包含 content, score 等字段
                memory_content = result.get("content", "无内容")
                score = result.get("score", 0)
                content += f"{i}. {memory_content}\n"
                content += f"   (相关度: {score:.2f})\n\n"
            
            return ToolResult(
                success=True,
                content=content,
                metadata={"count": len(results)}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                content=None,
                error=f"记忆搜索失败: {str(e)}"
            )


class MemoryStoreTool(ReadWriteTool):
    """Store information to memory."""
    
    name = "memory_store"
    description = "存储信息到记忆系统"
    parameters = {
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "要存储的内容"
            },
            "memory_type": {
                "type": "string",
                "enum": ["user", "feedback", "project", "reference"],
                "description": "记忆类型"
            },
            "importance": {
                "type": "number",
                "description": "重要性分数 (0-1)",
                "default": 0.5
            }
        },
        "required": ["content", "memory_type"]
    }
    
    def __init__(self, memory_manager):
        self.memory = memory_manager
    
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
            
            # 获取用户上下文
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
    
    def _generate_description(self, content: str, memory_type: str) -> str:
        """Generate a meaningful description for the memory."""
        # 截取前30个字符作为基础
        base = content[:30] if len(content) > 30 else content
        
        # 根据类型添加前缀
        type_prefixes = {
            "user": "用户偏好",
            "feedback": "行为反馈",
            "project": "项目动态",
            "reference": "外部引用"
        }
        
        prefix = type_prefixes.get(memory_type, "记忆")
        return f"{prefix}：{base}"


class ContextRetrieveTool(ReadOnlyTool):
    """Retrieve conversation context."""
    
    name = "context_retrieve"
    description = "获取当前对话上下文"
    parameters = {
        "type": "object",
        "properties": {
            "last_n": {
                "type": "integer",
                "description": "获取最近N条消息",
                "default": 5
            }
        }
    }
    
    async def execute(self, last_n: int = 5, **kwargs) -> ToolResult:
        """Get conversation context."""
        messages = kwargs.get("messages", [])
        
        recent = messages[-last_n:] if messages else []
        
        if not recent:
            return ToolResult(
                success=True,
                content="暂无对话历史。"
            )
        
        content = "最近的对话：\n\n"
        for msg in recent:
            role = "用户" if msg.get("role") == "user" else "助手"
            content += f"**{role}**: {msg.get('content', '')[:100]}...\n\n"
        
        return ToolResult(
            success=True,
            content=content
        )


# Export all built-in tools
BUILTIN_TOOLS = [
    MemorySearchTool,
    MemoryStoreTool,
    ContextRetrieveTool,
]
