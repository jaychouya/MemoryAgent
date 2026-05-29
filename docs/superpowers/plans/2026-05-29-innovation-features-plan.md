# MemoryAI 高级创新功能实施计划

基于 Claude Code 架构原则的三个创新功能 + 回复质量优化

---

## 📋 执行摘要

本计划将实现三个高级创新功能，使 MemoryAI 具备更强的代码理解、知识管理和学习能力：

1. **语义化冲突解决（Semantic Patch）** - 使用 AST 进行代码匹配
2. **跨项目知识图谱迁移（Cross-Project Skill Graph）** - 技能知识图谱
3. **执行轨迹自动抽象为技能（Trace-to-Skill）** - 自动技能生成
4. **回复质量优化** - 提高回复文本长度和质量

---

## 🎯 功能一：语义化冲突解决（Semantic Patch）

### 问题分析

当前问题：
- 基于文本的 `oldString` 匹配在代码格式化后会失败
- 逻辑等价重构（变量重命名、格式调整）会导致匹配失败
- Agent 无法理解"代码意图"，只能做字符串匹配

### 解决方案

使用 tree-sitter 将代码解析为 AST，通过 AST 相似度进行语义匹配。

### 架构设计

```
src/
├── agent/
│   └── semantic/
│       ├── __init__.py
│       ├── parser.py          # AST 解析器
│       ├── matcher.py         # AST 匹配器
│       ├── differ.py          # 语义 diff
│       └── patcher.py         # 语义 patch
```

### 实现步骤

#### Step 1: 安装依赖

```bash
pip install tree-sitter tree-sitter-python tree-sitter-javascript
```

#### Step 2: 实现 AST 解析器

**文件**: `src/agent/semantic/parser.py`

```python
"""
AST Parser for semantic code understanding.

Uses tree-sitter to parse code into AST for semantic matching.
"""

import tree_sitter_python as tspython
import tree_sitter_javascript as tsjavascript
from tree_sitter import Language, Parser, Node
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import hashlib


@dataclass
class ASTNode:
    """Represents an AST node with metadata."""
    type: str
    text: str
    start_line: int
    end_line: int
    children: List["ASTNode"]
    hash: str = ""
    
    def __post_init__(self):
        if not self.hash:
            self.hash = self._compute_hash()
    
    def _compute_hash(self) -> str:
        """Compute hash based on structure, not text."""
        structure = f"{self.type}:{len(self.children)}"
        return hashlib.md5(structure.encode()).hexdigest()[:8]


class CodeParser:
    """Parse code into AST using tree-sitter."""
    
    def __init__(self):
        self._parsers = {}
        self._init_parsers()
    
    def _init_parsers(self):
        """Initialize language parsers."""
        # Python
        PY_LANGUAGE = Language(tspython.language())
        self._parsers["python"] = Parser(PY_LANGUAGE)
        
        # JavaScript
        JS_LANGUAGE = Language(tsjavascript.language())
        self._parsers["javascript"] = Parser(JS_LANGUAGE)
    
    def parse(self, code: str, language: str = "python") -> Optional[ASTNode]:
        """Parse code into AST."""
        parser = self._parsers.get(language)
        if not parser:
            return None
        
        tree = parser.parse(bytes(code, "utf8"))
        return self._convert_node(tree.root_node)
    
    def _convert_node(self, node: Node) -> ASTNode:
        """Convert tree-sitter node to ASTNode."""
        children = [self._convert_node(child) for child in node.children]
        
        return ASTNode(
            type=node.type,
            text=node.text.decode("utf8") if node.text else "",
            start_line=node.start_point[0],
            end_line=node.end_point[0],
            children=children
        )
```

#### Step 3: 实现 AST 匹配器

**文件**: `src/agent/semantic/matcher.py`

```python
"""
AST Matcher for semantic code matching.

Finds semantically similar code blocks using AST comparison.
"""

from typing import List, Optional, Tuple
from dataclasses import dataclass
from .parser import ASTNode


@dataclass
class MatchResult:
    """Result of AST matching."""
    node: ASTNode
    similarity: float
    start_line: int
    end_line: int


class ASTMatcher:
    """Match code blocks using AST similarity."""
    
    def find_similar(
        self,
        target: ASTNode,
        source: ASTNode,
        threshold: float = 0.7
    ) -> List[MatchResult]:
        """Find nodes in source similar to target."""
        results = []
        
        # Compare target with each node in source
        for source_node in self._walk_ast(source):
            similarity = self._compute_similarity(target, source_node)
            
            if similarity >= threshold:
                results.append(MatchResult(
                    node=source_node,
                    similarity=similarity,
                    start_line=source_node.start_line,
                    end_line=source_node.end_line
                ))
        
        # Sort by similarity
        results.sort(key=lambda r: r.similarity, reverse=True)
        return results
    
    def _compute_similarity(self, node1: ASTNode, node2: ASTNode) -> float:
        """Compute similarity between two AST nodes."""
        # Type match
        type_score = 1.0 if node1.type == node2.type else 0.0
        
        # Structure match (children count)
        max_children = max(len(node1.children), len(node2.children), 1)
        structure_score = 1.0 - abs(len(node1.children) - len(node2.children)) / max_children
        
        # Hash match (structural hash)
        hash_score = 1.0 if node1.hash == node2.hash else 0.0
        
        # Weighted average
        return (type_score * 0.4 + structure_score * 0.3 + hash_score * 0.3)
    
    def _walk_ast(self, node: ASTNode):
        """Walk through all nodes in AST."""
        yield node
        for child in node.children:
            yield from self._walk_ast(child)
```

#### Step 4: 实现语义 Patcher

**文件**: `src/agent/semantic/patcher.py`

```python
"""
Semantic Patcher for code modification.

Applies patches based on AST matching instead of text matching.
"""

from typing import Optional, List
from .parser import CodeParser, ASTNode
from .matcher import ASTMatcher, MatchResult


class SemanticPatcher:
    """Apply code patches using semantic matching."""
    
    def __init__(self):
        self.parser = CodeParser()
        self.matcher = ASTMatcher()
    
    def find_and_replace(
        self,
        file_content: str,
        old_pattern: str,
        new_pattern: str,
        language: str = "python"
    ) -> Optional[str]:
        """
        Find and replace using semantic matching.
        
        Args:
            file_content: Current file content
            old_pattern: Pattern to find (can be semantically different)
            new_pattern: Replacement pattern
            language: Programming language
            
        Returns:
            Modified content or None if no match
        """
        # Parse both
        file_ast = self.parser.parse(file_content, language)
        pattern_ast = self.parser.parse(old_pattern, language)
        
        if not file_ast or not pattern_ast:
            return None
        
        # Find similar nodes
        matches = self.matcher.find_similar(pattern_ast, file_ast)
        
        if not matches:
            return None
        
        # Get best match
        best_match = matches[0]
        
        # Replace in original content
        lines = file_content.split("\n")
        
        # Replace matched lines with new pattern
        new_lines = (
            lines[:best_match.start_line] +
            new_pattern.split("\n") +
            lines[best_match.end_line + 1:]
        )
        
        return "\n".join(new_lines)
```

---

## 🎯 功能二：跨项目知识图谱迁移（Cross-Project Skill Graph）

### 问题分析

当前问题：
- 技能是孤立的 markdown 文件
- 无法表达技能间的依赖关系
- 无法根据项目上下文选择合适技能
- 跨项目技能迁移困难

### 解决方案

建立技能知识图谱，使用 networkx 实现图存储和查询。

### 架构设计

```
src/
├── skills/
│   ├── __init__.py
│   ├── graph.py           # 技能图谱核心
│   ├── node.py            # 技能节点定义
│   ├── matcher.py         # 技能匹配器
│   └── migrator.py        # 技能迁移器
```

### 实现步骤

#### Step 1: 安装依赖

```bash
pip install networkx
```

#### Step 2: 定义技能节点

**文件**: `src/skills/node.py`

```python
"""
Skill node definition for knowledge graph.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime


@dataclass
class SkillNode:
    """Represents a skill in the knowledge graph."""
    
    id: str
    name: str
    description: str
    content: str
    
    # Prerequisites
    prerequisites: Dict[str, Any] = field(default_factory=dict)
    # Example: {"framework": "next.js", "node_version": ">=18", "database": "postgresql"}
    
    # Dependencies
    dependencies: List[str] = field(default_factory=list)
    # Example: ["npm", "git", "docker"]
    
    # Success/Feedback tracking
    success_count: int = 0
    failure_count: int = 0
    feedback: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        total = self.success_count + self.failure_count
        if total == 0:
            return 0.5  # Default
        return self.success_count / total
    
    def matches_context(self, context: Dict[str, Any]) -> float:
        """Calculate how well this skill matches the given context."""
        if not self.prerequisites:
            return 1.0  # No prerequisites = always matches
        
        matches = 0
        total = len(self.prerequisites)
        
        for key, required_value in self.prerequisites.items():
            actual_value = context.get(key)
            
            if actual_value is None:
                continue
            
            if self._values_match(required_value, actual_value):
                matches += 1
        
        return matches / total if total > 0 else 1.0
    
    def _values_match(self, required: Any, actual: Any) -> bool:
        """Check if values match (supports version ranges, etc.)."""
        if isinstance(required, str) and isinstance(actual, str):
            # Simple string match
            return required.lower() in actual.lower() or actual.lower() in required.lower()
        
        return required == actual
```

#### Step 3: 实现技能图谱

**文件**: `src/skills/graph.py`

```python
"""
Skill Knowledge Graph implementation.

Uses networkx for graph storage and querying.
"""

import networkx as nx
from typing import List, Dict, Any, Optional, Set
from .node import SkillNode
import json
from pathlib import Path


class SkillGraph:
    """Knowledge graph for skills."""
    
    def __init__(self, storage_path: str = "skills/graph"):
        self.graph = nx.DiGraph()
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._load()
    
    def add_skill(self, skill: SkillNode):
        """Add a skill to the graph."""
        # Add node with attributes
        self.graph.add_node(
            skill.id,
            skill=skill,
            name=skill.name,
            tags=skill.tags
        )
        
        # Add dependency edges
        for dep_id in skill.dependencies:
            if dep_id in self.graph:
                self.graph.add_edge(skill.id, dep_id, type="depends_on")
        
        self._save()
    
    def remove_skill(self, skill_id: str):
        """Remove a skill from the graph."""
        if skill_id in self.graph:
            self.graph.remove_node(skill_id)
            self._save()
    
    def get_skill(self, skill_id: str) -> Optional[SkillNode]:
        """Get a skill by ID."""
        if skill_id in self.graph:
            return self.graph.nodes[skill_id].get("skill")
        return None
    
    def find_matching_skills(
        self,
        context: Dict[str, Any],
        tags: List[str] = None,
        limit: int = 5
    ) -> List[SkillNode]:
        """Find skills matching the given context."""
        candidates = []
        
        for node_id in self.graph.nodes:
            skill = self.graph.nodes[node_id].get("skill")
            if not skill:
                continue
            
            # Calculate context match score
            context_score = skill.matches_context(context)
            
            # Calculate tag match score
            tag_score = 1.0
            if tags:
                matching_tags = set(tags) & set(skill.tags)
                tag_score = len(matching_tags) / len(tags) if tags else 1.0
            
            # Calculate overall score
            score = (context_score * 0.6 + tag_score * 0.2 + skill.success_rate * 0.2)
            
            candidates.append((skill, score))
        
        # Sort by score
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        return [skill for skill, score in candidates[:limit]]
    
    def get_related_skills(
        self,
        skill_id: str,
        max_distance: int = 2
    ) -> List[SkillNode]:
        """Get skills related to the given skill."""
        if skill_id not in self.graph:
            return []
        
        related = set()
        
        # BFS to find related skills
        queue = [(skill_id, 0)]
        visited = {skill_id}
        
        while queue:
            current_id, distance = queue.pop(0)
            
            if distance >= max_distance:
                continue
            
            # Get neighbors
            for neighbor in self.graph.neighbors(current_id):
                if neighbor not in visited:
                    visited.add(neighbor)
                    related.add(neighbor)
                    queue.append((neighbor, distance + 1))
            
            # Get predecessors
            for predecessor in self.graph.predecessors(current_id):
                if predecessor not in visited:
                    visited.add(predecessor)
                    related.add(predecessor)
                    queue.append((predecessor, distance + 1))
        
        return [
            self.graph.nodes[nid].get("skill")
            for nid in related
            if "skill" in self.graph.nodes[nid]
        ]
    
    def _save(self):
        """Save graph to disk."""
        data = {}
        
        for node_id in self.graph.nodes:
            skill = self.graph.nodes[node_id].get("skill")
            if skill:
                data[node_id] = {
                    "id": skill.id,
                    "name": skill.name,
                    "description": skill.description,
                    "content": skill.content,
                    "prerequisites": skill.prerequisites,
                    "dependencies": skill.dependencies,
                    "tags": skill.tags,
                    "success_count": skill.success_count,
                    "failure_count": skill.failure_count
                }
        
        filepath = self.storage_path / "graph.json"
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
    
    def _load(self):
        """Load graph from disk."""
        filepath = self.storage_path / "graph.json"
        
        if not filepath.exists():
            return
        
        with open(filepath) as f:
            data = json.load(f)
        
        for node_id, skill_data in data.items():
            skill = SkillNode(**skill_data)
            self.add_skill(skill)
```

---

## 🎯 功能三：执行轨迹自动抽象为技能（Trace-to-Skill）

### 问题分析

当前问题：
- 技能创建依赖简单启发式（5+ tool calls）
- 宝贵经验隐藏在工具调用序列中
- 缺乏自动化的模式识别

### 解决方案

使用序列对齐算法发现可复用模式，自动生成技能初稿。

### 架构设计

```
src/
├── agent/
│   └── reflection/
│       ├── __init__.py
│       ├── tracer.py        # 执行轨迹记录
│       ├── analyzer.py      # 序列分析器
│       └── generator.py     # 技能生成器
```

### 实现步骤

#### Step 1: 实现执行轨迹记录器

**文件**: `src/agent/reflection/tracer.py`

```python
"""
Execution tracer for recording tool call sequences.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import json


@dataclass
class ToolCall:
    """Records a single tool call."""
    tool_name: str
    parameters: Dict[str, Any]
    result: Any
    timestamp: datetime = field(default_factory=datetime.now)
    duration_ms: float = 0


@dataclass
class ExecutionTrace:
    """Records a complete execution trace."""
    id: str
    task_description: str
    tool_calls: List[ToolCall]
    start_time: datetime
    end_time: Optional[datetime] = None
    success: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration_seconds(self) -> float:
        """Calculate total duration."""
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


class ExecutionTracer:
    """Records execution traces for analysis."""
    
    def __init__(self, storage_path: str = "traces"):
        self.storage_path = storage_path
        self._current_trace: Optional[ExecutionTrace] = None
        self._traces: List[ExecutionTrace] = []
    
    def start_trace(self, task_description: str) -> str:
        """Start recording a new trace."""
        import hashlib
        trace_id = hashlib.md5(task_description.encode()).hexdigest()[:8]
        
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
        """Record a tool call in current trace."""
        if not self._current_trace:
            return
        
        call = ToolCall(
            tool_name=tool_name,
            parameters=parameters,
            result=result,
            duration_ms=duration_ms
        )
        
        self._current_trace.tool_calls.append(call)
    
    def end_trace(self, success: bool = True):
        """End current trace and save."""
        if not self._current_trace:
            return
        
        self._current_trace.end_time = datetime.now()
        self._current_trace.success = success
        
        self._traces.append(self._current_trace)
        self._save_trace(self._current_trace)
        
        self._current_trace = None
    
    def get_traces(self, limit: int = 100) -> List[ExecutionTrace]:
        """Get recent traces."""
        return self._traces[-limit:]
    
    def _save_trace(self, trace: ExecutionTrace):
        """Save trace to disk."""
        import os
        os.makedirs(self.storage_path, exist_ok=True)
        
        filepath = os.path.join(self.storage_path, f"trace_{trace.id}.json")
        
        data = {
            "id": trace.id,
            "task_description": trace.task_description,
            "tool_calls": [
                {
                    "tool_name": call.tool_name,
                    "parameters": call.parameters,
                    "timestamp": call.timestamp.isoformat()
                }
                for call in trace.tool_calls
            ],
            "start_time": trace.start_time.isoformat(),
            "end_time": trace.end_time.isoformat() if trace.end_time else None,
            "success": trace.success
        }
        
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
```

#### Step 2: 实现序列分析器

**文件**: `src/agent/reflection/analyzer.py`

```python
"""
Sequence analyzer for discovering reusable patterns.
"""

from typing import List, Dict, Tuple, Set
from collections import Counter
from dataclasses import dataclass
from .tracer import ExecutionTrace


@dataclass
class Pattern:
    """Represents a discovered pattern."""
    sequence: List[str]
    frequency: int
    success_rate: float
    examples: List[str]  # Trace IDs


class SequenceAnalyzer:
    """Analyzes tool call sequences to discover patterns."""
    
    def __init__(self, min_pattern_length: int = 2, min_frequency: int = 3):
        self.min_pattern_length = min_pattern_length
        self.min_frequency = min_frequency
    
    def discover_patterns(
        self,
        traces: List[ExecutionTrace]
    ) -> List[Pattern]:
        """Discover recurring patterns in traces."""
        # Extract all sequences
        sequences = [trace.tool_sequence for trace in traces]
        
        # Find frequent subsequences
        patterns = self._find_frequent_subsequences(sequences, traces)
        
        # Filter by minimum frequency
        patterns = [p for p in patterns if p.frequency >= self.min_frequency]
        
        # Sort by frequency
        patterns.sort(key=lambda p: p.frequency, reverse=True)
        
        return patterns
    
    def _find_frequent_subsequences(
        self,
        sequences: List[List[str]],
        traces: List[ExecutionTrace]
    ) -> List[Pattern]:
        """Find frequent subsequences using sliding window."""
        pattern_counts: Counter = Counter()
        pattern_examples: Dict[str, List[str]] = {}
        
        for i, seq in enumerate(sequences):
            # Generate subsequences of different lengths
            for length in range(self.min_pattern_length, len(seq) + 1):
                for start in range(len(seq) - length + 1):
                    subseq = tuple(seq[start:start + length])
                    pattern_str = "->".join(subseq)
                    
                    pattern_counts[pattern_str] += 1
                    
                    if pattern_str not in pattern_examples:
                        pattern_examples[pattern_str] = []
                    pattern_examples[pattern_str].append(traces[i].id)
        
        # Convert to Pattern objects
        patterns = []
        for pattern_str, count in pattern_counts.items():
            sequence = pattern_str.split("->")
            
            # Calculate success rate for this pattern
            success_count = sum(
                1 for trace in traces
                if self._sequence_contains(trace.tool_sequence, sequence) and trace.success
            )
            success_rate = success_count / count if count > 0 else 0
            
            patterns.append(Pattern(
                sequence=sequence,
                frequency=count,
                success_rate=success_rate,
                examples=list(set(pattern_examples[pattern_str]))[:5]
            ))
        
        return patterns
    
    def _sequence_contains(self, full_sequence: List[str], subsequence: List[str]) -> bool:
        """Check if full sequence contains subsequence."""
        if len(subsequence) > len(full_sequence):
            return False
        
        for i in range(len(full_sequence) - len(subsequence) + 1):
            if full_sequence[i:i + len(subsequence)] == subsequence:
                return True
        
        return False
```

#### Step 3: 实现技能生成器

**文件**: `src/agent/reflection/generator.py`

```python
"""
Skill generator for creating skills from patterns.
"""

from typing import List, Dict, Any
from .analyzer import Pattern
from .tracer import ExecutionTrace
from src.skills.node import SkillNode
import hashlib


class SkillGenerator:
    """Generate skills from discovered patterns."""
    
    def generate_from_pattern(
        self,
        pattern: Pattern,
        traces: List[ExecutionTrace],
        llm_service=None
    ) -> SkillNode:
        """Generate a skill from a discovered pattern."""
        # Get example traces
        example_traces = [
            trace for trace in traces
            if trace.id in pattern.examples
        ]
        
        # Generate description
        description = self._generate_description(pattern, example_traces)
        
        # Generate content
        content = self._generate_content(pattern, example_traces)
        
        # Generate prerequisites
        prerequisites = self._infer_prerequisites(example_traces)
        
        # Create skill
        skill_id = hashlib.md5(
            "->".join(pattern.sequence).encode()
        ).hexdigest()[:8]
        
        return SkillNode(
            id=f"auto_{skill_id}",
            name=f"Auto-generated: {pattern.sequence[0]} → {pattern.sequence[-1]}",
            description=description,
            content=content,
            prerequisites=prerequisites,
            dependencies=[],
            tags=["auto-generated", pattern.sequence[0]],
            success_count=int(pattern.frequency * pattern.success_rate),
            failure_count=int(pattern.frequency * (1 - pattern.success_rate))
        )
    
    def _generate_description(
        self,
        pattern: Pattern,
        traces: List[ExecutionTrace]
    ) -> str:
        """Generate skill description."""
        # Simple description based on pattern
        steps = " → ".join(pattern.sequence)
        
        return f"""Automatically generated skill based on {pattern.frequency} observed executions.

Pattern: {steps}
Success rate: {pattern.success_rate:.0%}

This skill captures a common workflow pattern discovered from execution traces."""
    
    def _generate_content(
        self,
        pattern: Pattern,
        traces: List[ExecutionTrace]
    ) -> str:
        """Generate skill content."""
        lines = [
            "# Auto-Generated Skill",
            "",
            f"## Pattern",
            "",
            "```",
            " → ".join(pattern.sequence),
            "```",
            "",
            f"## Statistics",
            "",
            f"- Frequency: {pattern.frequency} occurrences",
            f"- Success rate: {pattern.success_rate:.0%}",
            "",
            "## Steps",
            ""
        ]
        
        for i, step in enumerate(pattern.sequence, 1):
            lines.append(f"{i}. Call `{step}`")
        
        lines.extend([
            "",
            "## Example Usage",
            ""
        ])
        
        for trace in traces[:3]:
            lines.append(f"- Task: {trace.task_description}")
        
        return "\n".join(lines)
    
    def _infer_prerequisites(
        self,
        traces: List[ExecutionTrace]
    ) -> Dict[str, Any]:
        """Infer prerequisites from traces."""
        prerequisites = {}
        
        # Analyze tool usage patterns
        tools_used = set()
        for trace in traces:
            for call in trace.tool_calls:
                tools_used.add(call.tool_name)
        
        # Map tools to prerequisites
        if "npm" in tools_used or "yarn" in tools_used:
            prerequisites["runtime"] = "node"
        
        if "pip" in tools_used or "python" in tools_used:
            prerequisites["runtime"] = "python"
        
        if "git" in tools_used:
            prerequisites["vcs"] = "git"
        
        return prerequisites
```

---

## 🎯 功能四：回复质量优化

### 问题分析

当前问题：
- 回复文本太短，缺乏详细解释
- 没有提供足够的上下文和示例
- 缺少结构化的格式

### 解决方案

优化 System Prompt，增加回复长度和质量要求。

### 实现步骤

#### Step 1: 更新 System Prompt

**文件**: `src/agent/prompts/sections.py`

```python
OUTPUT_STYLE = PromptSection(
    name="output_style",
    content="""## 输出规范

### 回复质量要求
1. **详细完整**：提供全面的解释，不要过于简洁
2. **结构清晰**：使用标题、列表、代码块等格式组织内容
3. **中文优先**：默认使用中文回答，除非用户使用英文提问
4. **提供示例**：在适当的地方提供代码示例或实际案例
5. **解释原因**：不仅说"怎么做"，还要解释"为什么这样做"

### 回复长度指导
- 简单问题：至少 200 字
- 中等复杂度：300-500 字
- 复杂问题：500-1000 字
- 技术解释：包含代码示例和详细说明

### 格式规范
- 使用 `#` 标题分层
- 使用 `1.` 有序列表展示步骤
- 使用 `-` 无序列表列举要点
- 使用 ``` 代码块展示代码
- 使用 **加粗** 强调重点
- 使用 > 引用块提供补充说明

### 回答结构
1. **直接回答**：先给出核心答案
2. **详细解释**：展开说明原因和背景
3. **示例演示**：提供代码或实际案例
4. **注意事项**：列出常见陷阱或最佳实践
5. **扩展阅读**：建议进一步学习的方向""",
    section_type=SectionType.STATIC,
    cache_priority=40
)
```

#### Step 2: 更新 LLM 调用参数

**文件**: `src/backend/services/__init__.py`

```python
# 增加 max_tokens
kwargs = {
    "model": self.model,
    "messages": api_messages,
    "temperature": 0.7,
    "max_tokens": 4000  # 从 2000 增加到 4000
}
```

---

## 📊 实施计划

### Phase 1: 语义化冲突解决 (1-2天)

1. 安装 tree-sitter 依赖
2. 实现 AST 解析器
3. 实现 AST 匹配器
4. 实现语义 Patcher
5. 集成到工具系统

### Phase 2: 技能知识图谱 (1-2天)

1. 安装 networkx 依赖
2. 实现技能节点定义
3. 实现技能图谱
4. 实现技能匹配器
5. 集成到 Agent 系统

### Phase 3: 执行轨迹抽象 (1-2天)

1. 实现执行轨迹记录器
2. 实现序列分析器
3. 实现技能生成器
4. 集成到反思系统

### Phase 4: 回复质量优化 (0.5天)

1. 更新 System Prompt
2. 调整 LLM 参数
3. 测试回复质量

---

## 🔧 技术依赖

```bash
pip install tree-sitter tree-sitter-python tree-sitter-javascript networkx
```

---

## 📚 参考资料

1. tree-sitter 官方文档: https://tree-sitter.github.io/
2. networkx 官方文档: https://networkx.org/
3. 序列模式挖掘算法: https://en.wikipedia.org/wiki/Sequential_pattern_mining

---

*计划创建时间: 2026-05-29*
*预计完成时间: 4-7天*
