"""
Skill generator for creating skills from patterns.

Automatically generates skill definitions from
discovered execution patterns.
"""

from typing import List, Dict, Any
from .analyzer import Pattern
from .tracer import ExecutionTrace
from src.skills.node import SkillNode
import hashlib


class SkillGenerator:
    """
    Generate skills from discovered patterns.
    
    Takes execution patterns and creates reusable skill definitions
    that can be stored in the skill knowledge graph.
    """
    
    def generate_from_pattern(
        self,
        pattern: Pattern,
        traces: List[ExecutionTrace],
        llm_service=None
    ) -> SkillNode:
        """
        Generate a skill from a discovered pattern.
        
        Args:
            pattern: Discovered pattern
            traces: Example traces
            llm_service: Optional LLM for generating descriptions
            
        Returns:
            Generated SkillNode
        """
        # Get example traces
        example_traces = [
            trace for trace in traces
            if trace.id in pattern.examples
        ]
        
        # Generate content
        content = self._generate_content(pattern, example_traces)
        
        # Generate prerequisites
        prerequisites = self._infer_prerequisites(example_traces)
        
        # Create skill
        skill_id = hashlib.md5(
            pattern.pattern_string.encode()
        ).hexdigest()[:8]
        
        return SkillNode(
            id=f"auto_{skill_id}",
            name=f"Workflow: {pattern.sequence[0]} → {pattern.sequence[-1]}",
            description=pattern.description,
            content=content,
            prerequisites=prerequisites,
            dependencies=[],
            tags=["auto-generated", pattern.sequence[0]],
            success_count=round(pattern.frequency * pattern.success_rate),
            failure_count=round(pattern.frequency * (1 - pattern.success_rate))
        )
    
    def _generate_content(
        self,
        pattern: Pattern,
        traces: List[ExecutionTrace]
    ) -> str:
        """
        Generate skill content from pattern.
        
        Args:
            pattern: The pattern
            traces: Example traces
            
        Returns:
            Skill content in markdown
        """
        lines = [
            "# Auto-Generated Skill",
            "",
            "## Pattern",
            "",
            "```",
            pattern.pattern_string,
            "```",
            "",
            "## Statistics",
            "",
            f"- **Frequency**: {pattern.frequency} occurrences",
            f"- **Success rate**: {pattern.success_rate:.0%}",
            "",
            "## Steps",
            ""
        ]
        
        for i, step in enumerate(pattern.sequence, 1):
            lines.append(f"{i}. `{step}`")
        
        lines.extend([
            "",
            "## Example Tasks",
            ""
        ])
        
        for trace in traces[:3]:
            lines.append(f"- {trace.task_description}")
        
        lines.extend([
            "",
            "## Usage Notes",
            "",
            "This skill was automatically generated from execution traces.",
            "Review and refine before using in production."
        ])
        
        return "\n".join(lines)
    
    def _infer_prerequisites(
        self,
        traces: List[ExecutionTrace]
    ) -> Dict[str, Any]:
        """
        Infer prerequisites from traces.
        
        Analyzes tool usage to determine what's needed.
        """
        prerequisites = {}
        
        # Analyze tool usage patterns
        tools_used = set()
        for trace in traces:
            for call in trace.tool_calls:
                tools_used.add(call.tool_name)
        
        # Map tools to prerequisites
        if any(t in tools_used for t in ["npm", "yarn", "pnpm"]):
            prerequisites["runtime"] = "node"
        
        if any(t in tools_used for t in ["pip", "python", "poetry"]):
            prerequisites["runtime"] = "python"
        
        if "git" in tools_used:
            prerequisites["vcs"] = "git"
        
        if any(t in tools_used for t in ["docker", "docker-compose"]):
            prerequisites["container"] = "docker"
        
        return prerequisites
    
    def generate_from_traces(
        self,
        traces: List[ExecutionTrace],
        min_pattern_length: int = 2,
        min_frequency: int = 3
    ) -> List[SkillNode]:
        """
        Generate multiple skills from traces.
        
        Args:
            traces: Execution traces
            min_pattern_length: Minimum pattern length
            min_frequency: Minimum frequency
            
        Returns:
            List of generated skills
        """
        from .analyzer import SequenceAnalyzer
        
        analyzer = SequenceAnalyzer(
            min_pattern_length=min_pattern_length,
            min_frequency=min_frequency
        )
        
        patterns = analyzer.discover_patterns(traces)
        
        skills = []
        for pattern in patterns:
            skill = self.generate_from_pattern(pattern, traces)
            skills.append(skill)
        
        return skills
