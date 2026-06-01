"""
Unit tests for Skill Graph module.
"""

import pytest
import tempfile
import shutil
from src.skills.node import SkillNode
from src.skills.graph import SkillGraph
from src.skills.matcher import SkillMatcher


class TestSkillNode:
    """Tests for SkillNode."""
    
    def test_create_skill(self):
        skill = SkillNode.create(
            name="Deploy to Vercel",
            description="Deploy Next.js app to Vercel",
            content="1. Run npm build\n2. Run vercel deploy"
        )
        
        assert skill.name == "Deploy to Vercel"
        assert skill.description == "Deploy Next.js app to Vercel"
        assert skill.id.startswith("skill_")
    
    def test_matches_context(self):
        skill = SkillNode.create(
            name="Deploy",
            description="Deploy app",
            content="...",
            prerequisites={"framework": "next.js", "node_version": ">=18"}
        )
        
        context_match = {"framework": "next.js", "node_version": "20"}
        context_no_match = {"framework": "django", "python_version": "3.9"}
        
        assert skill.matches_context(context_match) >= 0.5
        assert skill.matches_context(context_no_match) < 0.5
    
    def test_record_success(self):
        skill = SkillNode.create(
            name="Test",
            description="Test",
            content="..."
        )
        
        initial_count = skill.success_count
        skill.record_success()
        
        assert skill.success_count == initial_count + 1
    
    def test_record_failure(self):
        skill = SkillNode.create(
            name="Test",
            description="Test",
            content="..."
        )
        
        initial_count = skill.failure_count
        skill.record_failure(reason="Network error")
        
        assert skill.failure_count == initial_count + 1
        assert len(skill.feedback) > 0
    
    def test_success_rate(self):
        skill = SkillNode.create(
            name="Test",
            description="Test",
            content="..."
        )
        
        skill.record_success()
        skill.record_success()
        skill.record_failure()
        
        assert skill.success_rate == pytest.approx(2/3, 0.01)
    
    def test_to_dict(self):
        skill = SkillNode.create(
            name="Test",
            description="Test skill",
            content="Test content",
            tags=["test", "example"]
        )
        
        data = skill.to_dict()
        
        assert data["name"] == "Test"
        assert data["description"] == "Test skill"
        assert "test" in data["tags"]


class TestSkillGraph:
    """Tests for SkillGraph."""
    
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.graph = SkillGraph(storage_path=self.temp_dir)
    
    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_add_skill(self):
        skill = SkillNode.create(
            name="Test Skill",
            description="A test skill",
            content="Test content"
        )
        
        self.graph.add_skill(skill)
        
        retrieved = self.graph.get_skill(skill.id)
        assert retrieved is not None
        assert retrieved.name == "Test Skill"
    
    def test_remove_skill(self):
        skill = SkillNode.create(
            name="Test Skill",
            description="A test skill",
            content="Test content"
        )
        
        self.graph.add_skill(skill)
        self.graph.remove_skill(skill.id)
        
        retrieved = self.graph.get_skill(skill.id)
        assert retrieved is None
    
    def test_find_matching_skills(self):
        skill1 = SkillNode.create(
            name="Deploy Vercel",
            description="Deploy to Vercel",
            content="...",
            prerequisites={"framework": "next.js"},
            tags=["deploy", "vercel"]
        )
        
        skill2 = SkillNode.create(
            name="Deploy AWS",
            description="Deploy to AWS",
            content="...",
            prerequisites={"framework": "any"},
            tags=["deploy", "aws"]
        )
        
        self.graph.add_skill(skill1)
        self.graph.add_skill(skill2)
        
        context = {"framework": "next.js"}
        matches = self.graph.find_matching_skills(context, tags=["deploy"])
        
        assert len(matches) >= 1
    
    def test_get_all_skills(self):
        skill1 = SkillNode.create(name="Skill 1", description="...", content="...")
        skill2 = SkillNode.create(name="Skill 2", description="...", content="...")
        
        self.graph.add_skill(skill1)
        self.graph.add_skill(skill2)
        
        all_skills = self.graph.get_all_skills()
        assert len(all_skills) == 2
    
    def test_get_stats(self):
        skill = SkillNode.create(
            name="Test",
            description="...",
            content="...",
            tags=["test"]
        )
        
        self.graph.add_skill(skill)
        
        stats = self.graph.get_stats()
        assert stats["total_skills"] == 1
        assert "test" in stats["tags"]


class TestSkillMatcher:
    """Tests for SkillMatcher."""
    
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.graph = SkillGraph(storage_path=self.temp_dir)
    
    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_find_best_skill(self):
        skill = SkillNode.create(
            name="Deploy to Vercel",
            description="Deploy Next.js app to Vercel",
            content="...",
            prerequisites={"framework": "next.js"},
            tags=["deploy", "vercel"]
        )
        
        self.graph.add_skill(skill)
        
        matcher = SkillMatcher(self.graph)
        result = matcher.find_best_skill(
            task_description="Deploy my Next.js app",
            context={"framework": "next.js"}
        )
        
        assert result is not None
        assert result.skill.name == "Deploy to Vercel"
    
    def test_find_matching_skills(self):
        skill1 = SkillNode.create(name="Skill A", description="...", content="...", tags=["tag1"])
        skill2 = SkillNode.create(name="Skill B", description="...", content="...", tags=["tag2"])
        
        self.graph.add_skill(skill1)
        self.graph.add_skill(skill2)
        
        matcher = SkillMatcher(self.graph)
        results = matcher.find_matching_skills(
            task_description="Test task",
            tags=["tag1"]
        )
        
        assert len(results) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
