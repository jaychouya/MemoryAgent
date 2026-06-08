"""Shared MemoryManager singleton for HTTP + MCP."""

from typing import Optional

from src.memory.manager import MemoryManager
from src.memory.paths import default_storage_dir

_manager: Optional[MemoryManager] = None
_manager_dir: Optional[str] = None


def get_shared_memory_manager(llm_service=None) -> MemoryManager:
    global _manager, _manager_dir
    storage = default_storage_dir()
    if _manager is not None and _manager_dir is None:
        _manager_dir = storage
    if _manager is None or _manager_dir != storage:
        _manager = MemoryManager(storage_dir=storage, llm_service=llm_service)
        _manager_dir = storage
    elif llm_service is not None:
        _manager.llm = llm_service
        _manager.retrieval.llm = llm_service
    return _manager


def reset_shared_memory_manager() -> None:
    global _manager, _manager_dir
    _manager = None
    _manager_dir = None
