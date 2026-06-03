"""Tests for external integration framework."""
import pytest
import tempfile
import shutil
from pathlib import Path
from src.agent.integrations import (
    IntegrationManager,
    IntegrationConfig,
    IntegrationType,
    AuthType,
    IntegrationCredentials,
    EmailIntegration,
    CalendarIntegration,
    DocumentIntegration,
    CodeIntegration,
    get_integration_manager
)


@pytest.fixture
def integration_manager():
    """Create a temporary integration manager."""
    temp_dir = tempfile.mkdtemp()
    manager = IntegrationManager(config_dir=temp_dir)
    yield manager
    shutil.rmtree(temp_dir)


def test_integration_manager_creates():
    """IntegrationManager 应该能创建。"""
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = IntegrationManager(config_dir=temp_dir)
        assert manager is not None


def test_get_available_integrations(integration_manager):
    """get_available_integrations 应该返回可用集成列表。"""
    integrations = integration_manager.get_available_integrations()
    
    assert len(integrations) > 0
    
    # 检查是否有 Gmail
    gmail = next(
        (i for i in integrations if i["id"] == "gmail"),
        None
    )
    assert gmail is not None
    assert gmail["name"] == "Gmail"
    assert gmail["connected"] is False


def test_get_integration(integration_manager):
    """get_integration 应该返回集成配置。"""
    config = integration_manager.get_integration("gmail")
    
    assert config is not None
    assert config.name == "Gmail"
    assert config.integration_type == IntegrationType.EMAIL


def test_connect_integration(integration_manager):
    """connect_integration 应该能连接集成。"""
    result = integration_manager.connect_integration(
        integration_id="gmail",
        credentials={"access_token": "test-token"}
    )
    
    assert result is True
    
    # 检查是否已连接
    integrations = integration_manager.get_available_integrations()
    gmail = next(
        (i for i in integrations if i["id"] == "gmail"),
        None
    )
    assert gmail["connected"] is True


def test_disconnect_integration(integration_manager):
    """disconnect_integration 应该能断开集成。"""
    integration_manager.connect_integration(
        integration_id="gmail",
        credentials={"access_token": "test-token"}
    )
    
    result = integration_manager.disconnect_integration("gmail")
    
    assert result is True
    
    # 检查是否已断开
    integrations = integration_manager.get_available_integrations()
    gmail = next(
        (i for i in integrations if i["id"] == "gmail"),
        None
    )
    assert gmail["connected"] is False


def test_connect_unknown_integration(integration_manager):
    """connect_integration 应该拒绝未知集成。"""
    result = integration_manager.connect_integration(
        integration_id="unknown",
        credentials={"key": "value"}
    )
    
    assert result is False


def test_get_provider(integration_manager):
    """get_provider 应该返回集成提供者。"""
    integration_manager.connect_integration(
        integration_id="gmail",
        credentials={"access_token": "test-token"}
    )
    
    provider = integration_manager.get_provider("gmail")
    
    assert provider is not None
    assert isinstance(provider, EmailIntegration)


def test_get_provider_not_connected(integration_manager):
    """get_provider 应该在未连接时返回 None。"""
    provider = integration_manager.get_provider("gmail")
    
    assert provider is None


@pytest.mark.asyncio
async def test_sync_integration(integration_manager):
    """sync_integration 应该能同步集成。"""
    integration_manager.connect_integration(
        integration_id="gmail",
        credentials={"access_token": "test-token"}
    )
    
    result = await integration_manager.sync_integration("gmail")
    
    assert result.integration_id == "gmail"
    assert result.success is True


@pytest.mark.asyncio
async def test_sync_integration_not_connected(integration_manager):
    """sync_integration 应该在未连接时失败。"""
    result = await integration_manager.sync_integration("gmail")
    
    assert result.integration_id == "gmail"
    assert result.success is False
    assert "not connected" in result.errors[0]


def test_get_sync_status(integration_manager):
    """get_sync_status 应该返回同步状态。"""
    integration_manager.connect_integration(
        integration_id="gmail",
        credentials={"access_token": "test-token"}
    )
    
    status = integration_manager.get_sync_status()
    
    assert "gmail" in status["connected"]
    assert "github" in status["available"]


def test_preset_integrations(integration_manager):
    """应该有预设集成。"""
    integrations = integration_manager.get_available_integrations()
    ids = [i["id"] for i in integrations]
    
    assert "gmail" in ids
    assert "google_calendar" in ids
    assert "notion" in ids
    assert "github" in ids
    assert "slack" in ids


def test_email_integration():
    """EmailIntegration 应该能创建。"""
    config = IntegrationConfig(
        integration_id="gmail",
        name="Gmail",
        integration_type=IntegrationType.EMAIL,
        auth_type=AuthType.OAUTH2,
        base_url="https://gmail.googleapis.com/gmail/v1"
    )
    
    provider = EmailIntegration(config)
    assert provider is not None


@pytest.mark.asyncio
async def test_email_integration_test_connection():
    """EmailIntegration.test_connection 应该检查凭证。"""
    config = IntegrationConfig(
        integration_id="gmail",
        name="Gmail",
        integration_type=IntegrationType.EMAIL,
        auth_type=AuthType.OAUTH2,
        base_url="https://gmail.googleapis.com/gmail/v1"
    )
    
    provider = EmailIntegration(config)
    
    # 没有凭证时应该返回 False
    result = await provider.test_connection()
    assert result is False
    
    # 有凭证时应该返回 True
    provider.set_credentials(IntegrationCredentials(
        integration_id="gmail",
        credentials={"access_token": "test"}
    ))
    result = await provider.test_connection()
    assert result is True


def test_get_integration_manager_singleton():
    """get_integration_manager 应该返回单例。"""
    manager1 = get_integration_manager()
    manager2 = get_integration_manager()
    
    assert manager1 is manager2
