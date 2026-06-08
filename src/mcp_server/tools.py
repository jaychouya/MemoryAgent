"""Shared memory sidecar logic for MCP and HTTP."""

import json
from typing import Any, Dict, List, Optional

from src.memory.manager import MemoryManager
from src.memory.sidecar import build_export_payload, SIDECAR_V2
from src.memory.types import MemoryType
from src.backend.audit import log_memory_event
from src.memory.store_schema import validate_store_payload

_TYPE_MAP = {
    "user": MemoryType.USER,
    "feedback": MemoryType.FEEDBACK,
    "project": MemoryType.PROJECT,
    "reference": MemoryType.REFERENCE,
}


_managers: Dict[str, MemoryManager] = {}


def get_manager(storage_dir: str = "memories") -> MemoryManager:
    if storage_dir not in _managers:
        _managers[storage_dir] = MemoryManager(storage_dir=storage_dir)
    return _managers[storage_dir]


async def recall_memories(
    user_id: str,
    query: str,
    limit: int = 5,
    storage_dir: str = "memories",
    project_id: Optional[str] = None,
    scope: str = "user",
) -> Dict[str, Any]:
    manager = get_manager(storage_dir)
    items = await manager.retrieve(
        query=query, user_id=user_id, project_id=project_id, top_k=limit
    )
    payload = build_export_payload(
        user_id=user_id,
        memories=items,
        query=query,
        project_id=project_id,
        scope=scope,
    )
    log_memory_event("recall", user_id, detail={"query": query, "count": payload["count"]})
    return payload


async def store_memory(
    user_id: str,
    content: str,
    memory_type: str = "user",
    description: Optional[str] = None,
    storage_dir: str = "memories",
    project_id: Optional[str] = None,
    supersedes: Optional[str] = None,
    source_session_id: Optional[str] = None,
    source_turn: Optional[int] = None,
    source_quote: Optional[str] = None,
) -> Dict[str, Any]:
    validated, err = validate_store_payload(
        user_id=user_id,
        content=content,
        memory_type=memory_type,
        description=description,
        project_id=project_id,
        supersedes=supersedes,
        source_session_id=source_session_id,
        source_turn=source_turn,
        source_quote=source_quote,
    )
    if validated is None:
        return {"stored": False, "reason": f"validation_error: {err}"}

    manager = get_manager(storage_dir)
    mtype = _TYPE_MAP.get(validated.memory_type, MemoryType.USER)
    meta = {}
    for key in (
        "project_id",
        "supersedes",
        "source_session_id",
        "source_turn",
        "source_quote",
    ):
        value = getattr(validated, key)
        if value is not None:
            meta[key] = value
    item = await manager.store(
        content=validated.content,
        memory_type=mtype,
        description=validated.description,
        user_id=validated.user_id,
        metadata=meta,
    )
    if item is None:
        return {"stored": False, "reason": "excluded_or_failed"}
    log_memory_event("store", user_id, memory_id=item.id, detail={"type": mtype.value})
    return {
        "stored": True,
        "memory_id": item.id,
        "memory_type": item.type.value,
        "project_id": project_id,
        "content": item.content[:200],
    }


async def update_memory(
    memory_id: str,
    user_id: str,
    content: Optional[str] = None,
    description: Optional[str] = None,
    storage_dir: str = "memories",
) -> Dict[str, Any]:
    manager = get_manager(storage_dir)
    ok = await manager.update_memory(memory_id, content=content, description=description)
    if ok:
        log_memory_event("update", user_id, memory_id=memory_id)
    return {"updated": ok, "memory_id": memory_id}


async def delete_memory(
    memory_id: str,
    user_id: str,
    storage_dir: str = "memories",
) -> Dict[str, Any]:
    manager = get_manager(storage_dir)
    ok = await manager.delete_memory(memory_id)
    if ok:
        log_memory_event("delete", user_id, memory_id=memory_id)
    return {"deleted": ok, "memory_id": memory_id}


async def list_memories(
    user_id: str,
    limit: int = 20,
    storage_dir: str = "memories",
    project_id: Optional[str] = None,
    memory_type: Optional[str] = None,
) -> Dict[str, Any]:
    manager = get_manager(storage_dir)
    items = await manager.list_memories(
        user_id=user_id,
        project_id=project_id,
        memory_type=memory_type,
        limit=limit,
    )
    return {
        "user_id": user_id,
        "project_id": project_id,
        "count": len(items),
        "memories": items,
        "format": SIDECAR_V2,
    }


async def export_memories(
    user_id: str,
    query: Optional[str] = None,
    limit: int = 10,
    storage_dir: str = "memories",
    project_id: Optional[str] = None,
    scope: str = "user",
) -> Dict[str, Any]:
    manager = get_manager(storage_dir)
    if query:
        items = await manager.retrieve(
            query=query, user_id=user_id, project_id=project_id, top_k=limit
        )
    else:
        items = await manager.list_memories(
            user_id=user_id, project_id=project_id, limit=limit
        )
    return build_export_payload(
        user_id=user_id,
        memories=items,
        query=query,
        project_id=project_id,
        scope=scope,
    )


def format_tool_json(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)
