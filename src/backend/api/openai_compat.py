"""OpenAI-compatible /v1/chat/completions for zero-change SDK integration."""

from __future__ import annotations

import json
import time
import uuid
from typing import Any, AsyncGenerator, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.backend.api.chat import (
    ChatRequest,
    _agent_result_from_loop_out,
    _chat_scope,
    _content_from_loop_out,
    _execute_chat,
    _memory_user_id,
    _persist_session,
    _resolve_llm,
    _resolve_memory_llm,
    _run_observer,
    get_agent_loop,
    sessions,
    _llm_not_ready_message,
)
from src.agent.query_loop import LoopEventType

router = APIRouter()


class OpenAIMessage(BaseModel):
    role: str
    content: Any = ""
    name: Optional[str] = None
    tool_call_id: Optional[str] = None


class OpenAIChatRequest(BaseModel):
    model: str = "memoryagent"
    messages: List[OpenAIMessage] = Field(min_length=1)
    stream: bool = False
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    user: Optional[str] = None
    session_id: Optional[str] = Field(
        default=None,
        description="MemoryAgent extension: conversation session key",
    )


def _completion_id() -> str:
    return f"chatcmpl-{uuid.uuid4().hex[:24]}"


def _message_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text") or ""))
        return "".join(parts)
    return str(content)


def _split_openai_messages(
    messages: List[OpenAIMessage],
) -> tuple[Optional[str], List[Dict[str, str]], str]:
    system_parts: List[str] = []
    convo: List[Dict[str, str]] = []
    for msg in messages:
        text = _message_text(msg.content)
        role = (msg.role or "").lower()
        if role == "system":
            if text:
                system_parts.append(text)
            continue
        if role in ("user", "assistant", "tool"):
            convo.append({"role": role, "content": text})
    if not convo:
        raise HTTPException(status_code=400, detail="messages must include a user message")
    last = convo[-1]
    if last.get("role") != "user":
        raise HTTPException(status_code=400, detail="last message must be from user")
    user_message = last.get("content") or ""
    context = convo[:-1]
    system_prompt = "\n\n".join(system_parts) if system_parts else None
    return system_prompt, context, user_message


def _to_chat_request(body: OpenAIChatRequest) -> tuple[ChatRequest, Optional[str], List[Dict[str, str]]]:
    system_prompt, context, user_message = _split_openai_messages(body.messages)
    session_id = (body.session_id or body.user or "openai-default").strip()
    user_id = (body.user or "openai-user").strip()
    request = ChatRequest(
        message=user_message,
        session_id=session_id,
        user_id=user_id,
        cross_session_memory=False,
    )
    return request, system_prompt, context


def _completion_response(
    completion_id: str,
    model: str,
    content: str,
) -> Dict[str, Any]:
    now = int(time.time())
    return {
        "id": completion_id,
        "object": "chat.completion",
        "created": now,
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        },
    }


def _chunk_sse(completion_id: str, model: str, delta: Dict[str, Any], finish: Optional[str] = None) -> str:
    payload = {
        "id": completion_id,
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": model,
        "choices": [{"index": 0, "delta": delta, "finish_reason": finish}],
    }
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


@router.get("/models")
async def list_models():
    return {
        "object": "list",
        "data": [
            {
                "id": "memoryagent",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "memoryagent",
            }
        ],
    }


@router.post("/chat/completions")
async def chat_completions(body: OpenAIChatRequest):
    request, system_prompt, context = _to_chat_request(body)
    user_id, project_id, session_key = _chat_scope(request)
    memory_user_id = _memory_user_id(user_id, request.session_id, request.cross_session_memory)
    sessions[session_key] = list(context)

    completion_id = _completion_id()
    model = body.model or "memoryagent"

    if body.stream:
        return StreamingResponse(
            _stream_openai(request, system_prompt, session_key, memory_user_id, project_id, completion_id, model),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    llm = _resolve_llm(request)
    not_ready = _llm_not_ready_message(request, llm)
    if not_ready:
        return _completion_response(completion_id, model, not_ready)

    if system_prompt:
        agent = get_agent_loop(llm, _resolve_memory_llm(llm))
        result = await agent.run(
            user_message=request.message,
            system_prompt=system_prompt,
            context_messages=sessions[session_key],
            session_id=request.session_id,
            user_id=memory_user_id,
            project_id=project_id,
        )
        _persist_session(session_key, request, result)
        await _run_observer(request, result, memory_user_id, project_id)
        content = result.content or ""
    else:
        result = await _execute_chat(request)
        content = result.content or ""

    return _completion_response(completion_id, model, content)


async def _stream_openai(
    request: ChatRequest,
    system_prompt: Optional[str],
    session_key: str,
    memory_user_id: str,
    project_id: str,
    completion_id: str,
    model: str,
) -> AsyncGenerator[str, None]:
    llm = _resolve_llm(request)
    not_ready = _llm_not_ready_message(request, llm)
    if not_ready:
        yield _chunk_sse(completion_id, model, {"role": "assistant", "content": ""})
        yield _chunk_sse(completion_id, model, {"content": not_ready})
        yield _chunk_sse(completion_id, model, {}, "stop")
        yield "data: [DONE]\n\n"
        return

    yield _chunk_sse(completion_id, model, {"role": "assistant", "content": ""})
    loop_out: Dict[str, Any] = {}
    agent = get_agent_loop(llm, _resolve_memory_llm(llm))
    async for loop_ev in agent.run_stream(
        user_message=request.message,
        system_prompt=system_prompt,
        context_messages=sessions[session_key],
        session_id=request.session_id,
        user_id=memory_user_id,
        project_id=project_id,
        loop_out=loop_out,
    ):
        if loop_ev.type == LoopEventType.TOKEN and loop_ev.content:
            yield _chunk_sse(completion_id, model, {"content": loop_ev.content})

    result = _agent_result_from_loop_out(loop_out)
    _persist_session(session_key, request, result)
    await _run_observer(request, result, memory_user_id, project_id)
    if not _content_from_loop_out(loop_out) and not (result.content or "").strip():
        yield _chunk_sse(completion_id, model, {"content": "（无回复内容）"})
    yield _chunk_sse(completion_id, model, {}, "stop")
    yield "data: [DONE]\n\n"
