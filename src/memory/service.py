"""Shared MemoryManager singleton for HTTP + MCP."""

from typing import Optional

from src.memory.manager import MemoryManager

_manager: Optional[MemoryManager] = None


def get_shared_memory_manager(llm_service=None) -> MemoryManager:
    global _manager
    if _manager is None:
        _manager = MemoryManager(llm_service=llm_service)
    elif llm_service is not None:
        _manager.llm = llm_service
        _manager.retrieval.llm = llm_service
    return _manager


def reset_shared_memory_manager() -> None:
    global _manager
    _manager = None
