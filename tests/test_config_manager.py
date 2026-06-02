"""Tests for simplified configuration manager."""
import pytest
import tempfile
import shutil
from pathlib import Path
from src.backend.config_manager import ConfigManager


@pytest.fixture
def config_manager():
    """Create a temporary config manager."""
    temp_dir = tempfile.mkdtemp()
    manager = ConfigManager(config_dir=temp_dir)
    yield manager
    shutil.rmtree(temp_dir)


def test_config_manager_creates():
    """ConfigManager 应该能创建。"""
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = ConfigManager(config_dir=temp_dir)
        assert manager is not None


def test_get_presets(config_manager):
    """get_presets 应该返回预设配置。"""
    presets = config_manager.get_presets()
    
    assert "presets" in presets
    assert len(presets["presets"]) > 0
    
    # 检查是否有 OpenAI
    openai_preset = next(
        (p for p in presets["presets"] if p["id"] == "openai"),
        None
    )
    assert openai_preset is not None
    assert openai_preset["name"] == "OpenAI"


def test_save_config(config_manager):
    """save_config 应该能保存配置。"""
    config = {
        "api_key": "test-key",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini"
    }
    
    result = config_manager.save_config(config)
    
    assert result["success"] is True


def test_save_config_empty_api_key(config_manager):
    """save_config 应该拒绝空 API Key。"""
    config = {
        "api_key": "",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini"
    }
    
    result = config_manager.save_config(config)
    
    assert result["success"] is False
    assert "API Key" in result["error"]


def test_load_config(config_manager):
    """load_config 应该能加载配置。"""
    config = {
        "api_key": "test-key",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini"
    }
    
    config_manager.save_config(config)
    loaded = config_manager.load_config()
    
    assert loaded is not None
    assert loaded["api_key"] == "test-key"


def test_load_config_not_exists(config_manager):
    """load_config 应该在配置不存在时返回 None。"""
    loaded = config_manager.load_config()
    
    assert loaded is None


def test_quick_setup(config_manager):
    """quick_setup 应该能快速设置。"""
    result = config_manager.quick_setup(
        provider="openai",
        api_key="test-key"
    )
    
    assert result["success"] is True
    
    # 验证配置已保存
    config = config_manager.load_config()
    assert config is not None
    assert config["provider"] == "openai"
    assert config["model"] == "gpt-4o-mini"


def test_quick_setup_custom_model(config_manager):
    """quick_setup 应该支持自定义模型。"""
    result = config_manager.quick_setup(
        provider="openai",
        api_key="test-key",
        model="gpt-4o"
    )
    
    assert result["success"] is True
    
    config = config_manager.load_config()
    assert config["model"] == "gpt-4o"


def test_quick_setup_unknown_provider(config_manager):
    """quick_setup 应该拒绝未知提供商。"""
    result = config_manager.quick_setup(
        provider="unknown",
        api_key="test-key"
    )
    
    assert result["success"] is False
    assert "未知" in result["error"]


def test_get_setup_guide(config_manager):
    """get_setup_guide 应该返回设置指南。"""
    guide = config_manager.get_setup_guide("openai")
    
    assert "title" in guide
    assert "steps" in guide
    assert len(guide["steps"]) > 0


def test_get_setup_guide_unknown(config_manager):
    """get_setup_guide 应该处理未知提供商。"""
    guide = config_manager.get_setup_guide("unknown")
    
    assert guide["title"] == "未知提供商"
