"""Team collaboration - shared workspaces and knowledge sharing."""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class CollaborationRole(str, Enum):
    """Roles in collaboration."""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


@dataclass
class TeamMember:
    """A team member."""
    user_id: str
    role: CollaborationRole
    joined_at: datetime
    permissions: List[str]


@dataclass
class SharedWorkspace:
    """A shared workspace for team collaboration."""
    workspace_id: str
    name: str
    description: str
    owner_id: str
    created_at: datetime
    members: List[TeamMember]
    is_public: bool = False


class CollaborationManager:
    """Manages team collaboration features."""
    
    def __init__(self, storage_dir: str = "collaboration"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # 工作空间存储
        self.workspaces: Dict[str, SharedWorkspace] = {}
        self._load_workspaces()
    
    def _load_workspaces(self):
        """Load workspaces from disk."""
        workspaces_file = self.storage_dir / "workspaces.json"
        if workspaces_file.exists():
            try:
                data = json.loads(workspaces_file.read_text())
                for ws_data in data:
                    workspace = self._deserialize_workspace(ws_data)
                    self.workspaces[workspace.workspace_id] = workspace
            except Exception as e:
                logger.error(f"Failed to load workspaces: {e}")
    
    def _save_workspaces(self):
        """Save workspaces to disk."""
        workspaces_file = self.storage_dir / "workspaces.json"
        data = [self._serialize_workspace(ws) for ws in self.workspaces.values()]
        workspaces_file.write_text(json.dumps(data, indent=2))
    
    def _serialize_workspace(self, workspace: SharedWorkspace) -> Dict:
        """Serialize workspace to dict."""
        return {
            "workspace_id": workspace.workspace_id,
            "name": workspace.name,
            "description": workspace.description,
            "owner_id": workspace.owner_id,
            "created_at": workspace.created_at.isoformat(),
            "members": [
                {
                    "user_id": m.user_id,
                    "role": m.role.value,
                    "joined_at": m.joined_at.isoformat(),
                    "permissions": m.permissions
                }
                for m in workspace.members
            ],
            "is_public": workspace.is_public
        }
    
    def _deserialize_workspace(self, data: Dict) -> SharedWorkspace:
        """Deserialize workspace from dict."""
        members = []
        for m_data in data.get("members", []):
            members.append(TeamMember(
                user_id=m_data["user_id"],
                role=CollaborationRole(m_data["role"]),
                joined_at=datetime.fromisoformat(m_data["joined_at"]),
                permissions=m_data.get("permissions", [])
            ))
        
        return SharedWorkspace(
            workspace_id=data["workspace_id"],
            name=data["name"],
            description=data["description"],
            owner_id=data["owner_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            members=members,
            is_public=data.get("is_public", False)
        )
    
    def create_workspace(
        self,
        name: str,
        description: str,
        owner_id: str,
        is_public: bool = False
    ) -> SharedWorkspace:
        """Create a new shared workspace."""
        import uuid
        workspace_id = f"ws_{uuid.uuid4().hex[:8]}"
        
        owner = TeamMember(
            user_id=owner_id,
            role=CollaborationRole.OWNER,
            joined_at=datetime.now(),
            permissions=["read", "write", "admin"]
        )
        
        workspace = SharedWorkspace(
            workspace_id=workspace_id,
            name=name,
            description=description,
            owner_id=owner_id,
            created_at=datetime.now(),
            members=[owner],
            is_public=is_public
        )
        
        self.workspaces[workspace_id] = workspace
        self._save_workspaces()
        
        logger.info(f"Created workspace: {workspace_id}")
        return workspace
    
    def add_member(
        self,
        workspace_id: str,
        user_id: str,
        role: CollaborationRole = CollaborationRole.MEMBER
    ) -> bool:
        """Add a member to workspace."""
        if workspace_id not in self.workspaces:
            return False
        
        workspace = self.workspaces[workspace_id]
        
        # 检查是否已经是成员
        for member in workspace.members:
            if member.user_id == user_id:
                return False
        
        # 根据角色设置权限
        permissions = self._get_permissions_for_role(role)
        
        member = TeamMember(
            user_id=user_id,
            role=role,
            joined_at=datetime.now(),
            permissions=permissions
        )
        
        workspace.members.append(member)
        self._save_workspaces()
        
        logger.info(f"Added member {user_id} to workspace {workspace_id}")
        return True
    
    def remove_member(self, workspace_id: str, user_id: str) -> bool:
        """Remove a member from workspace."""
        if workspace_id not in self.workspaces:
            return False
        
        workspace = self.workspaces[workspace_id]
        
        # 不能移除所有者
        if workspace.owner_id == user_id:
            return False
        
        workspace.members = [m for m in workspace.members if m.user_id != user_id]
        self._save_workspaces()
        
        logger.info(f"Removed member {user_id} from workspace {workspace_id}")
        return True
    
    def _get_permissions_for_role(self, role: CollaborationRole) -> List[str]:
        """Get permissions for a role."""
        permissions_map = {
            CollaborationRole.OWNER: ["read", "write", "admin", "delete"],
            CollaborationRole.ADMIN: ["read", "write", "admin"],
            CollaborationRole.MEMBER: ["read", "write"],
            CollaborationRole.VIEWER: ["read"]
        }
        return permissions_map.get(role, ["read"])
    
    def get_workspace(self, workspace_id: str) -> Optional[SharedWorkspace]:
        """Get workspace by ID."""
        return self.workspaces.get(workspace_id)
    
    def list_workspaces(self, user_id: str) -> List[SharedWorkspace]:
        """List workspaces for a user."""
        result = []
        for workspace in self.workspaces.values():
            # 检查用户是否是成员
            for member in workspace.members:
                if member.user_id == user_id:
                    result.append(workspace)
                    break
            # 或者是公开工作空间
            if workspace.is_public and workspace not in result:
                result.append(workspace)
        return result
    
    def share_memory(
        self,
        workspace_id: str,
        memory_id: str,
        shared_by: str
    ) -> bool:
        """Share a memory with workspace."""
        if workspace_id not in self.workspaces:
            return False
        
        workspace = self.workspaces[workspace_id]
        
        # 检查权限
        has_permission = False
        for member in workspace.members:
            if member.user_id == shared_by and "write" in member.permissions:
                has_permission = True
                break
        
        if not has_permission:
            return False
        
        # 保存共享记录
        shared_file = self.storage_dir / f"{workspace_id}_shared.json"
        shared_memories = []
        if shared_file.exists():
            try:
                shared_memories = json.loads(shared_file.read_text())
            except:
                pass
        
        shared_memories.append({
            "memory_id": memory_id,
            "shared_by": shared_by,
            "shared_at": datetime.now().isoformat()
        })
        
        shared_file.write_text(json.dumps(shared_memories, indent=2))
        
        logger.info(f"Shared memory {memory_id} with workspace {workspace_id}")
        return True
    
    def get_shared_memories(self, workspace_id: str) -> List[Dict[str, Any]]:
        """Get shared memories for workspace."""
        shared_file = self.storage_dir / f"{workspace_id}_shared.json"
        if not shared_file.exists():
            return []
        
        try:
            return json.loads(shared_file.read_text())
        except:
            return []
    
    def check_permission(
        self,
        workspace_id: str,
        user_id: str,
        permission: str
    ) -> bool:
        """Check if user has permission in workspace."""
        if workspace_id not in self.workspaces:
            return False
        
        workspace = self.workspaces[workspace_id]
        
        for member in workspace.members:
            if member.user_id == user_id:
                return permission in member.permissions
        
        return False
