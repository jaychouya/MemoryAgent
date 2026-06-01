"""Test Subconscious Loop - background memory processing."""
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from src.memory.worker import BackgroundWorker


def test_worker_creates():
    """后台工作器应该能创建。"""
    worker = BackgroundWorker()
    assert worker is not None
    assert worker.interval == 300  # 默认5分钟


def test_worker_registers_tasks():
    """后台工作器应该能注册任务。"""
    worker = BackgroundWorker()
    
    task = MagicMock()
    task.__name__ = "test_task"
    
    worker.register_task(task, interval=60)
    
    assert len(worker.tasks) == 1


def test_worker_runs_task():
    """后台工作器应该能运行任务。"""
    worker = BackgroundWorker()
    
    task = MagicMock()
    task.__name__ = "test_task"
    
    worker.register_task(task, interval=60)
    
    # 运行一次
    worker.run_once()
    
    task.assert_called_once()


def test_worker_handles_task_error():
    """后台工作器应该处理任务错误。"""
    worker = BackgroundWorker()
    
    task = MagicMock(side_effect=Exception("test error"))
    task.__name__ = "failing_task"
    
    worker.register_task(task, interval=60)
    
    # 运行一次，不应该抛出异常
    worker.run_once()
    
    task.assert_called_once()


def test_worker_stops():
    """后台工作器应该能停止。"""
    worker = BackgroundWorker()
    
    assert worker.running is False
    
    worker.start()
    assert worker.running is True
    
    worker.stop()
    assert worker.running is False


def test_worker_get_stats():
    """后台工作器应该返回统计信息。"""
    worker = BackgroundWorker()
    
    task = MagicMock()
    task.__name__ = "test_task"
    
    worker.register_task(task, interval=60)
    
    stats = worker.get_stats()
    
    assert "tasks" in stats
    assert stats["tasks"] == 1
