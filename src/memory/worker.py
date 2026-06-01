"""Background worker for Subconscious Loop."""

import logging
import threading
import time
from typing import Callable, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ScheduledTask:
    """A scheduled background task."""
    
    func: Callable
    interval: int  # seconds
    last_run: datetime = None
    run_count: int = 0
    error_count: int = 0
    
    @property
    def name(self) -> str:
        return getattr(self.func, '__name__', str(self.func))


class BackgroundWorker:
    """Background worker for Subconscious Loop."""
    
    def __init__(self, interval: int = 300):
        self.interval = interval
        self.tasks: List[ScheduledTask] = []
        self.running = False
        self.thread: threading.Thread = None
    
    def register_task(self, func: Callable, interval: int = None):
        """Register a background task."""
        task = ScheduledTask(
            func=func,
            interval=interval or self.interval
        )
        self.tasks.append(task)
        logger.info(f"Registered background task: {task.name}")
    
    def run_once(self):
        """Run all registered tasks once."""
        for task in self.tasks:
            try:
                task.func()
                task.run_count += 1
                task.last_run = datetime.now()
                logger.debug(f"Ran task: {task.name}")
            except Exception as e:
                task.error_count += 1
                logger.error(f"Task {task.name} failed: {e}")
    
    def _run_loop(self):
        """Main background loop."""
        logger.info("Background worker started")
        
        while self.running:
            self.run_once()
            time.sleep(self.interval)
        
        logger.info("Background worker stopped")
    
    def start(self):
        """Start the background worker."""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info("Background worker thread started")
    
    def stop(self):
        """Stop the background worker."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
            self.thread = None
        logger.info("Background worker stopped")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get worker statistics."""
        return {
            "running": self.running,
            "tasks": len(self.tasks),
            "task_details": [
                {
                    "name": t.name,
                    "interval": t.interval,
                    "run_count": t.run_count,
                    "error_count": t.error_count,
                    "last_run": t.last_run.isoformat() if t.last_run else None
                }
                for t in self.tasks
            ]
        }
