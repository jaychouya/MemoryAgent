"""Checkpoint mechanism for long-running tasks."""

import logging
import json
import uuid
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class CheckpointStatus(str, Enum):
    """Checkpoint status."""
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RESTORED = "restored"


@dataclass
class Checkpoint:
    """A checkpoint for saving task state."""
    checkpoint_id: str
    task_id: str
    status: CheckpointStatus
    created_at: datetime
    state: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    parent_checkpoint_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "checkpoint_id": self.checkpoint_id,
            "task_id": self.task_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "state": self.state,
            "metadata": self.metadata,
            "parent_checkpoint_id": self.parent_checkpoint_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Checkpoint":
        """Create from dictionary."""
        return cls(
            checkpoint_id=data["checkpoint_id"],
            task_id=data["task_id"],
            status=CheckpointStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            state=data.get("state", {}),
            metadata=data.get("metadata", {}),
            parent_checkpoint_id=data.get("parent_checkpoint_id")
        )


class CheckpointManager:
    """Manages checkpoints for long-running tasks."""
    
    def __init__(self, storage_dir: str = ".memoryai/checkpoints"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoints: Dict[str, Checkpoint] = {}
        self._load_checkpoints()
    
    def _load_checkpoints(self):
        """Load checkpoints from disk."""
        for checkpoint_file in self.storage_dir.glob("*.json"):
            try:
                data = json.loads(checkpoint_file.read_text())
                checkpoint = Checkpoint.from_dict(data)
                self.checkpoints[checkpoint.checkpoint_id] = checkpoint
            except Exception as e:
                logger.error(f"Failed to load checkpoint {checkpoint_file}: {e}")
    
    def _save_checkpoint(self, checkpoint: Checkpoint):
        """Save checkpoint to disk."""
        checkpoint_file = self.storage_dir / f"{checkpoint.checkpoint_id}.json"
        checkpoint_file.write_text(json.dumps(checkpoint.to_dict(), indent=2))
    
    def create_checkpoint(
        self,
        task_id: str,
        state: Dict[str, Any],
        metadata: Dict[str, Any] = None,
        parent_checkpoint_id: str = None
    ) -> Checkpoint:
        """Create a new checkpoint."""
        checkpoint_id = f"cp_{uuid.uuid4().hex[:12]}"
        
        checkpoint = Checkpoint(
            checkpoint_id=checkpoint_id,
            task_id=task_id,
            status=CheckpointStatus.CREATED,
            created_at=datetime.now(),
            state=state,
            metadata=metadata or {},
            parent_checkpoint_id=parent_checkpoint_id
        )
        
        self.checkpoints[checkpoint_id] = checkpoint
        self._save_checkpoint(checkpoint)
        
        logger.info(f"Created checkpoint: {checkpoint_id} for task {task_id}")
        return checkpoint
    
    def update_checkpoint(
        self,
        checkpoint_id: str,
        state: Dict[str, Any] = None,
        status: CheckpointStatus = None,
        metadata: Dict[str, Any] = None
    ) -> Optional[Checkpoint]:
        """Update an existing checkpoint."""
        if checkpoint_id not in self.checkpoints:
            logger.error(f"Checkpoint not found: {checkpoint_id}")
            return None
        
        checkpoint = self.checkpoints[checkpoint_id]
        
        if state is not None:
            checkpoint.state = state
        if status is not None:
            checkpoint.status = status
        if metadata is not None:
            checkpoint.metadata.update(metadata)
        
        self._save_checkpoint(checkpoint)
        
        logger.info(f"Updated checkpoint: {checkpoint_id}")
        return checkpoint
    
    def get_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """Get a checkpoint by ID."""
        return self.checkpoints.get(checkpoint_id)
    
    def get_task_checkpoints(
        self,
        task_id: str,
        limit: int = 10
    ) -> List[Checkpoint]:
        """Get checkpoints for a task."""
        task_checkpoints = [
            cp for cp in self.checkpoints.values()
            if cp.task_id == task_id
        ]
        
        # 按创建时间排序
        task_checkpoints.sort(
            key=lambda cp: cp.created_at,
            reverse=True
        )
        
        return task_checkpoints[:limit]
    
    def get_latest_checkpoint(
        self,
        task_id: str
    ) -> Optional[Checkpoint]:
        """Get the latest checkpoint for a task."""
        checkpoints = self.get_task_checkpoints(task_id, limit=1)
        return checkpoints[0] if checkpoints else None
    
    def restore_checkpoint(
        self,
        checkpoint_id: str
    ) -> Optional[Dict[str, Any]]:
        """Restore state from a checkpoint."""
        if checkpoint_id not in self.checkpoints:
            logger.error(f"Checkpoint not found: {checkpoint_id}")
            return None
        
        checkpoint = self.checkpoints[checkpoint_id]
        checkpoint.status = CheckpointStatus.RESTORED
        self._save_checkpoint(checkpoint)
        
        logger.info(f"Restored checkpoint: {checkpoint_id}")
        return checkpoint.state
    
    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """Delete a checkpoint."""
        if checkpoint_id not in self.checkpoints:
            return False
        
        del self.checkpoints[checkpoint_id]
        
        checkpoint_file = self.storage_dir / f"{checkpoint_id}.json"
        if checkpoint_file.exists():
            checkpoint_file.unlink()
        
        logger.info(f"Deleted checkpoint: {checkpoint_id}")
        return True
    
    def cleanup_old_checkpoints(
        self,
        max_age_days: int = 30
    ) -> int:
        """Cleanup old checkpoints."""
        cutoff_date = datetime.now().timestamp() - (max_age_days * 86400)
        
        to_delete = []
        for checkpoint in self.checkpoints.values():
            if checkpoint.created_at.timestamp() < cutoff_date:
                to_delete.append(checkpoint.checkpoint_id)
        
        for checkpoint_id in to_delete:
            self.delete_checkpoint(checkpoint_id)
        
        logger.info(f"Cleaned up {len(to_delete)} old checkpoints")
        return len(to_delete)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get checkpoint statistics."""
        total = len(self.checkpoints)
        by_status = {}
        
        for checkpoint in self.checkpoints.values():
            status = checkpoint.status.value
            by_status[status] = by_status.get(status, 0) + 1
        
        return {
            "total_checkpoints": total,
            "by_status": by_status
        }


class TaskCheckpointMixin:
    """Mixin for adding checkpoint support to tasks."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._checkpoint_manager = CheckpointManager()
        self._current_task_id: Optional[str] = None
    
    def start_task(self, task_id: str = None) -> str:
        """Start a new task with checkpoint support."""
        self._current_task_id = task_id or f"task_{uuid.uuid4().hex[:8]}"
        return self._current_task_id
    
    def save_checkpoint(
        self,
        state: Dict[str, Any],
        metadata: Dict[str, Any] = None
    ) -> Optional[Checkpoint]:
        """Save current state as checkpoint."""
        if not self._current_task_id:
            logger.error("No active task")
            return None
        
        return self._checkpoint_manager.create_checkpoint(
            task_id=self._current_task_id,
            state=state,
            metadata=metadata
        )
    
    def restore_from_checkpoint(
        self,
        checkpoint_id: str
    ) -> Optional[Dict[str, Any]]:
        """Restore state from checkpoint."""
        return self._checkpoint_manager.restore_checkpoint(checkpoint_id)
    
    def get_latest_checkpoint(self) -> Optional[Checkpoint]:
        """Get latest checkpoint for current task."""
        if not self._current_task_id:
            return None
        
        return self._checkpoint_manager.get_latest_checkpoint(
            self._current_task_id
        )


# 全局检查点管理器实例
_checkpoint_manager: Optional[CheckpointManager] = None


def get_checkpoint_manager() -> CheckpointManager:
    """Get or create global checkpoint manager."""
    global _checkpoint_manager
    if _checkpoint_manager is None:
        _checkpoint_manager = CheckpointManager()
    return _checkpoint_manager
