from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging
import json
from datetime import datetime
from pathlib import Path

from src.backend.services import get_llm_service, LLMService
from src.agent.loop import AgentLoop
from src.agent.tools.registry import get_tool_registry
from src.agent.tools.builtin import MemorySearchTool, MemoryStoreTool, ContextRetrieveTool
from src.agent.tools.advanced import SemanticPatchTool, SkillSearchTool, SkillCreateTool, TraceAnalysisTool
from src.agent.plans import (
    PlanModeManager,
    EnterPlanModeTool,
    ExitPlanModeTool,
    CreatePlanTool
)
from src.memory.manager import MemoryManager
from src.skills.graph import SkillGraph
from src.agent.reflection.tracer import ExecutionTracer

router = APIRouter()
logger = logging.getLogger(__name__)

sessions: Dict[str, List[Dict[str, str]]] = {}

SESSIONS_DIR = Path("sessions")
SESSIONS_DIR.mkdir(exist_ok=True)


def load_sessions():
    """Load sessions from disk."""
    global sessions
    for session_file in SESSIONS_DIR.glob("*.json"):
        try:
            with open(session_file) as f:
                data = json.load(f)
                sessions[data["key"]] = data["messages"]
        except Exception as e:
            logger.warning(f"Failed to load session {session_file}: {e}")


def save_session(session_key: str, messages: List[Dict]):
    """Save session to disk."""
    try:
        filename = session_key.replace(":", "_") + ".json"
        filepath = SESSIONS_DIR / filename
        with open(filepath, "w") as f:
            json.dump({"key": session_key, "messages": messages}, f, indent=2)
    except Exception as e:
        logger.warning(f"Failed to save session {session_key}: {e}")


load_sessions()

global_model_config: Optional[Dict[str, str]] = None

_agent_loop: Optional[AgentLoop] = None
_plan_manager: Optional[PlanModeManager] = None
_memory_manager: Optional[MemoryManager] = None
_skill_graph: Optional[SkillGraph] = None
_tracer: Optional[ExecutionTracer] = None


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


def get_agent_loop(llm_service) -> AgentLoop:
    global _agent_loop, _plan_manager, _memory_manager, _skill_graph, _tracer
    if _agent_loop is None:
        registry = get_tool_registry()
        
        _memory_manager = MemoryManager(llm_service=llm_service)
        _skill_graph = SkillGraph()
        _tracer = ExecutionTracer()
        
        registry.register(MemorySearchTool(_memory_manager))
        registry.register(MemoryStoreTool(_memory_manager))
        registry.register(ContextRetrieveTool())
        registry.register(SemanticPatchTool())
        registry.register(SkillSearchTool(_skill_graph))
        registry.register(SkillCreateTool(_skill_graph))
        registry.register(TraceAnalysisTool(_tracer))
        
        _plan_manager = PlanModeManager()
        registry.register(EnterPlanModeTool(_plan_manager))
        registry.register(ExitPlanModeTool(_plan_manager))
        registry.register(CreatePlanTool(_plan_manager))
        
        _agent_loop = AgentLoop(
            llm_service=llm_service,
            tool_registry=registry,
            memory_manager=_memory_manager,
            max_turns=10
        )
    return _agent_loop


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        session_key = f"{request.user_id}:{request.session_id}"
        if session_key not in sessions:
            sessions[session_key] = []
        
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
        
        agent = get_agent_loop(llm)
        
        result = await agent.run(
            user_message=request.message,
            context_messages=sessions[session_key],
            session_id=request.session_id,
            user_id=request.user_id
        )
        
        sessions[session_key].append({
            "role": "user",
            "content": request.message,
            "timestamp": datetime.now().isoformat()
        })
        sessions[session_key].append({
            "role": "assistant",
            "content": result.content,
            "timestamp": datetime.now().isoformat()
        })
        
        save_session(session_key, sessions[session_key])
        
        if len(sessions[session_key]) > 20:
            sessions[session_key] = sessions[session_key][-20:]
        
        memory_updates = []
        if result.state and result.state.memories_used:
            for mem in result.state.memories_used:
                memory_updates.append(MemoryUpdate(
                    type="retrieved",
                    content=mem,
                    layer="memory",
                    action="used"
                ))
        
        return ChatResponse(
            response=result.content,
            memory_updates=memory_updates,
            decision_explanation=DecisionExplanation(
                action=result.stop_reason.value,
                confidence=0.9,
                reasoning=f"Agent completed in {result.state.turn_count} turns"
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
            messages = sessions[key]
            last_message = messages[-1] if messages else None
            user_sessions.append({
                "session_id": session_id,
                "message_count": len(messages),
                "last_message": last_message.get("content", "")[:50] if last_message else "",
                "last_timestamp": last_message.get("timestamp", "") if last_message else "",
                "created_at": messages[0].get("timestamp", "") if messages else ""
            })
    user_sessions.sort(key=lambda x: x.get("last_timestamp", ""), reverse=True)
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
        global global_model_config, _agent_loop
        global_model_config = {
            "api_key": config.api_key,
            "base_url": config.base_url,
            "model": config.model
        }
        _agent_loop = None
        return {"status": "success", "message": "配置已保存"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
