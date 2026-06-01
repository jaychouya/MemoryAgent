"""
Unit tests for Trace-to-Skill module.
"""

import pytest
import tempfile
import shutil
from datetime import datetime
from src.agent.reflection.tracer import ExecutionTracer, ExecutionTrace, ToolCall
from src.agent.reflection.analyzer import SequenceAnalyzer, Pattern
from src.agent.reflection.generator import SkillGenerator


class TestExecutionTracer:
    """Tests for ExecutionTracer."""
    
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.tracer = ExecutionTracer(storage_path=self.temp_dir)
    
    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_start_trace(self):
        trace_id = self.tracer.start_trace("Deploy to Vercel")
        
        assert trace_id is not None
        assert len(trace_id) == 8
    
    def test_record_tool_call(self):
        self.tracer.start_trace("Test task")
        self.tracer.record_tool_call(
            tool_name="npm",
            parameters={"args": "install"},
            result="success",
            duration_ms=100
        )
        
        traces = self.tracer.get_traces()
        assert len(traces) == 0
    
    def test_end_trace(self):
        self.tracer.start_trace("Test task")
        self.tracer.record_tool_call("npm", {"args": "install"}, "success")
        self.tracer.end_trace(success=True)
        
        traces = self.tracer.get_traces()
        assert len(traces) == 1
        assert traces[0].success is True
    
    def test_get_traces(self):
        self.tracer.start_trace("Task 1")
        self.tracer.end_trace(success=True)
        
        self.tracer.start_trace("Task 2")
        self.tracer.end_trace(success=False)
        
        traces = self.tracer.get_traces()
        assert len(traces) == 2
    
    def test_get_successful_traces(self):
        self.tracer.start_trace("Task 1")
        self.tracer.end_trace(success=True)
        
        self.tracer.start_trace("Task 2")
        self.tracer.end_trace(success=False)
        
        successful = self.tracer.get_successful_traces()
        assert len(successful) == 1


class TestExecutionTrace:
    """Tests for ExecutionTrace."""
    
    def test_tool_sequence(self):
        trace = ExecutionTrace(
            id="test",
            task_description="Test task",
            tool_calls=[
                ToolCall(tool_name="npm", parameters={}, result=""),
                ToolCall(tool_name="git", parameters={}, result=""),
                ToolCall(tool_name="vercel", parameters={}, result="")
            ],
            start_time=datetime.now()
        )
        
        assert trace.tool_sequence == ["npm", "git", "vercel"]
    
    def test_to_pattern(self):
        trace = ExecutionTrace(
            id="test",
            task_description="Test task",
            tool_calls=[
                ToolCall(tool_name="npm", parameters={}, result=""),
                ToolCall(tool_name="git", parameters={}, result="")
            ],
            start_time=datetime.now()
        )
        
        assert trace.to_pattern() == "npm->git"
    
    def test_duration_seconds(self):
        trace = ExecutionTrace(
            id="test",
            task_description="Test task",
            tool_calls=[],
            start_time=datetime.now(),
            end_time=datetime.now()
        )
        
        assert trace.duration_seconds >= 0


class TestSequenceAnalyzer:
    """Tests for SequenceAnalyzer."""
    
    def test_discover_patterns(self):
        analyzer = SequenceAnalyzer(min_pattern_length=2, min_frequency=2)
        
        traces = [
            ExecutionTrace(
                id="1",
                task_description="Task 1",
                tool_calls=[
                    ToolCall(tool_name="npm", parameters={}, result=""),
                    ToolCall(tool_name="git", parameters={}, result=""),
                    ToolCall(tool_name="vercel", parameters={}, result="")
                ],
                start_time=datetime.now(),
                success=True
            ),
            ExecutionTrace(
                id="2",
                task_description="Task 2",
                tool_calls=[
                    ToolCall(tool_name="npm", parameters={}, result=""),
                    ToolCall(tool_name="git", parameters={}, result=""),
                    ToolCall(tool_name="vercel", parameters={}, result="")
                ],
                start_time=datetime.now(),
                success=True
            ),
            ExecutionTrace(
                id="3",
                task_description="Task 3",
                tool_calls=[
                    ToolCall(tool_name="npm", parameters={}, result=""),
                    ToolCall(tool_name="git", parameters={}, result=""),
                    ToolCall(tool_name="aws", parameters={}, result="")
                ],
                start_time=datetime.now(),
                success=True
            )
        ]
        
        patterns = analyzer.discover_patterns(traces)
        
        assert len(patterns) > 0
        assert any(p.frequency >= 2 for p in patterns)
    
    def test_no_patterns_for_single_trace(self):
        analyzer = SequenceAnalyzer(min_pattern_length=2, min_frequency=3)
        
        traces = [
            ExecutionTrace(
                id="1",
                task_description="Task 1",
                tool_calls=[
                    ToolCall(tool_name="npm", parameters={}, result=""),
                    ToolCall(tool_name="git", parameters={}, result="")
                ],
                start_time=datetime.now(),
                success=True
            )
        ]
        
        patterns = analyzer.discover_patterns(traces)
        
        assert len(patterns) == 0


class TestPattern:
    """Tests for Pattern."""
    
    def test_pattern_string(self):
        pattern = Pattern(
            sequence=["npm", "git", "vercel"],
            frequency=5,
            success_rate=0.8,
            examples=["1", "2", "3"]
        )
        
        assert pattern.pattern_string == "npm -> git -> vercel"
    
    def test_to_dict(self):
        pattern = Pattern(
            sequence=["npm", "git"],
            frequency=3,
            success_rate=0.9,
            examples=["1", "2"],
            description="Test pattern"
        )
        
        data = pattern.to_dict()
        
        assert data["sequence"] == ["npm", "git"]
        assert data["frequency"] == 3
        assert data["success_rate"] == 0.9


class TestSkillGenerator:
    """Tests for SkillGenerator."""
    
    def test_generate_from_pattern(self):
        generator = SkillGenerator()
        
        pattern = Pattern(
            sequence=["npm", "git", "vercel"],
            frequency=5,
            success_rate=0.8,
            examples=["1", "2"]
        )
        
        traces = [
            ExecutionTrace(
                id="1",
                task_description="Deploy to Vercel",
                tool_calls=[
                    ToolCall(tool_name="npm", parameters={}, result=""),
                    ToolCall(tool_name="git", parameters={}, result=""),
                    ToolCall(tool_name="vercel", parameters={}, result="")
                ],
                start_time=datetime.now(),
                success=True
            )
        ]
        
        skill = generator.generate_from_pattern(pattern, traces)
        
        assert skill.name.startswith("Workflow:")
        assert "auto-generated" in skill.tags
        assert skill.success_count == 4
        assert skill.failure_count == 1
    
    def test_generate_from_traces(self):
        generator = SkillGenerator()
        
        traces = [
            ExecutionTrace(
                id=str(i),
                task_description=f"Task {i}",
                tool_calls=[
                    ToolCall(tool_name="npm", parameters={}, result=""),
                    ToolCall(tool_name="git", parameters={}, result=""),
                    ToolCall(tool_name="vercel", parameters={}, result="")
                ],
                start_time=datetime.now(),
                success=True
            )
            for i in range(5)
        ]
        
        skills = generator.generate_from_traces(traces, min_frequency=3)
        
        assert len(skills) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
