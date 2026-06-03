"""Execution tracing system for observability."""

import logging
import time
import uuid
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class TraceEventType(str, Enum):
    """Types of trace events."""
    START = "start"
    END = "end"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    LLM_CALL = "llm_call"
    LLM_RESPONSE = "llm_response"
    ERROR = "error"
    MEMORY_SEARCH = "memory_search"
    MEMORY_STORE = "memory_store"


@dataclass
class TraceEvent:
    """A single trace event."""
    event_id: str
    trace_id: str
    event_type: TraceEventType
    timestamp: datetime
    data: Dict[str, Any] = field(default_factory=dict)
    parent_id: Optional[str] = None
    duration_ms: Optional[float] = None


@dataclass
class Trace:
    """A complete execution trace."""
    trace_id: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    events: List[TraceEvent] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration_ms(self) -> Optional[float]:
        if self.ended_at:
            return (self.ended_at - self.started_at).total_seconds() * 1000
        return None
    
    @property
    def token_usage(self) -> Dict[str, int]:
        """Calculate token usage from events."""
        total_input = 0
        total_output = 0
        
        for event in self.events:
            if event.event_type == TraceEventType.LLM_RESPONSE:
                usage = event.data.get("usage", {})
                total_input += usage.get("input_tokens", 0)
                total_output += usage.get("output_tokens", 0)
        
        return {
            "input_tokens": total_input,
            "output_tokens": total_output,
            "total_tokens": total_input + total_output
        }


class ExecutionTracer:
    """Manages execution traces for observability."""
    
    def __init__(self):
        self.traces: Dict[str, Trace] = {}
        self.current_trace_id: Optional[str] = None
    
    def start_trace(
        self,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Start a new trace."""
        trace_id = f"trace_{uuid.uuid4().hex[:12]}"
        
        trace = Trace(
            trace_id=trace_id,
            started_at=datetime.now(),
            metadata=metadata or {}
        )
        
        self.traces[trace_id] = trace
        self.current_trace_id = trace_id
        
        self._add_event(
            trace_id=trace_id,
            event_type=TraceEventType.START,
            data={"metadata": metadata or {}}
        )
        
        logger.info(f"Started trace: {trace_id}")
        return trace_id
    
    def end_trace(
        self,
        trace_id: str = None,
        status: str = "success"
    ):
        """End a trace."""
        trace_id = trace_id or self.current_trace_id
        if not trace_id or trace_id not in self.traces:
            return
        
        trace = self.traces[trace_id]
        trace.ended_at = datetime.now()
        
        self._add_event(
            trace_id=trace_id,
            event_type=TraceEventType.END,
            data={"status": status}
        )
        
        if trace_id == self.current_trace_id:
            self.current_trace_id = None
        
        logger.info(f"Ended trace: {trace_id} ({status})")
    
    def _add_event(
        self,
        trace_id: str,
        event_type: TraceEventType,
        data: Dict[str, Any] = None,
        parent_id: str = None
    ) -> str:
        """Add an event to trace."""
        if trace_id not in self.traces:
            return None
        
        event_id = f"evt_{uuid.uuid4().hex[:8]}"
        
        event = TraceEvent(
            event_id=event_id,
            trace_id=trace_id,
            event_type=event_type,
            timestamp=datetime.now(),
            data=data or {},
            parent_id=parent_id
        )
        
        self.traces[trace_id].events.append(event)
        return event_id
    
    def trace_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        trace_id: str = None
    ) -> str:
        """Trace a tool call."""
        trace_id = trace_id or self.current_trace_id
        if not trace_id:
            return None
        
        return self._add_event(
            trace_id=trace_id,
            event_type=TraceEventType.TOOL_CALL,
            data={
                "tool_name": tool_name,
                "arguments": arguments
            }
        )
    
    def trace_tool_result(
        self,
        tool_name: str,
        result: Any,
        success: bool,
        duration_ms: float,
        trace_id: str = None
    ):
        """Trace a tool result."""
        trace_id = trace_id or self.current_trace_id
        if not trace_id:
            return
        
        self._add_event(
            trace_id=trace_id,
            event_type=TraceEventType.TOOL_RESULT,
            data={
                "tool_name": tool_name,
                "result": str(result)[:500],  # Truncate long results
                "success": success,
                "duration_ms": duration_ms
            }
        )
    
    def trace_llm_call(
        self,
        model: str,
        messages: List[Dict],
        trace_id: str = None
    ) -> str:
        """Trace an LLM call."""
        trace_id = trace_id or self.current_trace_id
        if not trace_id:
            return None
        
        return self._add_event(
            trace_id=trace_id,
            event_type=TraceEventType.LLM_CALL,
            data={
                "model": model,
                "message_count": len(messages)
            }
        )
    
    def trace_llm_response(
        self,
        model: str,
        response: str,
        usage: Dict[str, int],
        duration_ms: float,
        trace_id: str = None
    ):
        """Trace an LLM response."""
        trace_id = trace_id or self.current_trace_id
        if not trace_id:
            return
        
        self._add_event(
            trace_id=trace_id,
            event_type=TraceEventType.LLM_RESPONSE,
            data={
                "model": model,
                "response_length": len(response),
                "usage": usage,
                "duration_ms": duration_ms
            }
        )
    
    def trace_error(
        self,
        error: str,
        context: Dict[str, Any] = None,
        trace_id: str = None
    ):
        """Trace an error."""
        trace_id = trace_id or self.current_trace_id
        if not trace_id:
            return
        
        self._add_event(
            trace_id=trace_id,
            event_type=TraceEventType.ERROR,
            data={
                "error": error,
                "context": context or {}
            }
        )
    
    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """Get a trace by ID."""
        return self.traces.get(trace_id)
    
    def get_recent_traces(self, limit: int = 10) -> List[Trace]:
        """Get recent traces."""
        traces = sorted(
            self.traces.values(),
            key=lambda t: t.started_at,
            reverse=True
        )
        return traces[:limit]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get tracing statistics."""
        total_traces = len(self.traces)
        completed_traces = sum(
            1 for t in self.traces.values() if t.ended_at
        )
        
        total_tokens = sum(
            t.token_usage["total_tokens"]
            for t in self.traces.values()
        )
        
        avg_duration = None
        durations = [
            t.duration_ms for t in self.traces.values()
            if t.duration_ms is not None
        ]
        if durations:
            avg_duration = sum(durations) / len(durations)
        
        return {
            "total_traces": total_traces,
            "completed_traces": completed_traces,
            "total_tokens": total_tokens,
            "avg_duration_ms": avg_duration
        }
    
    def clear(self):
        """Clear all traces."""
        self.traces.clear()
        self.current_trace_id = None


# Global tracer instance
_tracer: Optional[ExecutionTracer] = None


def get_tracer() -> ExecutionTracer:
    """Get or create global tracer instance."""
    global _tracer
    if _tracer is None:
        _tracer = ExecutionTracer()
    return _tracer
