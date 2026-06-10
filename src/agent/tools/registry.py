"""
Tool Registry for MemoryAI Agent.

Manages tool discovery, permission checks, and execution orchestration.
Inspired by Claude Code's tool system.
"""

import logging
from typing import Dict, List, Optional, Set
from concurrent.futures import ThreadPoolExecutor
import asyncio

from src.agent.tools.base import BaseTool, ToolPermission, ToolResult

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Central registry for all Agent tools.
    
    Responsibilities:
    - Tool registration and discovery
    - Permission checking
    - Parallel/serial execution orchestration
    - Tool schema generation for LLM
    """
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._initialized = False
    
    def register(self, tool: BaseTool) -> None:
        """
        Register a tool.
        
        Args:
            tool: Tool instance to register
            
        Raises:
            ValueError: If tool name already registered
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' already registered")
        
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name} ({tool.permission.value})")
    
    def register_many(self, tools: List[BaseTool]) -> None:
        """Register multiple tools."""
        for tool in tools:
            self.register(tool)
    
    def get(self, name: str) -> Optional[BaseTool]:
        """Get tool by name."""
        return self._tools.get(name)
    
    def get_all(self) -> List[BaseTool]:
        """Get all registered tools."""
        return list(self._tools.values())
    
    def get_by_permission(self, permission: ToolPermission) -> List[BaseTool]:
        """Get tools filtered by permission level."""
        return [t for t in self._tools.values() if t.permission == permission]
    
    def get_read_only(self) -> List[BaseTool]:
        """Get all read-only tools."""
        return self.get_by_permission(ToolPermission.READ_ONLY)
    
    def get_function_schemas(self, exclude: Optional[Set[str]] = None) -> List[Dict]:
        """
        Get all tool schemas for LLM function calling.
        
        Returns:
            List of OpenAI function schemas
        """
        excluded = exclude or set()
        return [
            tool.to_function_schema()
            for tool in self._tools.values()
            if tool.name not in excluded
        ]
    
    def check_permission(self, tool_name: str, action: str = "execute") -> bool:
        """
        Check if a tool operation is allowed.
        
        Args:
            tool_name: Name of the tool
            action: Action being performed
            
        Returns:
            True if allowed
        """
        tool = self.get(tool_name)
        if not tool:
            return False
        
        # Destructive tools always require confirmation
        if tool.permission == ToolPermission.DESTRUCTIVE:
            return tool.requires_confirmation
        
        return True
    
    async def execute(
        self,
        tool_name: str,
        params: Dict,
        require_confirmation: bool = True
    ) -> ToolResult:
        """
        Execute a single tool.
        
        Args:
            tool_name: Name of tool to execute
            params: Parameters for the tool
            require_confirmation: If True, check if tool needs user approval
            
        Returns:
            ToolResult from execution
        """
        tool = self.get(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                content=None,
                error=f"Tool '{tool_name}' not found"
            )
        
        # Check if confirmation required
        if require_confirmation and tool.requires_confirmation:
            return ToolResult(
                success=False,
                content=None,
                error=f"Tool '{tool_name}' requires user confirmation",
                metadata={"requires_confirmation": True}
            )
        
        try:
            # Validate params
            await tool.validate_params(**params)
            
            # Execute
            result = await tool.execute(**params)
            return result
            
        except Exception as e:
            logger.error(f"Tool '{tool_name}' execution failed: {e}")
            return ToolResult(
                success=False,
                content=None,
                error=str(e)
            )
    
    async def execute_parallel(
        self,
        tool_calls: List[Dict],
        max_workers: int = 5
    ) -> List[ToolResult]:
        """
        Execute multiple tool calls in parallel.
        
        Only parallelizable tools are run concurrently.
        Non-parallelizable tools are queued.
        
        Args:
            tool_calls: List of {"tool": name, "params": {...}}
            max_workers: Maximum concurrent executions
            
        Returns:
            List of ToolResult in same order as input
        """
        results = [None] * len(tool_calls)
        
        # Separate parallelizable and serial tools
        parallel_calls = []
        serial_calls = []
        
        for i, call in enumerate(tool_calls):
            tool = self.get(call["tool"])
            if tool and tool.can_run_parallel:
                parallel_calls.append((i, call))
            else:
                serial_calls.append((i, call))
        
        # Execute parallel calls
        if parallel_calls:
            tasks = []
            for i, call in parallel_calls:
                task = self.execute(
                    call["tool"],
                    call["params"],
                    require_confirmation=False
                )
                tasks.append((i, task))
            
            # Gather results
            gathered = await asyncio.gather(
                *[t for _, t in tasks],
                return_exceptions=True
            )
            
            for (i, _), result in zip(tasks, gathered):
                if isinstance(result, Exception):
                    results[i] = ToolResult(
                        success=False,
                        content=None,
                        error=str(result)
                    )
                else:
                    results[i] = result
        
        # Execute serial calls
        for i, call in serial_calls:
            results[i] = await self.execute(
                call["tool"],
                call["params"],
                require_confirmation=False
            )
        
        return results
    
    def get_stats(self) -> Dict:
        """Get registry statistics."""
        return {
            "total_tools": len(self._tools),
            "by_permission": {
                "read_only": len(self.get_read_only()),
                "read_write": len(self.get_by_permission(ToolPermission.READ_WRITE)),
                "destructive": len(self.get_by_permission(ToolPermission.DESTRUCTIVE)),
            }
        }


# Global registry instance
_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Get or create global tool registry."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry
