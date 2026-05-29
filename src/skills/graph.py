"""
Skill Knowledge Graph implementation.

Uses networkx for graph storage and querying.
Provides:
- Skill storage and retrieval
- Context-aware skill matching
- Dependency tracking
- Related skill discovery
"""

import networkx as nx
from typing import List, Dict, Any, Optional, Set
from pathlib import Path
import json
from datetime import datetime

from src.skills.node import SkillNode


class SkillGraph:
    """
    Knowledge graph for skills.
    
    Features:
    - Graph-based storage using networkx
    - Context-aware skill matching
    - Dependency tracking
    - Related skill discovery
    - Persistence to disk
    """
    
    def __init__(self, storage_path: str = "skills/graph"):
        """
        Initialize skill graph.
        
        Args:
            storage_path: Path to store graph data
        """
        self.graph = nx.DiGraph()
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._load()
    
    def add_skill(self, skill: SkillNode):
        """
        Add a skill to the graph.
        
        Args:
            skill: SkillNode to add
        """
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
        """
        Remove a skill from the graph.
        
        Args:
            skill_id: ID of skill to remove
        """
        if skill_id in self.graph:
            self.graph.remove_node(skill_id)
            self._save()
    
    def get_skill(self, skill_id: str) -> Optional[SkillNode]:
        """
        Get a skill by ID.
        
        Args:
            skill_id: Skill identifier
            
        Returns:
            SkillNode if found, None otherwise
        """
        if skill_id in self.graph:
            return self.graph.nodes[skill_id].get("skill")
        return None
    
    def find_matching_skills(
        self,
        context: Dict[str, Any],
        tags: List[str] = None,
        limit: int = 5
    ) -> List[SkillNode]:
        """
        Find skills matching the given context.
        
        Args:
            context: Current project/environment context
            tags: Optional tags to filter by
            limit: Maximum results
            
        Returns:
            List of matching SkillNodes sorted by relevance
        """
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
            score = (
                context_score * 0.5 +
                tag_score * 0.2 +
                skill.success_rate * 0.3
            )
            
            candidates.append((skill, score))
        
        # Sort by score
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        return [skill for skill, score in candidates[:limit]]
    
    def get_related_skills(
        self,
        skill_id: str,
        max_distance: int = 2
    ) -> List[SkillNode]:
        """
        Get skills related to the given skill.
        
        Args:
            skill_id: Source skill ID
            max_distance: Maximum graph distance
            
        Returns:
            List of related SkillNodes
        """
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
            
            # Get neighbors (both directions)
            for neighbor in self.graph.neighbors(current_id):
                if neighbor not in visited:
                    visited.add(neighbor)
                    related.add(neighbor)
                    queue.append((neighbor, distance + 1))
            
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
    
    def get_all_skills(self) -> List[SkillNode]:
        """Get all skills in the graph."""
        return [
            self.graph.nodes[nid].get("skill")
            for nid in self.graph.nodes
            if "skill" in self.graph.nodes[nid]
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get graph statistics."""
        skills = self.get_all_skills()
        
        return {
            "total_skills": len(skills),
            "total_edges": self.graph.number_of_edges(),
            "avg_success_rate": sum(s.success_rate for s in skills) / len(skills) if skills else 0,
            "tags": list(set(tag for s in skills for tag in s.tags))
        }
    
    def _save(self):
        """Save graph to disk."""
        data = {}
        
        for node_id in self.graph.nodes:
            skill = self.graph.nodes[node_id].get("skill")
            if skill:
                data[node_id] = skill.to_dict()
        
        filepath = self.storage_path / "graph.json"
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
    
    def _load(self):
        """Load graph from disk."""
        filepath = self.storage_path / "graph.json"
        
        if not filepath.exists():
            return
        
        try:
            with open(filepath) as f:
                data = json.load(f)
            
            for node_id, skill_data in data.items():
                skill = SkillNode.from_dict(skill_data)
                self.add_skill(skill)
        except Exception as e:
            print(f"Warning: Failed to load skill graph: {e}")
