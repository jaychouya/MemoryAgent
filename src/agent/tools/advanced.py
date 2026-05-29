"""
Advanced tools for MemoryAI Agent.

Integrates the new semantic, skill graph, and reflection features.
"""

from typing import Any, Dict, List
from src.agent.tools.base import ReadOnlyTool, ReadWriteTool, ToolResult
from src.agent.semantic.patcher import SemanticPatcher
from src.skills.graph import SkillGraph
from src.skills.matcher import SkillMatcher
from src.agent.reflection.tracer import ExecutionTracer
from src.agent.reflection.generator import SkillGenerator


class SemanticPatchTool(ReadWriteTool):
    """Tool for applying semantic code patches."""
    
    name = "semantic_patch"
    description = "Apply code changes using semantic matching (AST-based)"
    parameters = {
        "type": "object",
        "properties": {
            "file_content": {
                "type": "string",
                "description": "Current file content"
            },
            "old_pattern": {
                "type": "string",
                "description": "Code pattern to find (can be semantically different)"
            },
            "new_pattern": {
                "type": "string",
                "description": "Replacement code"
            },
            "language": {
                "type": "string",
                "description": "Programming language",
                "default": "python"
            }
        },
        "required": ["file_content", "old_pattern", "new_pattern"]
    }
    
    def __init__(self):
        self.patcher = SemanticPatcher()
    
    async def execute(
        self,
        file_content: str,
        old_pattern: str,
        new_pattern: str,
        language: str = "python",
        **kwargs
    ) -> ToolResult:
        result = self.patcher.find_and_replace(
            file_content, old_pattern, new_pattern, language
        )
        
        if result.success:
            return ToolResult(
                success=True,
                content=result.modified_content,
                metadata={
                    "similarity": result.match.similarity if result.match else None,
                    "message": result.message
                }
            )
        else:
            return ToolResult(
                success=False,
                content=None,
                error=result.message
            )


class SkillSearchTool(ReadOnlyTool):
    """Tool for searching skills in the knowledge graph."""
    
    name = "skill_search"
    description = "Search for relevant skills based on context"
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "What you're trying to do"
            },
            "context": {
                "type": "object",
                "description": "Project context (framework, language, etc.)",
                "default": {}
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Filter by tags",
                "default": []
            }
        },
        "required": ["query"]
    }
    
    def __init__(self, graph: SkillGraph):
        self.matcher = SkillMatcher(graph)
    
    async def execute(
        self,
        query: str,
        context: Dict = None,
        tags: List[str] = None,
        **kwargs
    ) -> ToolResult:
        matches = self.matcher.find_matching_skills(
            query, context or {}, tags
        )
        
        if not matches:
            return ToolResult(
                success=True,
                content="No matching skills found."
            )
        
        content = "Found matching skills:\n\n"
        for match in matches[:5]:
            content += f"### {match.skill.name}\n"
            content += f"**Score**: {match.score:.2f}\n"
            content += f"**Description**: {match.skill.description}\n"
            if match.reasons:
                content += f"**Reasons**: {', '.join(match.reasons)}\n"
            content += "\n"
        
        return ToolResult(
            success=True,
            content=content,
            metadata={"count": len(matches)}
        )


class SkillCreateTool(ReadWriteTool):
    """Tool for creating new skills."""
    
    name = "skill_create"
    description = "Create a new skill in the knowledge graph"
    parameters = {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Skill name"
            },
            "description": {
                "type": "string",
                "description": "What the skill does"
            },
            "content": {
                "type": "string",
                "description": "Skill instructions/content"
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Categorization tags",
                "default": []
            },
            "prerequisites": {
                "type": "object",
                "description": "Requirements to use this skill",
                "default": {}
            }
        },
        "required": ["name", "description", "content"]
    }
    
    def __init__(self, graph: SkillGraph):
        self.graph = graph
    
    async def execute(
        self,
        name: str,
        description: str,
        content: str,
        tags: List[str] = None,
        prerequisites: Dict = None,
        **kwargs
    ) -> ToolResult:
        from src.skills.node import SkillNode
        
        skill = SkillNode.create(
            name=name,
            description=description,
            content=content,
            tags=tags or [],
            prerequisites=prerequisites or {}
        )
        
        self.graph.add_skill(skill)
        
        return ToolResult(
            success=True,
            content=f"Skill '{name}' created successfully with ID: {skill.id}",
            metadata={"skill_id": skill.id}
        )


class TraceAnalysisTool(ReadOnlyTool):
    """Tool for analyzing execution traces."""
    
    name = "trace_analysis"
    description = "Analyze execution traces to discover patterns"
    parameters = {
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "description": "Number of traces to analyze",
                "default": 50
            },
            "min_frequency": {
                "type": "integer",
                "description": "Minimum pattern frequency",
                "default": 3
            }
        }
    }
    
    def __init__(self, tracer: ExecutionTracer):
        self.tracer = tracer
        self.generator = SkillGenerator()
    
    async def execute(
        self,
        limit: int = 50,
        min_frequency: int = 3,
        **kwargs
    ) -> ToolResult:
        traces = self.tracer.get_traces(limit)
        
        if not traces:
            return ToolResult(
                success=True,
                content="No traces recorded yet."
            )
        
        skills = self.generator.generate_from_traces(
            traces,
            min_frequency=min_frequency
        )
        
        if not skills:
            return ToolResult(
                success=True,
                content=f"Analyzed {len(traces)} traces but found no recurring patterns."
            )
        
        content = f"Analyzed {len(traces)} traces. Found {len(skills)} patterns:\n\n"
        for skill in skills[:5]:
            content += f"### {skill.name}\n"
            content += f"{skill.description}\n"
            content += f"Success rate: {skill.success_rate:.0%}\n\n"
        
        return ToolResult(
            success=True,
            content=content,
            metadata={"patterns_found": len(skills)}
        )
