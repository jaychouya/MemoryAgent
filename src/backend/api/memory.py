from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
from pathlib import Path

router = APIRouter()
logger = logging.getLogger(__name__)

MEMORIES_DIR = Path("memories")


class MemoryResponse(BaseModel):
    """Memory response model."""
    memory_id: str
    content: str
    layer: str
    created_at: str
    metadata: dict = {}


class MemoryStatsResponse(BaseModel):
    """Memory statistics response."""
    total: int
    user: int
    feedback: int
    project: int
    reference: int


def count_memories_by_type(memory_type: str) -> int:
    """Count memories in a specific type directory."""
    type_dir = MEMORIES_DIR / memory_type
    if not type_dir.exists():
        return 0
    return len(list(type_dir.glob("*.md")))


def read_memory_file(file_path: Path) -> Optional[Dict]:
    """Read a memory file and extract metadata."""
    try:
        content = file_path.read_text(encoding="utf-8")
        lines = content.split("\n")
        
        metadata = {}
        content_start = 0
        in_frontmatter = False
        
        for i, line in enumerate(lines):
            if line.strip() == "---":
                if in_frontmatter:
                    content_start = i + 1
                    break
                in_frontmatter = True
                continue
            
            if in_frontmatter and ":" in line:
                key, value = line.split(":", 1)
                metadata[key.strip()] = value.strip()
        
        memory_content = "\n".join(lines[content_start:]).strip()
        
        return {
            "memory_id": file_path.stem,
            "content": memory_content[:200] + "..." if len(memory_content) > 200 else memory_content,
            "layer": file_path.parent.name,
            "created_at": metadata.get("created", ""),
            "metadata": {
                "type": metadata.get("type", ""),
                "description": metadata.get("description", "")
            }
        }
    except Exception as e:
        logger.warning(f"Failed to read memory file {file_path}: {e}")
        return None


def _rows_for_user(rows: List[Dict], user_id: str) -> List[Dict]:
    filtered = []
    for row in rows:
        uid = row.get("user_id")
        if uid == user_id:
            filtered.append(row)
    return filtered


@router.get("/memories")
async def list_memories(
    user_id: str = Query(..., description="User identifier"),
    layer: Optional[str] = Query(None, description="Memory layer filter"),
    project_id: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100)
):
    """List memories for a user (index-backed, user-scoped)."""
    from src.memory.service import get_shared_memory_manager

    manager = get_shared_memory_manager()
    rows = await manager.list_memories(
        user_id=user_id,
        project_id=project_id,
        memory_type=layer,
        limit=limit,
    )
    rows = [r for r in rows if not r.get("superseded_by")]
    return [
        {
            "memory_id": row.get("memory_id") or row.get("id", ""),
            "content": row.get("content", ""),
            "description": row.get("description", ""),
            "memory_type": row.get("memory_type", "user"),
            "layer": row.get("memory_type", "user"),
            "user_id": row.get("user_id") or user_id,
            "project_id": row.get("project_id"),
            "score": row.get("score", 0.0),
            "source_session_id": row.get("source_session_id"),
            "source_turn": row.get("source_turn"),
            "source_quote": row.get("source_quote"),
            "superseded_by": row.get("superseded_by"),
            "valid_until": row.get("valid_until"),
            "conflict_reason": row.get("conflict_reason"),
            "created_at": str(row.get("created_at", "")),
        }
        for row in rows
    ]


@router.get("/memories/archived")
async def list_archived_memories(
    user_id: str = Query(..., description="User identifier"),
    project_id: Optional[str] = Query(None),
    limit: int = Query(30, ge=1, le=100),
):
    """List superseded memories still on disk for audit."""
    from src.memory.service import get_shared_memory_manager

    manager = get_shared_memory_manager()
    rows = await manager.list_archived_memories(
        user_id=user_id,
        project_id=project_id,
        limit=limit,
    )
    return rows


@router.get("/memory/stats", response_model=MemoryStatsResponse)
async def get_memory_stats(
    user_id: Optional[str] = Query(None, description="Scope stats to one user (active index only)"),
    project_id: Optional[str] = Query(None),
):
    """Active memory counts from search index (excludes superseded/retired)."""
    from src.memory.service import get_shared_memory_manager

    manager = get_shared_memory_manager()
    stats = manager.get_active_stats(user_id=user_id, project_id=project_id)
    return MemoryStatsResponse(**stats)


@router.get("/memory/export")
async def export_memories_for_sidecar(
    user_id: str = Query(..., description="User identifier"),
    query: Optional[str] = Query(None, description="Optional recall query"),
    project_id: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=50),
):
    from src.mcp_server.tools import export_memories
    return await export_memories(
        user_id=user_id, query=query, limit=limit, project_id=project_id
    )


@router.post("/memory/recall")
async def recall_memories_sidecar(body: dict):
    from src.mcp_server.tools import recall_memories
    from src.mcp_server.workspace import effective_chat_scope
    from src.memory.paths import default_storage_dir

    user_id, project_id = effective_chat_scope(
        body.get("user_id", "anonymous"),
        body.get("project_id"),
    )
    return await recall_memories(
        user_id=user_id,
        query=body.get("query", ""),
        limit=int(body.get("limit", 5)),
        project_id=project_id or body.get("project_id"),
        storage_dir=default_storage_dir(),
    )


@router.patch("/memories/{memory_id}")
async def update_memory_endpoint(memory_id: str, body: dict):
    from src.mcp_server.tools import update_memory
    from src.memory.paths import default_storage_dir

    user_id = body.get("user_id", "anonymous")
    result = await update_memory(
        memory_id=memory_id,
        user_id=user_id,
        content=body.get("content"),
        description=body.get("description"),
        storage_dir=default_storage_dir(),
    )
    if not result.get("updated"):
        status = 403 if result.get("reason") == "forbidden" else 404
        raise HTTPException(status_code=status, detail=result.get("reason", "Memory not found"))
    return result


@router.get("/memory/audit")
async def get_memory_audit(limit: int = Query(50, ge=1, le=500)):
    from pathlib import Path
    import json
    path = Path(".memoryai/audit.jsonl")
    if not path.exists():
        return {"events": []}
    lines = path.read_text(encoding="utf-8").strip().split("\n")
    events = []
    for line in lines[-limit:]:
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return {"events": events}


@router.get("/memory/metrics")
async def get_memory_metrics(user_id: str = Query(default="eval_user")):
    from src.memory.eval import get_last_report
    from src.memory.service import get_shared_memory_manager

    manager = get_shared_memory_manager()
    stats = await manager.get_stats()
    report = get_last_report()
    payload = {
        "storage_stats": stats,
        "vector_count": manager.vector_store.size(),
        "last_eval": None,
    }
    if report:
        payload["last_eval"] = report.to_dict()
    return payload


@router.post("/memory/metrics/run-eval")
async def run_memory_eval():
    import tempfile

    from src.memory.eval import run_recall_eval, GOLDEN_PATH
    from src.memory.manager import MemoryManager

    try:
        with tempfile.TemporaryDirectory(prefix="memoryagent-eval-") as tmp:
            manager = MemoryManager(storage_dir=tmp)
            report = await run_recall_eval(manager, fixture_path=GOLDEN_PATH)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Golden fixture not found")
    return report.to_dict()


class ConflictResolveRequest(BaseModel):
    user_id: str = "anonymous"
    new_content: str
    memory_type: str = "user"
    keep_existing_id: Optional[str] = None
    supersede_ids: List[str] = []
    project_id: Optional[str] = None
    session_id: Optional[str] = None


@router.post("/memory/conflicts/resolve")
async def resolve_memory_conflict(body: ConflictResolveRequest):
    from src.memory.service import get_shared_memory_manager
    from src.memory.types import MemoryType

    manager = get_shared_memory_manager()
    if body.keep_existing_id and not body.supersede_ids:
        return {"ok": True, "kept": body.keep_existing_id, "stored": None}

    try:
        mem_type = MemoryType(body.memory_type)
    except ValueError:
        mem_type = MemoryType.USER

    if body.keep_existing_id:
        for old_id in body.supersede_ids:
            await manager.resolve_conflict(body.keep_existing_id, old_id, body.user_id)
        return {"ok": True, "kept": body.keep_existing_id, "stored": None}

    item = await manager.store_resolved_conflict(
        content=body.new_content,
        memory_type=mem_type,
        supersede_ids=body.supersede_ids,
        user_id=body.user_id,
        project_id=body.project_id,
        session_id=body.session_id,
    )
    if not item:
        raise HTTPException(status_code=400, detail="store_failed")
    return {"ok": True, "stored": item.id, "superseded": body.supersede_ids}


@router.delete("/memories/{memory_id}")
async def delete_memory_endpoint(
    memory_id: str,
    user_id: str = Query("anonymous"),
):
    from src.mcp_server.tools import delete_memory
    from src.memory.paths import default_storage_dir

    result = await delete_memory(memory_id, user_id, storage_dir=default_storage_dir())
    if not result.get("deleted"):
        status = 403 if result.get("reason") == "forbidden" else 404
        raise HTTPException(status_code=status, detail=result.get("reason", "Memory not found"))
    return {"status": "deleted", **result}
