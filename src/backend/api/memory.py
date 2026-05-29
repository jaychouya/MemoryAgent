from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
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
    # TODO: Integrate with actual memory manager
    # For now, return mock data
    
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


@router.delete("/memories/{memory_id}")
async def delete_memory(memory_id: str):
    """
    Delete a specific memory.
    
    Args:
        memory_id: Memory identifier to delete
    """
    # TODO: Integrate with actual memory manager
    logger.info(f"Deleting memory {memory_id}")
    
    return {"status": "deleted", "memory_id": memory_id}
