from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict
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


@router.get("/memories", response_model=List[MemoryResponse])
async def list_memories(
    user_id: str = Query(..., description="User identifier"),
    layer: Optional[str] = Query(None, description="Memory layer filter"),
    limit: int = Query(20, ge=1, le=100)
):
    """List memories for a user."""
    memories = []
    
    if layer:
        type_dirs = [MEMORIES_DIR / layer]
    else:
        type_dirs = [d for d in MEMORIES_DIR.iterdir() if d.is_dir()]
    
    for type_dir in type_dirs:
        if not type_dir.exists():
            continue
        
        for memory_file in type_dir.glob("*.md"):
            memory_data = read_memory_file(memory_file)
            if memory_data:
                memories.append(MemoryResponse(**memory_data))
    
    memories.sort(key=lambda m: m.created_at, reverse=True)
    return memories[:limit]


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


@router.delete("/memories/{memory_id}")
async def delete_memory(memory_id: str):
    """Delete a specific memory."""
    for memory_type in ["user", "feedback", "project", "reference"]:
        memory_file = MEMORIES_DIR / memory_type / f"{memory_id}.md"
        if memory_file.exists():
            memory_file.unlink()
            logger.info(f"Deleted memory {memory_id}")
            return {"status": "deleted", "memory_id": memory_id}
    
    raise HTTPException(status_code=404, detail="Memory not found")
