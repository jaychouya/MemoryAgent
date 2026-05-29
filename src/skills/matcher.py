"""
Skill Matcher for finding the best skill for a given task.

Uses multiple signals to match skills:
- Task description similarity
- Context match
- Success rate
- Tag relevance
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from src.skills.node import SkillNode
from src.skills.graph import SkillGraph


@dataclass
class SkillMatch:
    """Result of skill matching."""
    skill: SkillNode
    score: float
    reasons: List[str]


class SkillMatcher:
    """
    Matches skills to tasks using multiple signals.
    """
    
    def __init__(self, graph: SkillGraph):
        """
        Initialize matcher.
        
        Args:
            graph: SkillGraph to search
        """
        self.graph = graph
    
    def find_best_skill(
        self,
        task_description: str,
        context: Dict[str, Any] = None,
        tags: List[str] = None
    ) -> Optional[SkillMatch]:
        """
        Find the best skill for a task.
        
        Args:
            task_description: Description of the task
            context: Current context
            tags: Relevant tags
            
        Returns:
            Best SkillMatch or None
        """
        matches = self.find_matching_skills(task_description, context, tags)
        return matches[0] if matches else None
    
    def find_matching_skills(
        self,
        task_description: str,
        context: Dict[str, Any] = None,
        tags: List[str] = None,
        limit: int = 5
    ) -> List[SkillMatch]:
        """
        Find skills matching a task.
        
        Args:
            task_description: Task description
            context: Current context
            tags: Relevant tags
            limit: Maximum results
            
        Returns:
            List of SkillMatch sorted by score
        """
        # Get context-matching skills
        context = context or {}
        candidates = self.graph.find_matching_skills(context, tags, limit=20)
        
        # Score each candidate
        matches = []
        task_lower = task_description.lower()
        
        for skill in candidates:
            score, reasons = self._score_skill(skill, task_lower, context, tags)
            matches.append(SkillMatch(
                skill=skill,
                score=score,
                reasons=reasons
            ))
        
        # Sort by score
        matches.sort(key=lambda m: m.score, reverse=True)
        
        return matches[:limit]
    
    def _score_skill(
        self,
        skill: SkillNode,
        task_lower: str,
        context: Dict[str, Any],
        tags: List[str] = None
    ) -> tuple:
        """
        Score a skill for a task.
        
        Returns:
            (score, reasons) tuple
        """
        reasons = []
        score = 0.0
        
        # Name match
        if skill.name.lower() in task_lower or task_lower in skill.name.lower():
            score += 0.3
            reasons.append("Name matches task")
        
        # Description match
        if task_lower in skill.description.lower():
            score += 0.2
            reasons.append("Description matches task")
        
        # Tag match
        if tags:
            matching_tags = set(tags) & set(skill.tags)
            if matching_tags:
                tag_score = len(matching_tags) / len(tags)
                score += tag_score * 0.2
                reasons.append(f"Matching tags: {matching_tags}")
        
        # Context match
        context_score = skill.matches_context(context)
        score += context_score * 0.2
        if context_score > 0.8:
            reasons.append("High context match")
        
        # Success rate
        score += skill.success_rate * 0.1
        if skill.success_rate > 0.8:
            reasons.append("High success rate")
        
        return score, reasons
    
    def suggest_skills_for_project(
        self,
        project_context: Dict[str, Any]
    ) -> List[SkillMatch]:
        """
        Suggest skills for a project based on context.
        
        Args:
            project_context: Project context (framework, language, etc.)
            
        Returns:
            List of suggested skills
        """
        return self.find_matching_skills(
            task_description="",
            context=project_context,
            limit=10
        )
