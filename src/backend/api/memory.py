from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


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


@router.get("/memories", response_model=List[MemoryResponse])
async def list_memories(
    user_id: str = Query(..., description="User identifier"),
    layer: Optional[str] = Query(None, description="Memory layer filter"),
    limit: int = Query(20, ge=1, le=100)
):
    """
    List memories for a user.
    
    Args:
        user_id: User identifier
        layer: Optional layer filter (working, short_term, long_term, episodic)
        limit: Maximum number of memories to return
    """
    mock_memories = [
        MemoryResponse(
            memory_id="mem_001",
            content="User likes coffee",
            layer="long_term",
            created_at="2024-01-15T10:30:00",
            metadata={"category": "food_preference"}
        ),
        MemoryResponse(
            memory_id="mem_002",
            content="Had meeting about project X",
            layer="short_term",
            created_at="2024-01-20T14:00:00",
            metadata={"type": "event"}
        )
    ]
    
    if layer:
        mock_memories = [m for m in mock_memories if m.layer == layer]
    
    return mock_memories[:limit]


@router.get("/memory/stats", response_model=MemoryStatsResponse)
async def get_memory_stats():
    """Get memory system statistics."""
    return MemoryStatsResponse(
        total=42,
        user=12,
        feedback=8,
        project=15,
        reference=7
    )


@router.delete("/memories/{memory_id}")
async def delete_memory(memory_id: str):
    """
    Delete a specific memory.
    
    Args:
        memory_id: Memory identifier to delete
    """
    logger.info(f"Deleting memory {memory_id}")
    
    return {"status": "deleted", "memory_id": memory_id}
