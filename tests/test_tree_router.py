"""Test MemoryTree and ModelRouter integration."""
import pytest
import tempfile
import asyncio
from pathlib import Path
from src.memory.tree import MemoryTree
from src.agent.router import ModelRouter, ModelType


def test_memory_tree_creates():
    """MemoryTree 应该能创建。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tree = MemoryTree(tmpdir)
        assert tree is not None


def test_memory_tree_saves_context():
    """MemoryTree 应该能保存上下文。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tree = MemoryTree(tmpdir)
        
        result = asyncio.run(tree.saveContext(
            user_id="user1",
            interaction={
                "query": "用户喜欢Python",
                "reply": "好的，我记住了"
            }
        ))
        
        assert result is True


def test_memory_tree_retrieves_context():
    """MemoryTree 应该能检索上下文。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tree = MemoryTree(tmpdir)
        
        # 保存记忆
        asyncio.run(tree.saveContext(
            user_id="user1",
            interaction={
                "query": "用户喜欢Python",
                "reply": "好的，我记住了"
            }
        ))
        
        # 检索记忆
        results = asyncio.run(tree.retrieveRelevantContext(
            query="Python",
            user_id="user1"
        ))
        
        assert len(results) > 0


def test_memory_tree_classifies_interaction():
    """MemoryTree 应该能分类交互。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tree = MemoryTree(tmpdir)
        
        # 测试分类
        assert tree._classify_interaction({"query": "我喜欢Python"}).value == "user"
        assert tree._classify_interaction({"query": "不要用mock"}).value == "feedback"
        assert tree._classify_interaction({"query": "项目截止日期"}).value == "project"


def test_model_router_creates():
    """ModelRouter 应该能创建。"""
    router = ModelRouter()
    assert router is not None


def test_model_router_routes_fast():
    """ModelRouter 应该路由简单任务到快速模型。"""
    router = ModelRouter()
    
    model_type = router.route("你好")
    assert model_type == ModelType.FAST


def test_model_router_routes_reasoning():
    """ModelRouter 应该路由复杂任务到推理模型。"""
    router = ModelRouter()
    
    model_type = router.route("请分析这段代码的性能问题")
    assert model_type == ModelType.REASONING


def test_model_router_routes_vision():
    """ModelRouter 应该路由图像任务到视觉模型。"""
    router = ModelRouter()
    
    model_type = router.route("请分析这张图片", has_images=True)
    assert model_type == ModelType.VISION


def test_model_router_routes_local():
    """ModelRouter 应该路由私密任务到本地模型。"""
    router = ModelRouter()
    
    model_type = router.route("请帮我处理密码")
    assert model_type == ModelType.LOCAL


def test_model_router_gets_config():
    """ModelRouter 应该能获取模型配置。"""
    router = ModelRouter()
    
    config = router.get_config(ModelType.FAST)
    assert config.model_name == "gpt-4o-mini"


def test_memory_tree_get_stats():
    """MemoryTree 应该返回统计信息。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tree = MemoryTree(tmpdir)
        
        stats = tree.get_stats()
        assert "storage" in stats
        assert "worker" in stats
