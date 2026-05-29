"""
Base tool interface for MemoryAI Agent.

Inspired by Claude Code's tool system:
- Each tool has a clear permission level
- Tools declare if they require confirmation
- Tools declare if they can run in parallel
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from enum import Enum
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class ToolPermission(str, Enum):
    """Tool permission levels - controls what a tool can do."""
    
    # Read-only operations (safe to auto-execute)
    READ_ONLY = "read_only"
    
    # Read-write operations (may modify local state)
    READ_WRITE = "read_write"
    
    # Destructive operations (requires explicit confirmation)
    DESTRUCTIVE = "destructive"


@dataclass
class ToolResult:
    """Result from a tool execution."""
    
    success: bool
    content: Any
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        result = {
            "success": self.success,
            "content": self.content,
        }
        if self.error:
            result["error"] = self.error
        if self.metadata:
            result["metadata"] = self.metadata
        return result


class BaseTool(ABC):
    """
    Abstract base class for all Agent tools.
    
    Each tool must declare:
    - name: Unique identifier
    - description: What the tool does (for LLM)
    - permission: What level of access it needs
    - requires_confirmation: If user must approve before execution
    - can_run_parallel: If multiple instances can run concurrently
    
    This design follows Claude Code's principle:
    "Tools declare their safety properties at compile time,
     not runtime."
    """
    
    # Tool metadata (must be set by subclasses)
    name: str = ""
    description: str = ""
    permission: ToolPermission = ToolPermission.READ_ONLY
    requires_confirmation: bool = False
    can_run_parallel: bool = True
    
    # Parameters schema (for LLM function calling)
    parameters: Dict[str, Any] = {}
    
    def __init_subclass__(cls, **kwargs):
        """Validate subclass has required attributes."""
        super().__init_subclass__(**kwargs)
        
        # Skip validation for abstract subclasses
        if hasattr(cls, '__abstractmethods__') and cls.__abstractmethods__:
            return
            
        if not cls.name:
            raise ValueError(f"Tool class {cls.__name__} must define 'name'")
        if not cls.description:
            raise ValueError(f"Tool class {cls.__name__} must define 'description'")
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """
        Execute the tool with given parameters.
        
        Args:
            **kwargs: Tool-specific parameters
            
        Returns:
            ToolResult with success status and content
        """
        pass
    
    def to_function_schema(self) -> Dict[str, Any]:
        """
        Convert tool to OpenAI function calling schema.
        
        Returns:
            Dict in OpenAI function format
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }
    
    async def validate_params(self, **kwargs) -> bool:
        """
        Validate parameters before execution.
        
        Override in subclass to add custom validation.
        
        Returns:
            True if valid, raises ValueError if not
        """
        return True


class ReadOnlyTool(BaseTool):
    """Convenience base class for read-only tools."""
    permission = ToolPermission.READ_ONLY
    requires_confirmation = False


class ReadWriteTool(BaseTool):
    """Convenience base class for read-write tools."""
    permission = ToolPermission.READ_WRITE
    requires_confirmation = False


class DestructiveTool(BaseTool):
    """Convenience base class for destructive tools."""
    permission = ToolPermission.DESTRUCTIVE
    requires_confirmation = True
