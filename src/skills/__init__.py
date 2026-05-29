"""
Skill Knowledge Graph module.

Provides skill management with:
- Skill nodes with prerequisites and dependencies
- Graph-based storage and querying
- Context-aware skill matching
- Cross-project skill migration
"""

from src.skills.node import SkillNode
from src.skills.graph import SkillGraph
from src.skills.matcher import SkillMatcher

__all__ = [
    "SkillNode",
    "SkillGraph",
    "SkillMatcher"
]
