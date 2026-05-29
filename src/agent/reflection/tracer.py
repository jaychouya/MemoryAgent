"""
Execution tracer for recording tool call sequences.

Records complete execution traces including:
- Tool calls with parameters and results
- Timing information
- Success/failure status
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from pathlib import Path
import hashlib


@dataclass
class ToolCall:
    """
    Records a single tool call.
    
    Attributes:
        tool_name: Name of the tool called
        parameters: Parameters passed to the tool
        result: Result returned by the tool
        timestamp: When the call was made
        duration_ms: How long the call took
    """
    tool_name: str
    parameters: Dict[str, Any]
    result: Any
    timestamp: datetime = field(default_factory=datetime.now)
    duration_ms: float = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tool_name": self.tool_name,
            "parameters": self.parameters,
            "result": str(self.result)[:500],  # Truncate long results
            "timestamp": self.timestamp.isoformat(),
            "duration_ms": self.duration_ms
        }


@dataclass
class ExecutionTrace:
    """
    Records a complete execution trace.
    
    Attributes:
        id: Unique trace identifier
        task_description: What the task was about
        tool_calls: List of tool calls made
        start_time: When execution started
        end_time: When execution ended
        success: Whether the task succeeded
        metadata: Additional metadata
    """
    id: str
    task_description: str
    tool_calls: List[ToolCall]
    start_time: datetime
    end_time: Optional[datetime] = None
    success: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration_seconds(self) -> float:
        """Calculate total duration in seconds."""
        if not self.end_time:
            return 0
        return (self.end_time - self.start_time).total_seconds()
    
    @property
    def tool_sequence(self) -> List[str]:
        """Get sequence of tool names."""
        return [call.tool_name for call in self.tool_calls]
    
    def to_pattern(self) -> str:
        """Convert to pattern string for comparison."""
        return "->".join(self.tool_sequence)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "task_description": self.task_description,
            "tool_calls": [call.to_dict() for call in self.tool_calls],
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "success": self.success,
            "metadata": self.metadata
        }


class ExecutionTracer:
    """
    Records execution traces for analysis.
    
    Usage:
        tracer = ExecutionTracer()
        tracer.start_trace("Deploy to Vercel")
        tracer.record_tool_call("npm", {"args": "install"}, result)
        tracer.record_tool_call("vercel", {"args": "deploy"}, result)
        tracer.end_trace(success=True)
    """
    
    def __init__(self, storage_path: str = "traces"):
        """
        Initialize tracer.
        
        Args:
            storage_path: Path to store trace files
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._current_trace: Optional[ExecutionTrace] = None
        self._traces: List[ExecutionTrace] = []
        self._load_traces()
    
    def start_trace(self, task_description: str) -> str:
        """
        Start recording a new trace.
        
        Args:
            task_description: Description of the task
            
        Returns:
            Trace ID
        """
        trace_id = hashlib.md5(
            f"{task_description}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:8]
        
        self._current_trace = ExecutionTrace(
            id=trace_id,
            task_description=task_description,
            tool_calls=[],
            start_time=datetime.now()
        )
        
        return trace_id
    
    def record_tool_call(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        result: Any,
        duration_ms: float = 0
    ):
        """
        Record a tool call in current trace.
        
        Args:
            tool_name: Name of the tool
            parameters: Tool parameters
            result: Tool result
            duration_ms: Call duration in milliseconds
        """
        if not self._current_trace:
            return
        
        call = ToolCall(
            tool_name=tool_name,
            parameters=parameters,
            result=result,
            duration_ms=duration_ms
        )
        
        self._current_trace.tool_calls.append(call)
    
    def end_trace(self, success: bool = True, metadata: Dict[str, Any] = None):
        """
        End current trace and save.
        
        Args:
            success: Whether the task succeeded
            metadata: Additional metadata
        """
        if not self._current_trace:
            return
        
        self._current_trace.end_time = datetime.now()
        self._current_trace.success = success
        
        if metadata:
            self._current_trace.metadata.update(metadata)
        
        self._traces.append(self._current_trace)
        self._save_trace(self._current_trace)
        
        self._current_trace = None
    
    def get_traces(self, limit: int = 100) -> List[ExecutionTrace]:
        """Get recent traces."""
        return self._traces[-limit:]
    
    def get_successful_traces(self) -> List[ExecutionTrace]:
        """Get only successful traces."""
        return [t for t in self._traces if t.success]
    
    def _save_trace(self, trace: ExecutionTrace):
        """Save trace to disk."""
        filepath = self.storage_path / f"trace_{trace.id}.json"
        
        with open(filepath, "w") as f:
            json.dump(trace.to_dict(), f, indent=2)
    
    def _load_traces(self):
        """Load traces from disk."""
        for filepath in self.storage_path.glob("trace_*.json"):
            try:
                with open(filepath) as f:
                    data = json.load(f)
                
                trace = ExecutionTrace(
                    id=data["id"],
                    task_description=data["task_description"],
                    tool_calls=[
                        ToolCall(
                            tool_name=call["tool_name"],
                            parameters=call["parameters"],
                            result=call["result"],
                            timestamp=datetime.fromisoformat(call["timestamp"]),
                            duration_ms=call.get("duration_ms", 0)
                        )
                        for call in data["tool_calls"]
                    ],
                    start_time=datetime.fromisoformat(data["start_time"]),
                    end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
                    success=data.get("success", True),
                    metadata=data.get("metadata", {})
                )
                
                self._traces.append(trace)
            except Exception as e:
                print(f"Warning: Failed to load trace {filepath}: {e}")
