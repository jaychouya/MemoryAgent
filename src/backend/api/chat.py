from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, AsyncGenerator
import logging
import json
import asyncio
from datetime import datetime
from pathlib import Path

from src.backend.services import get_llm_service, LLMService
from src.agent.loop import AgentLoop, AgentResult, AgentState, StopReason, _REASON_MAP
from src.agent.query_loop import LoopEventType
from src.agent.loop_state import LoopExitReason, LoopState
from src.agent.streaming import StreamingManager, StreamEvent, StreamEventType
from src.agent.tools.registry import get_tool_registry, ToolRegistry
from src.agent.tools.builtin import MemorySearchTool, MemoryStoreTool, ContextRetrieveTool
from src.agent.tools.advanced import SemanticPatchTool, SkillSearchTool, SkillCreateTool, TraceAnalysisTool
from src.agent.plans import (
    PlanModeManager,
    EnterPlanModeTool,
    ExitPlanModeTool,
    CreatePlanTool
)
from src.memory.manager import MemoryManager
from src.memory.service import get_shared_memory_manager
from src.memory.observer import MemoryObserver
from src.memory.citations import MemoryCitation
from src.skills.graph import SkillGraph
from src.agent.reflection.tracer import ExecutionTracer
from src.backend.chat_utils import ChatExporter, FileUploader
from src.backend.config_manager import ConfigManager

router = APIRouter()
logger = logging.getLogger(__name__)

sessions: Dict[str, List[Dict[str, str]]] = {}
session_metadata: Dict[str, Dict[str, Any]] = {}

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
    project_id: Optional[str] = Field(default=None, description="Repo/project scope for memories")
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


class MemoryCitationResponse(BaseModel):
    memory_id: str
    memory_type: str
    description: str
    content_snippet: str
    score: float
    age_days: int
    is_stale: bool
    selection_reason: str
    evidence_level: str = "L1"
    source_session_id: str = ""
    source_turn: int = 0
    source_quote: str = ""
    l0_path: str = ""


class ChatResponse(BaseModel):
    response: str
    memory_updates: List[MemoryUpdate] = []
    memory_citations: List[MemoryCitationResponse] = []
    decision_explanation: Optional[DecisionExplanation] = None


def get_agent_loop(llm_service) -> AgentLoop:
    global _agent_loop, _plan_manager, _memory_manager, _skill_graph, _tracer, _tool_registry
    if _agent_loop is None:
        # 重置工具注册表，避免重复注册
        _tool_registry = ToolRegistry()
        
        _memory_manager = get_shared_memory_manager(llm_service=llm_service)
        _skill_graph = SkillGraph()
        _tracer = ExecutionTracer()
        
        _tool_registry.register(MemorySearchTool(_memory_manager))
        _tool_registry.register(MemoryStoreTool(_memory_manager))
        _tool_registry.register(ContextRetrieveTool())
        _tool_registry.register(SemanticPatchTool())
        _tool_registry.register(SkillSearchTool(_skill_graph))
        _tool_registry.register(SkillCreateTool(_skill_graph))
        _tool_registry.register(TraceAnalysisTool(_tracer))
        
        _plan_manager = PlanModeManager()
        _tool_registry.register(EnterPlanModeTool(_plan_manager))
        _tool_registry.register(ExitPlanModeTool(_plan_manager))
        _tool_registry.register(CreatePlanTool(_plan_manager))
        
        _agent_loop = AgentLoop(
            llm_service=llm_service,
            tool_registry=_tool_registry,
            memory_manager=_memory_manager,
            max_turns=10
        )
    return _agent_loop


def _resolve_llm(request: ChatRequest) -> LLMService:
    if request.llm_config:
        return LLMService(
            api_key=request.llm_config.api_key,
            model=request.llm_config.model,
            base_url=request.llm_config.base_url,
        )
    if global_model_config:
        return LLMService(
            api_key=global_model_config["api_key"],
            model=global_model_config["model"],
            base_url=global_model_config["base_url"],
        )
    return get_llm_service()


def _truncate_session_messages(messages: List[Dict]) -> List[Dict]:
    if len(messages) <= 20:
        return messages
    truncated = []
    count = 0
    i = len(messages) - 1
    while i >= 0 and count < 20:
        msg = messages[i]
        if msg.get("role") == "tool":
            j = i - 1
            while j >= 0 and messages[j].get("role") == "tool":
                j -= 1
            for k in range(j, i + 1):
                truncated.insert(0, messages[k])
                count += 1
            i = j - 1
        else:
            truncated.insert(0, msg)
            count += 1
            i -= 1
    return truncated


def _persist_session(session_key: str, request: ChatRequest, result) -> List[Dict]:
    if result.state and result.state.messages:
        sessions[session_key] = result.state.messages
    else:
        sessions[session_key].append({
            "role": "user",
            "content": request.message,
            "timestamp": datetime.now().isoformat(),
        })
        sessions[session_key].append({
            "role": "assistant",
            "content": result.content,
            "timestamp": datetime.now().isoformat(),
        })
    sessions[session_key] = _truncate_session_messages(sessions[session_key])
    save_session(session_key, sessions[session_key])
    return sessions[session_key]


def _citations_from_result(result) -> List[MemoryCitationResponse]:
    if not result.state or not result.state.memory_citations:
        return []
    return [
        MemoryCitationResponse(**c.to_dict())
        for c in result.state.memory_citations
    ]


def _memory_updates_from_result(result) -> List[MemoryUpdate]:
    updates = []
    if result.state and result.state.memory_citations:
        for c in result.state.memory_citations:
            updates.append(MemoryUpdate(
                type=c.memory_type,
                content=c.content_snippet,
                layer="memory",
                action="used",
            ))
    elif result.state and result.state.memories_used:
        for mem in result.state.memories_used:
            updates.append(MemoryUpdate(
                type="retrieved",
                content=mem,
                layer="memory",
                action="used",
            ))
    return updates


def _chat_scope(request: ChatRequest):
    from src.mcp_server.workspace import effective_chat_scope

    user_id, project_id = effective_chat_scope(request.user_id, request.project_id)
    return user_id, project_id, f"{user_id}:{request.session_id}"


async def _run_observer(
    request: ChatRequest,
    result,
    user_id: str = None,
    project_id: str = None,
):
    global _memory_manager
    if not _memory_manager or not result.state:
        return
    uid = user_id or request.user_id
    pid = project_id if project_id is not None else request.project_id
    try:
        observer = MemoryObserver(_memory_manager)
        await observer.observe_turn(
            user_message=request.message,
            assistant_message=result.content or "",
            user_id=uid,
            session_id=request.session_id,
            project_id=pid,
        )
    except Exception as e:
        logger.warning(f"Memory observer failed: {e}")


def _schedule_observer(
    request: ChatRequest, result, user_id: str = None, project_id: str = None
) -> None:
    from src.utils.config import settings

    if not settings.MEMORY_OBSERVER_ASYNC:
        return
    asyncio.create_task(_run_observer(request, result, user_id, project_id))


async def _await_observer_if_sync(
    request: ChatRequest, result, user_id: str = None, project_id: str = None
) -> None:
    from src.utils.config import settings

    if settings.MEMORY_OBSERVER_ASYNC:
        _schedule_observer(request, result, user_id, project_id)
    else:
        await _run_observer(request, result, user_id, project_id)


def _agent_result_from_loop_out(loop_out: dict) -> AgentResult:
    loop_state = loop_out.get("state")
    if loop_state is None:
        loop_state = LoopState()
    exit_reason = loop_out.get("exit_reason", LoopExitReason.ERROR)
    content = loop_out.get("content", "") or ""
    stop = _REASON_MAP.get(exit_reason, StopReason.ERROR)
    state = AgentState(
        messages=loop_state.messages,
        turn_count=loop_state.turn_count,
        tokens_used=loop_state.tokens_used,
        tools_called=loop_state.tools_called,
        memories_used=loop_state.memories_used,
        memory_citations=loop_state.memory_citations,
        is_plan_mode=loop_state.is_plan_mode,
        has_attempted_reactive_compact=loop_state.has_attempted_reactive_compact,
        output_recovery_count=loop_state.output_recovery_count,
    )
    return AgentResult(
        content=content,
        stop_reason=stop,
        state=state,
        metadata={"exit_reason": exit_reason.value if hasattr(exit_reason, "value") else str(exit_reason)},
    )


async def _execute_chat(request: ChatRequest):
    user_id, project_id, session_key = _chat_scope(request)
    if session_key not in sessions:
        sessions[session_key] = []
    llm = _resolve_llm(request)
    agent = get_agent_loop(llm)
    result = await agent.run(
        user_message=request.message,
        context_messages=sessions[session_key],
        session_id=request.session_id,
        user_id=user_id,
        project_id=project_id,
    )
    _persist_session(session_key, request, result)
    await _await_observer_if_sync(request, result, user_id, project_id)
    return result


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        result = await _execute_chat(request)
        return ChatResponse(
            response=result.content,
            memory_updates=_memory_updates_from_result(result),
            memory_citations=_citations_from_result(result),
            decision_explanation=DecisionExplanation(
                action=result.stop_reason.value,
                confidence=0.9,
                reasoning=f"Agent completed in {result.state.turn_count} turns",
            ),
        )
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        error_msg = str(e)
        return ChatResponse(
            response=f"处理消息时出现错误: {error_msg}\n\n请检查配置或稍后重试。",
            memory_updates=[],
            decision_explanation=DecisionExplanation(
                action="error_fallback",
                confidence=0.0,
                reasoning=f"Error: {str(e)}",
            ),
        )


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    user_id, project_id, session_key = _chat_scope(request)

    async def event_generator() -> AsyncGenerator[str, None]:
        streamer = StreamingManager()
        if session_key not in sessions:
            sessions[session_key] = []
        loop_out: Dict[str, Any] = {}
        try:
            llm = _resolve_llm(request)
            agent = get_agent_loop(llm)
            async for loop_ev in agent.run_stream(
                user_message=request.message,
                context_messages=sessions[session_key],
                session_id=request.session_id,
                user_id=user_id,
                project_id=project_id,
                loop_out=loop_out,
            ):
                if loop_ev.type == LoopEventType.TOKEN:
                    yield streamer.create_token_event(loop_ev.content).to_sse()
                elif loop_ev.type == LoopEventType.TOOL_CALL:
                    yield streamer.create_tool_call_event(
                        loop_ev.content,
                        loop_ev.metadata or {},
                    ).to_sse()
                elif loop_ev.type == LoopEventType.TOOL_RESULT:
                    yield streamer.create_tool_result_event(
                        loop_ev.metadata.get("tool_name", "tool"),
                        "error" if loop_ev.metadata.get("is_error") else "completed",
                    ).to_sse()
                elif loop_ev.type == LoopEventType.ERROR:
                    yield streamer.create_error_event(loop_ev.content).to_sse()

            result = _agent_result_from_loop_out(loop_out)
            _persist_session(session_key, request, result)
            await _await_observer_if_sync(request, result, user_id, project_id)

            for cit in _citations_from_result(result):
                meta_evt = StreamEvent(
                    type=StreamEventType.TOOL_RESULT,
                    content=cit.content_snippet[:200],
                    metadata={"source": "memory", "citation": cit.model_dump()},
                )
                yield meta_evt.to_sse()

            done = streamer.create_done_event()
            done.metadata["citations"] = [
                c.model_dump() for c in _citations_from_result(result)
            ]
            done.metadata["response"] = result.content
            yield done.to_sse()
        except Exception as e:
            logger.error(f"Stream chat error: {e}", exc_info=True)
            yield streamer.create_error_event(str(e)).to_sse()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/sessions")
async def list_sessions(user_id: str = "anonymous"):
    user_sessions = []
    for key in sessions.keys():
        if key.startswith(f"{user_id}:"):
            session_id = key.split(":")[1]
            messages = sessions[key]
            last_message = messages[-1] if messages else None
            
            # 从第一条用户消息中提取会话名称
            meta = session_metadata.get(key, {})
            name = meta.get("name") or session_id
            if not meta.get("name") and messages and isinstance(messages, list):
                first_user_msg = next((m for m in messages if m.get("role") == "user"), None)
                if first_user_msg:
                    content = first_user_msg.get("content", "")
                    name = content[:25] + ("..." if len(content) > 25 else "")
            
            user_sessions.append({
                "session_id": session_id,
                "name": name,
                "message_count": len(messages) if isinstance(messages, list) else 0,
                "last_message": last_message.get("content", "")[:50] if last_message else "",
                "last_timestamp": last_message.get("timestamp", "") if last_message else "",
                "created_at": messages[0].get("timestamp", "") if messages and isinstance(messages, list) and len(messages) > 0 else ""
            })
    user_sessions.sort(key=lambda x: x.get("last_timestamp", ""), reverse=True)
    return {"sessions": user_sessions}


@router.get("/sessions/{session_id}/messages")
async def get_session_messages(session_id: str, user_id: str = "anonymous"):
    """Get messages for a specific session."""
    session_key = f"{user_id}:{session_id}"
    if session_key in sessions:
        messages = sessions[session_key]
        if isinstance(messages, list):
            return {"messages": messages}
    return {"messages": []}


@router.post("/sessions/rename")
async def rename_session(request: dict):
    """Rename a session."""
    session_id = request.get("session_id")
    user_id = request.get("user_id", "anonymous")
    new_name = request.get("name")
    
    session_key = f"{user_id}:{session_id}"
    if session_key in sessions:
        session_metadata[session_key] = {"name": new_name}
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="Session not found")


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


@router.get("/sessions/{session_id}/export")
async def export_session(
    session_id: str,
    user_id: str = "anonymous",
    format: str = "json"
):
    """Export chat history in various formats."""
    session_key = f"{user_id}:{session_id}"
    
    if session_key not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages = sessions[session_key]
    
    if format == "json":
        content = ChatExporter.to_json(messages)
        media_type = "application/json"
        filename = f"{session_id}.json"
    elif format == "markdown" or format == "md":
        content = ChatExporter.to_markdown(messages)
        media_type = "text/markdown"
        filename = f"{session_id}.md"
    elif format == "text" or format == "txt":
        content = ChatExporter.to_text(messages)
        media_type = "text/plain"
        filename = f"{session_id}.txt"
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
    
    return {
        "content": content,
        "filename": filename,
        "format": format,
        "message_count": len(messages)
    }


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    user_id: str = "anonymous"
):
    """Upload a file for context."""
    try:
        content = await file.read()
        result = await FileUploader.save_upload(
            filename=file.filename,
            content=content,
            user_id=user_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/uploads/{user_id}")
async def list_uploads(user_id: str):
    """List user's uploaded files."""
    files = FileUploader.get_user_files(user_id)
    return {"files": files, "count": len(files)}


@router.get("/uploads/{user_id}/{filename}")
async def get_upload_content(user_id: str, filename: str):
    """Get uploaded file content."""
    file_path = Path("uploads") / user_id / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    content = FileUploader.read_file(str(file_path))
    if content is None:
        raise HTTPException(status_code=500, detail="Failed to read file")
    
    return {
        "filename": filename,
        "content": content,
        "size": len(content)
    }


# 初始化配置管理器
config_manager = ConfigManager()


@router.get("/config/presets")
async def get_config_presets():
    """Get available preset configurations."""
    return config_manager.get_presets()


@router.get("/config/guide/{provider}")
async def get_setup_guide(provider: str):
    """Get setup guide for a provider."""
    return config_manager.get_setup_guide(provider)


@router.post("/config/quick-setup")
async def quick_setup(request: dict):
    """Quick setup with preset provider."""
    provider = request.get("provider")
    api_key = request.get("api_key")
    model = request.get("model")
    
    if not provider or not api_key:
        raise HTTPException(
            status_code=400,
            detail="provider and api_key are required"
        )
    
    result = config_manager.quick_setup(provider, api_key, model)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    # 同时更新全局配置
    global global_model_config, _agent_loop
    config = config_manager.load_config()
    if config:
        global_model_config = {
            "api_key": config["api_key"],
            "base_url": config["base_url"],
            "model": config["model"]
        }
        _agent_loop = None
    
    return result
