"""
Skill node definition for knowledge graph.

Each skill node represents a reusable capability with:
- Prerequisites (what's needed to use this skill)
- Dependencies (other skills this skill depends on)
- Success/failure tracking
- Context matching
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
import hashlib


@dataclass
class SkillNode:
    """
    Represents a skill in the knowledge graph.
    
    Attributes:
        id: Unique identifier
        name: Human-readable name
        description: What this skill does
        content: Full skill content (instructions, code, etc.)
        prerequisites: Requirements to use this skill
        dependencies: Other skill IDs this skill depends on
        success_count: Number of successful uses
        failure_count: Number of failed uses
        feedback: User feedback entries
        tags: Categorization tags
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    id: str
    name: str
    description: str
    content: str
    
    # Prerequisites (e.g., {"framework": "next.js", "node_version": ">=18"})
    prerequisites: Dict[str, Any] = field(default_factory=dict)
    
    # Dependencies (list of skill IDs)
    dependencies: List[str] = field(default_factory=list)
    
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
            return 0.5  # Default for unrated skills
        return self.success_count / total
    
    @property
    def usage_count(self) -> int:
        """Get total usage count."""
        return self.success_count + self.failure_count
    
    @classmethod
    def create(
        cls,
        name: str,
        description: str,
        content: str,
        prerequisites: Dict[str, Any] = None,
        dependencies: List[str] = None,
        tags: List[str] = None
    ) -> "SkillNode":
        """Create a new skill node with auto-generated ID."""
        skill_id = hashlib.md5(name.encode()).hexdigest()[:8]
        
        return cls(
            id=f"skill_{skill_id}",
            name=name,
            description=description,
            content=content,
            prerequisites=prerequisites or {},
            dependencies=dependencies or [],
            tags=tags or []
        )
    
    def matches_context(self, context: Dict[str, Any]) -> float:
        """
        Calculate how well this skill matches the given context.
        
        Args:
            context: Current project/environment context
            
        Returns:
            Match score (0.0 to 1.0)
        """
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
        
        if isinstance(required, list):
            # List contains check
            return actual in required
        
        return required == actual
    
    def record_success(self):
        """Record a successful use."""
        self.success_count += 1
        self.updated_at = datetime.now()
    
    def record_failure(self, reason: str = None):
        """Record a failed use."""
        self.failure_count += 1
        self.updated_at = datetime.now()
        
        if reason:
            self.feedback.append({
                "type": "failure",
                "reason": reason,
                "timestamp": datetime.now().isoformat()
            })
    
    def add_feedback(self, feedback_type: str, content: str):
        """Add user feedback."""
        self.feedback.append({
            "type": feedback_type,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "content": self.content,
            "prerequisites": self.prerequisites,
            "dependencies": self.dependencies,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": self.success_rate,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SkillNode":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            content=data["content"],
            prerequisites=data.get("prerequisites", {}),
            dependencies=data.get("dependencies", []),
            success_count=data.get("success_count", 0),
            failure_count=data.get("failure_count", 0),
            tags=data.get("tags", []),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat()))
        )
