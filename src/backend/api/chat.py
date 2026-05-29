from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging

from src.backend.services import get_llm_service, LLMService

router = APIRouter()
logger = logging.getLogger(__name__)

sessions: Dict[str, List[Dict[str, str]]] = {}

# 全局模型配置
global_model_config: Optional[Dict[str, str]] = None


class ModelConfigRequest(BaseModel):
    api_key: str
    base_url: str
    model: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    session_id: str = Field(default="default")
    user_id: str = Field(default="anonymous")
    llm_config: Optional[ModelConfigRequest] = None


class MemoryUpdate(BaseModel):
    type: str
    content: str
    layer: str
    action: str


class DecisionExplanation(BaseModel):
    action: str
    confidence: float
    reasoning: str


class ChatResponse(BaseModel):
    response: str
    memory_updates: List[MemoryUpdate] = []
    decision_explanation: Optional[DecisionExplanation] = None


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        session_key = f"{request.user_id}:{request.session_id}"
        if session_key not in sessions:
            sessions[session_key] = []
        
        sessions[session_key].append({
            "role": "user",
            "content": request.message
        })
        
        if len(sessions[session_key]) > 10:
            sessions[session_key] = sessions[session_key][-10:]
        
        if request.llm_config:
            llm = LLMService(
                api_key=request.llm_config.api_key,
                model=request.llm_config.model,
                base_url=request.llm_config.base_url
            )
        elif global_model_config:
            llm = LLMService(
                api_key=global_model_config["api_key"],
                model=global_model_config["model"],
                base_url=global_model_config["base_url"]
            )
        else:
            llm = get_llm_service()
        
        response_text = await llm.generate_response(
            message=request.message,
            context=sessions[session_key][:-1]
        )
        
        sessions[session_key].append({
            "role": "assistant",
            "content": response_text
        })
        
        memory_updates = []
        if "喜欢" in request.message or "like" in request.message.lower():
            memory_updates.append(MemoryUpdate(
                type="preference",
                content=request.message,
                layer="short_term",
                action="created"
            ))
        
        return ChatResponse(
            response=response_text,
            memory_updates=memory_updates,
            decision_explanation=DecisionExplanation(
                action="response_generation",
                confidence=0.9,
                reasoning="Generated response using LLM with conversation context"
            )
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return ChatResponse(
            response="抱歉，处理您的消息时出现了问题。请稍后再试。",
            memory_updates=[],
            decision_explanation=DecisionExplanation(
                action="error_fallback",
                confidence=0.0,
                reasoning=f"Error: {str(e)}"
            )
        )


@router.get("/sessions")
async def list_sessions(user_id: str = "anonymous"):
    user_sessions = []
    for key in sessions.keys():
        if key.startswith(f"{user_id}:"):
            session_id = key.split(":")[1]
            user_sessions.append({
                "session_id": session_id,
                "message_count": len(sessions[key])
            })
    return {"sessions": user_sessions}


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, user_id: str = "anonymous"):
    session_key = f"{user_id}:{session_id}"
    if session_key in sessions:
        del sessions[session_key]
        return {"status": "deleted", "session_id": session_id}
    raise HTTPException(status_code=404, detail="Session not found")


@router.post("/config")
async def save_config(config: ModelConfigRequest):
    try:
        global global_model_config
        global_model_config = {
            "api_key": config.api_key,
            "base_url": config.base_url,
            "model": config.model
        }
        return {"status": "success", "message": "配置已保存"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
