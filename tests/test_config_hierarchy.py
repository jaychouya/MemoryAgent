"""Tests for CLAUDE.md hierarchy system."""
import pytest
import tempfile
import shutil
from pathlib import Path
from src.memory.config_hierarchy import ConfigHierarchy, ConfigLevel


@pytest.fixture
def temp_project():
    """Create a temporary project directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


def test_hierarchy_creates(temp_project):
    """ConfigHierarchy 应该能创建。"""
    hierarchy = ConfigHierarchy(project_root=temp_project)
    assert hierarchy is not None


def test_hierarchy_has_levels(temp_project):
    """应该定义六个层级。"""
    hierarchy = ConfigHierarchy(project_root=temp_project)
    
    assert len(hierarchy.LEVELS) == 6
    assert ConfigLevel.MANAGED in hierarchy.LEVELS
    assert ConfigLevel.USER in hierarchy.LEVELS
    assert ConfigLevel.PROJECT in hierarchy.LEVELS
    assert ConfigLevel.LOCAL in hierarchy.LEVELS
    assert ConfigLevel.AUTO in hierarchy.LEVELS
    assert ConfigLevel.TEAM in hierarchy.LEVELS


def test_hierarchy_load_project_config(temp_project):
    """应该加载项目配置。"""
    # 创建项目配置文件
    config_path = Path(temp_project) / "CLAUDE.md"
    config_path.write_text("# 项目规范\n\n使用 Python 3.9+")
    
    hierarchy = ConfigHierarchy(project_root=temp_project)
    content = hierarchy.load_all()
    
    assert "项目规范" in content
    assert "Python 3.9+" in content


def test_hierarchy_load_local_config(temp_project):
    """应该加载本地配置。"""
    # 创建本地配置文件
    config_path = Path(temp_project) / "CLAUDE.local.md"
    config_path.write_text("# 本地配置\n\n调试模式开启")
    
    hierarchy = ConfigHierarchy(project_root=temp_project)
    content = hierarchy.load_all()
    
    assert "本地配置" in content


def test_hierarchy_load_memory_index(temp_project):
    """应该加载记忆索引。"""
    # 创建记忆目录和索引
    memory_dir = Path(temp_project) / "memories"
    memory_dir.mkdir(exist_ok=True)
    
    memory_file = memory_dir / "MEMORY.md"
    memory_file.write_text("# 记忆索引\n\n- 用户喜欢 Python")
    
    hierarchy = ConfigHierarchy(project_root=temp_project)
    content = hierarchy.load_all()
    
    assert "记忆索引" in content
    assert "用户喜欢 Python" in content


def test_hierarchy_processes_include(temp_project):
    """应该处理 @include 指令。"""
    # 创建被包含的文件
    include_file = Path(temp_project) / "rules.md"
    include_file.write_text("# 规则\n\n不要用 mock")
    
    # 创建主配置文件
    config_path = Path(temp_project) / "CLAUDE.md"
    config_path.write_text("# 项目配置\n\n@include rules.md")
    
    hierarchy = ConfigHierarchy(project_root=temp_project)
    content = hierarchy.load_all()
    
    assert "不要用 mock" in content


def test_hierarchy_get_loaded_layers(temp_project):
    """get_loaded_layers 应该返回已加载的层级。"""
    # 创建项目配置
    config_path = Path(temp_project) / "CLAUDE.md"
    config_path.write_text("项目配置")
    
    hierarchy = ConfigHierarchy(project_root=temp_project)
    hierarchy.load_all()
    
    loaded = hierarchy.get_loaded_layers()
    
    assert len(loaded) > 0
    assert any(l.level == ConfigLevel.PROJECT for l in loaded)


def test_hierarchy_get_stats(temp_project):
    """get_stats 应该返回统计信息。"""
    hierarchy = ConfigHierarchy(project_root=temp_project)
    hierarchy.load_all()
    
    stats = hierarchy.get_stats()
    
    assert "total_levels" in stats
    assert "loaded_levels" in stats
    assert stats["total_levels"] == 6


def test_hierarchy_handles_missing_files(temp_project):
    """应该处理不存在的文件。"""
    hierarchy = ConfigHierarchy(project_root=temp_project)
    content = hierarchy.load_all()
    
    # 没有配置文件时应该返回空字符串或基本内容
    assert isinstance(content, str)
