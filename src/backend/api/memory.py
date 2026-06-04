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
        mid = row.get("memory_id") or row.get("id") or ""
        if uid == user_id or str(mid).startswith(f"{user_id}_"):
            filtered.append(row)
    return filtered


@router.get("/memories", response_model=List[MemoryResponse])
async def list_memories(
    user_id: str = Query(..., description="User identifier"),
    layer: Optional[str] = Query(None, description="Memory layer filter"),
    limit: int = Query(20, ge=1, le=100)
):
    """List memories for a user (index-backed, user-scoped)."""
    from src.memory.service import get_shared_memory_manager

    manager = get_shared_memory_manager()
    rows = manager.storage.index.search(
        query="",
        user_id=user_id,
        memory_type=layer,
        limit=limit * 3,
    )
    rows = _rows_for_user(rows, user_id)[:limit]

    memories = []
    for row in rows:
        memories.append(
            MemoryResponse(
                memory_id=row.get("memory_id") or row.get("id", ""),
                content=(row.get("content") or "")[:200],
                layer=row.get("memory_type", "user"),
                created_at=str(row.get("created_at", "")),
                metadata={"user_id": user_id},
            )
        )
    return memories


@router.get("/memory/stats", response_model=MemoryStatsResponse)
async def get_memory_stats():
    """Get memory system statistics from actual files."""
    user_count = count_memories_by_type("user")
    feedback_count = count_memories_by_type("feedback")
    project_count = count_memories_by_type("project")
    reference_count = count_memories_by_type("reference")
    
    return MemoryStatsResponse(
        total=user_count + feedback_count + project_count + reference_count,
        user=user_count,
        feedback=feedback_count,
        project=project_count,
        reference=reference_count
    )


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
    return await recall_memories(
        user_id=body.get("user_id", "anonymous"),
        query=body.get("query", ""),
        limit=int(body.get("limit", 5)),
        project_id=body.get("project_id"),
    )


@router.patch("/memories/{memory_id}")
async def update_memory_endpoint(memory_id: str, body: dict):
    from src.mcp_server.tools import update_memory
    user_id = body.get("user_id", "anonymous")
    result = await update_memory(
        memory_id=memory_id,
        user_id=user_id,
        content=body.get("content"),
        description=body.get("description"),
    )
    if not result.get("updated"):
        raise HTTPException(status_code=404, detail="Memory not found")
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
    from src.memory.eval import run_recall_eval, GOLDEN_PATH
    from src.memory.service import get_shared_memory_manager

    manager = get_shared_memory_manager()
    try:
        report = await run_recall_eval(manager, fixture_path=GOLDEN_PATH)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Golden fixture not found")
    return report.to_dict()


@router.delete("/memories/{memory_id}")
async def delete_memory_endpoint(
    memory_id: str,
    user_id: str = Query("anonymous"),
):
    from src.mcp_server.tools import delete_memory
    result = await delete_memory(memory_id, user_id)
    if not result.get("deleted"):
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"status": "deleted", **result}
