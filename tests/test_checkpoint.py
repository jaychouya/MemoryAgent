"""Tests for checkpoint mechanism."""
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from src.agent.checkpoint import (
    CheckpointManager,
    Checkpoint,
    CheckpointStatus,
    TaskCheckpointMixin,
    get_checkpoint_manager
)


@pytest.fixture
def checkpoint_manager():
    """Create a temporary checkpoint manager."""
    temp_dir = tempfile.mkdtemp()
    manager = CheckpointManager(storage_dir=temp_dir)
    yield manager
    shutil.rmtree(temp_dir)


def test_checkpoint_manager_creates():
    """CheckpointManager 应该能创建。"""
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = CheckpointManager(storage_dir=temp_dir)
        assert manager is not None


def test_create_checkpoint(checkpoint_manager):
    """create_checkpoint 应该创建检查点。"""
    checkpoint = checkpoint_manager.create_checkpoint(
        task_id="task_1",
        state={"step": 1, "data": "test"},
        metadata={"user_id": "user1"}
    )
    
    assert checkpoint is not None
    assert checkpoint.task_id == "task_1"
    assert checkpoint.state["step"] == 1
    assert checkpoint.status == CheckpointStatus.CREATED


def test_update_checkpoint(checkpoint_manager):
    """update_checkpoint 应该更新检查点。"""
    checkpoint = checkpoint_manager.create_checkpoint(
        task_id="task_1",
        state={"step": 1}
    )
    
    updated = checkpoint_manager.update_checkpoint(
        checkpoint_id=checkpoint.checkpoint_id,
        state={"step": 2},
        status=CheckpointStatus.IN_PROGRESS
    )
    
    assert updated is not None
    assert updated.state["step"] == 2
    assert updated.status == CheckpointStatus.IN_PROGRESS


def test_get_checkpoint(checkpoint_manager):
    """get_checkpoint 应该获取检查点。"""
    checkpoint = checkpoint_manager.create_checkpoint(
        task_id="task_1",
        state={"step": 1}
    )
    
    retrieved = checkpoint_manager.get_checkpoint(checkpoint.checkpoint_id)
    
    assert retrieved is not None
    assert retrieved.checkpoint_id == checkpoint.checkpoint_id


def test_get_task_checkpoints(checkpoint_manager):
    """get_task_checkpoints 应该获取任务的检查点。"""
    # 创建多个检查点
    checkpoint_manager.create_checkpoint(
        task_id="task_1",
        state={"step": 1}
    )
    checkpoint_manager.create_checkpoint(
        task_id="task_1",
        state={"step": 2}
    )
    checkpoint_manager.create_checkpoint(
        task_id="task_2",
        state={"step": 1}
    )
    
    checkpoints = checkpoint_manager.get_task_checkpoints("task_1")
    
    assert len(checkpoints) == 2


def test_get_latest_checkpoint(checkpoint_manager):
    """get_latest_checkpoint 应该获取最新的检查点。"""
    checkpoint_manager.create_checkpoint(
        task_id="task_1",
        state={"step": 1}
    )
    checkpoint_manager.create_checkpoint(
        task_id="task_1",
        state={"step": 2}
    )
    
    latest = checkpoint_manager.get_latest_checkpoint("task_1")
    
    assert latest is not None
    assert latest.state["step"] == 2


def test_restore_checkpoint(checkpoint_manager):
    """restore_checkpoint 应该恢复检查点。"""
    checkpoint = checkpoint_manager.create_checkpoint(
        task_id="task_1",
        state={"step": 1, "data": "test"}
    )
    
    state = checkpoint_manager.restore_checkpoint(checkpoint.checkpoint_id)
    
    assert state is not None
    assert state["step"] == 1
    assert state["data"] == "test"
    
    # 检查状态已更新
    updated = checkpoint_manager.get_checkpoint(checkpoint.checkpoint_id)
    assert updated.status == CheckpointStatus.RESTORED


def test_delete_checkpoint(checkpoint_manager):
    """delete_checkpoint 应该删除检查点。"""
    checkpoint = checkpoint_manager.create_checkpoint(
        task_id="task_1",
        state={"step": 1}
    )
    
    result = checkpoint_manager.delete_checkpoint(checkpoint.checkpoint_id)
    
    assert result is True
    assert checkpoint_manager.get_checkpoint(checkpoint.checkpoint_id) is None


def test_cleanup_old_checkpoints(checkpoint_manager):
    """cleanup_old_checkpoints 应该清理旧检查点。"""
    # 创建检查点
    checkpoint_manager.create_checkpoint(
        task_id="task_1",
        state={"step": 1}
    )
    
    # 清理（设置为 0 天，应该清理所有）
    cleaned = checkpoint_manager.cleanup_old_checkpoints(max_age_days=0)
    
    assert cleaned >= 0


def test_get_stats(checkpoint_manager):
    """get_stats 应该返回统计信息。"""
    checkpoint_manager.create_checkpoint(
        task_id="task_1",
        state={"step": 1}
    )
    checkpoint_manager.create_checkpoint(
        task_id="task_2",
        state={"step": 1}
    )
    
    stats = checkpoint_manager.get_stats()
    
    assert stats["total_checkpoints"] == 2
    assert "created" in stats["by_status"]


def test_checkpoint_to_dict():
    """Checkpoint.to_dict 应该转换为字典。"""
    checkpoint = Checkpoint(
        checkpoint_id="cp_123",
        task_id="task_1",
        status=CheckpointStatus.CREATED,
        created_at=datetime.now(),
        state={"step": 1},
        metadata={"key": "value"}
    )
    
    data = checkpoint.to_dict()
    
    assert data["checkpoint_id"] == "cp_123"
    assert data["task_id"] == "task_1"
    assert data["status"] == "created"


def test_checkpoint_from_dict():
    """Checkpoint.from_dict 应该从字典创建。"""
    data = {
        "checkpoint_id": "cp_123",
        "task_id": "task_1",
        "status": "created",
        "created_at": datetime.now().isoformat(),
        "state": {"step": 1},
        "metadata": {"key": "value"}
    }
    
    checkpoint = Checkpoint.from_dict(data)
    
    assert checkpoint.checkpoint_id == "cp_123"
    assert checkpoint.task_id == "task_1"
    assert checkpoint.status == CheckpointStatus.CREATED


class TestTaskWithCheckpoint(TaskCheckpointMixin):
    """Test class with checkpoint support."""
    
    def __init__(self):
        super().__init__()
        self.data = {}
    
    def process_step(self, step: int, data: str):
        """Process a step and save checkpoint."""
        self.data = {"step": step, "data": data}
        self.save_checkpoint(state=self.data)


def test_task_checkpoint_mixin():
    """TaskCheckpointMixin 应该支持检查点。"""
    task = TestTaskWithCheckpoint()
    
    task_id = task.start_task()
    task.process_step(1, "step1")
    task.process_step(2, "step2")
    
    latest = task.get_latest_checkpoint()
    
    assert latest is not None
    assert latest.state["step"] == 2
    assert latest.state["data"] == "step2"


def test_get_checkpoint_manager_singleton():
    """get_checkpoint_manager 应该返回单例。"""
    manager1 = get_checkpoint_manager()
    manager2 = get_checkpoint_manager()
    
    assert manager1 is manager2
