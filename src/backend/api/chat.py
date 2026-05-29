from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str = Field(..., min_length=1, max_length=10000)
    session_id: str = Field(default="default")
    user_id: str = Field(default="anonymous")


class MemoryUpdate(BaseModel):
    """Memory update information."""
    type: str
    content: str
    layer: str
    action: str


class DecisionExplanation(BaseModel):
    """Decision explanation."""
    action: str
    confidence: float
    reasoning: str


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str
    memory_updates: List[MemoryUpdate] = []
    decision_explanation: Optional[DecisionExplanation] = None


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process a chat message.
    
    This endpoint:
    1. Receives user message
    2. Processes through memory system
    3. Generates response
    4. Returns response with memory updates
    """
    try:
        # TODO: Integrate with actual agent and memory manager
        # For now, return a mock response
        
        response = f"I received your message: '{request.message}'. "
        
        # Simulate memory extraction
        memory_updates = []
        if "like" in request.message.lower() or "喜欢" in request.message:
            memory_updates.append(MemoryUpdate(
                type="preference",
                content=request.message,
                layer="short_term",
                action="created"
            ))
            response += "I'll remember your preference!"
        
        return ChatResponse(
            response=response,
            memory_updates=memory_updates,
            decision_explanation=DecisionExplanation(
                action="response_generation",
                confidence=0.9,
                reasoning="Processed user message and extracted preferences"
            )
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
