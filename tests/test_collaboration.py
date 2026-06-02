"""Tests for team collaboration."""
import pytest
import tempfile
import shutil
from pathlib import Path
from src.agent.collaboration import (
    CollaborationManager,
    CollaborationRole,
    TeamMember,
    SharedWorkspace
)


@pytest.fixture
def collaboration_manager():
    """Create a temporary collaboration manager."""
    temp_dir = tempfile.mkdtemp()
    manager = CollaborationManager(storage_dir=temp_dir)
    yield manager
    shutil.rmtree(temp_dir)


def test_collaboration_manager_creates():
    """CollaborationManager 应该能创建。"""
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = CollaborationManager(storage_dir=temp_dir)
        assert manager is not None


def test_create_workspace(collaboration_manager):
    """create_workspace 应该能创建工作空间。"""
    workspace = collaboration_manager.create_workspace(
        name="Test Workspace",
        description="A test workspace",
        owner_id="user1"
    )
    
    assert workspace is not None
    assert workspace.name == "Test Workspace"
    assert workspace.owner_id == "user1"
    assert len(workspace.members) == 1
    assert workspace.members[0].role == CollaborationRole.OWNER


def test_add_member(collaboration_manager):
    """add_member 应该能添加成员。"""
    workspace = collaboration_manager.create_workspace(
        name="Test Workspace",
        description="A test workspace",
        owner_id="user1"
    )
    
    result = collaboration_manager.add_member(
        workspace_id=workspace.workspace_id,
        user_id="user2",
        role=CollaborationRole.MEMBER
    )
    
    assert result is True
    
    # 验证成员已添加
    updated_workspace = collaboration_manager.get_workspace(workspace.workspace_id)
    assert len(updated_workspace.members) == 2


def test_remove_member(collaboration_manager):
    """remove_member 应该能移除成员。"""
    workspace = collaboration_manager.create_workspace(
        name="Test Workspace",
        description="A test workspace",
        owner_id="user1"
    )
    
    collaboration_manager.add_member(
        workspace_id=workspace.workspace_id,
        user_id="user2",
        role=CollaborationRole.MEMBER
    )
    
    result = collaboration_manager.remove_member(
        workspace_id=workspace.workspace_id,
        user_id="user2"
    )
    
    assert result is True
    
    # 验证成员已移除
    updated_workspace = collaboration_manager.get_workspace(workspace.workspace_id)
    assert len(updated_workspace.members) == 1


def test_cannot_remove_owner(collaboration_manager):
    """不能移除所有者。"""
    workspace = collaboration_manager.create_workspace(
        name="Test Workspace",
        description="A test workspace",
        owner_id="user1"
    )
    
    result = collaboration_manager.remove_member(
        workspace_id=workspace.workspace_id,
        user_id="user1"
    )
    
    assert result is False


def test_list_workspaces(collaboration_manager):
    """list_workspaces 应该列出用户的工作空间。"""
    collaboration_manager.create_workspace(
        name="Workspace 1",
        description="First workspace",
        owner_id="user1"
    )
    
    collaboration_manager.create_workspace(
        name="Workspace 2",
        description="Second workspace",
        owner_id="user2"
    )
    
    workspaces = collaboration_manager.list_workspaces("user1")
    
    assert len(workspaces) == 1
    assert workspaces[0].name == "Workspace 1"


def test_share_memory(collaboration_manager):
    """share_memory 应该能共享记忆。"""
    workspace = collaboration_manager.create_workspace(
        name="Test Workspace",
        description="A test workspace",
        owner_id="user1"
    )
    
    result = collaboration_manager.share_memory(
        workspace_id=workspace.workspace_id,
        memory_id="memory_123",
        shared_by="user1"
    )
    
    assert result is True
    
    # 验证共享记录
    shared = collaboration_manager.get_shared_memories(workspace.workspace_id)
    assert len(shared) == 1
    assert shared[0]["memory_id"] == "memory_123"


def test_check_permission(collaboration_manager):
    """check_permission 应该能检查权限。"""
    workspace = collaboration_manager.create_workspace(
        name="Test Workspace",
        description="A test workspace",
        owner_id="user1"
    )
    
    assert collaboration_manager.check_permission(
        workspace.workspace_id, "user1", "admin"
    ) is True
    
    assert collaboration_manager.check_permission(
        workspace.workspace_id, "user1", "read"
    ) is True
