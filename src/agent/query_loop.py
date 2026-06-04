"""
queryLoop — Claude Code-style agent heart.

Per turn: prepare messages → call model → needsFollowUp? → run tools → append results.
"""

import inspect
import logging
from dataclasses import dataclass, replace
from enum import Enum
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional, Tuple

from src.agent.loop_state import (
    LoopState,
    LoopExitReason,
    is_prompt_too_long_error,
    is_output_truncated,
)
from src.agent.tool_executor import (
    StreamingToolExecutor,
    build_tool_result_messages,
)

logger = logging.getLogger(__name__)

MAX_OUTPUT_RECOVERY = 3


def _maybe_compress_tool_results(results: List[Dict]) -> List[Dict]:
    from src.utils.config import settings
    from src.agent.ccr_store import compress_with_ccr

    if not settings.CCR_ENABLED:
        return results
    out = []
    for r in results:
        content = str(r.get("content", ""))
        if len(content) <= settings.CCR_OFFLOAD_THRESHOLD:
            out.append(r)
            continue
        preview, ref_id, stats = compress_with_ccr(
            content,
            settings.CCR_STORAGE_DIR,
            settings.CCR_OFFLOAD_THRESHOLD,
            settings.CCR_PREVIEW_CHARS,
        )
        meta = dict(r.get("metadata") or {})
        meta["ccr"] = stats
        if ref_id:
            meta["ccr_ref"] = ref_id
        out.append({**r, "content": preview, "metadata": meta})
    return out
OUTPUT_NUDGE = (
    "Output token limit hit. Resume directly from the cutoff — no apology, "
    "no recap. Split remaining work into smaller steps."
)


class LoopEventType(str, Enum):
    TOKEN = "token"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    TURN_START = "turn_start"
    DONE = "done"
    ERROR = "error"


@dataclass
class LoopEvent:
    type: LoopEventType
    content: str = ""
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


LoopEventCallback = Optional[Callable[[LoopEvent], None]]


async def execute_query_loop(
    llm_service,
    state: LoopState,
    tool_registry=None,
    context_compressor=None,
    max_turns: int = 50,
    user_id: str = None,
    session_id: str = None,
    on_event: LoopEventCallback = None,
) -> Tuple[LoopState, LoopExitReason, str]:
    executor = StreamingToolExecutor(tool_registry)
    exit_reason = LoopExitReason.COMPLETED
    final_content = ""

    def emit(ev: LoopEvent):
        if on_event:
            on_event(ev)

    while state.turn_count < max_turns:
        state = replace(state, turn_count=state.turn_count + 1)
        emit(LoopEvent(LoopEventType.TURN_START, metadata={"turn": state.turn_count}))

        messages_for_query = list(state.messages)
        if state.output_recovery_count > 0:
            messages_for_query.append({"role": "user", "content": OUTPUT_NUDGE})

        streamed_tokens = False

        async def on_token(delta: str):
            nonlocal streamed_tokens
            streamed_tokens = True
            emit(LoopEvent(LoopEventType.TOKEN, content=delta))

        try:
            response = await _call_model(
                llm_service,
                messages_for_query,
                state.system_prompt,
                tool_registry,
                on_token=on_token,
            )
        except Exception as e:
            if (
                is_prompt_too_long_error(e)
                and context_compressor
                and not state.has_attempted_reactive_compact
            ):
                compressed = await context_compressor.compress(
                    state.messages, force_level=4
                )
                state = replace(
                    state,
                    messages=compressed,
                    has_attempted_reactive_compact=True,
                    turn_count=state.turn_count - 1,
                )
                continue

            if is_prompt_too_long_error(e):
                exit_reason = LoopExitReason.PROMPT_TOO_LONG
                final_content = "上下文过长，压缩后仍无法继续。请新开对话或缩短输入。"
                emit(LoopEvent(LoopEventType.ERROR, content=final_content))
                break

            exit_reason = LoopExitReason.ERROR
            final_content = f"AI 服务错误: {e}"
            emit(LoopEvent(LoopEventType.ERROR, content=final_content))
            break

        if is_output_truncated(response):
            if state.output_recovery_count < MAX_OUTPUT_RECOVERY:
                state = replace(
                    state,
                    output_recovery_count=state.output_recovery_count + 1,
                    turn_count=state.turn_count - 1,
                )
                continue
            exit_reason = LoopExitReason.OUTPUT_TRUNCATED
            final_content = response.get("content", "") or "输出过长且无法恢复。"
            break

        tool_calls = response.get("tool_calls") or []
        text = response.get("content") or ""
        if text and not streamed_tokens and not response.get("streamed"):
            emit(LoopEvent(LoopEventType.TOKEN, content=text))

        if not tool_calls:
            exit_reason = LoopExitReason.COMPLETED
            final_content = text
            state = replace(
                state,
                messages=state.messages + [{"role": "assistant", "content": final_content}],
                final_content=final_content,
                has_attempted_reactive_compact=False,
                output_recovery_count=0,
            )
            break

        state = replace(
            state,
            messages=state.messages + [{
                "role": "assistant",
                "content": text,
                "tool_calls": tool_calls,
            }],
        )

        for tc in tool_calls:
            emit(LoopEvent(
                LoopEventType.TOOL_CALL,
                content=tc.get("function", {}).get("name", "tool"),
                metadata={"tool_call_id": tc.get("id")},
            ))

        executor.schedule_all(tool_calls, user_id=user_id, session_id=session_id)
        raw_results = await executor.collect(tool_calls)
        raw_results = _maybe_compress_tool_results(raw_results)

        for r in raw_results:
            emit(LoopEvent(
                LoopEventType.TOOL_RESULT,
                content=str(r.get("content", ""))[:500],
                metadata={
                    "tool_name": r.get("tool_name"),
                    "is_error": r.get("is_error", False),
                },
            ))

        tools_called = state.tools_called + [
            r.get("tool_name", "unknown") for r in raw_results
        ]
        tool_messages = build_tool_result_messages(tool_calls, raw_results)
        new_messages = state.messages + tool_messages
        if context_compressor and getattr(context_compressor, "maybe_inject_symbolic", None):
            new_messages = context_compressor.maybe_inject_symbolic(new_messages)
        state = replace(
            state,
            messages=new_messages,
            tools_called=tools_called,
            has_attempted_reactive_compact=False,
            output_recovery_count=0,
        )
    else:
        exit_reason = LoopExitReason.MAX_TURNS
        final_content = "已达到最大思考轮次，请简化问题后重试。"

    emit(LoopEvent(
        LoopEventType.DONE,
        metadata={"reason": exit_reason.value, "content": final_content},
    ))
    state = replace(state, final_content=final_content)
    return state, exit_reason, final_content


async def query_loop(
    llm_service,
    state: LoopState,
    loop_out: Optional[Dict[str, Any]] = None,
    **kwargs,
) -> AsyncGenerator[LoopEvent, None]:
    """Yield loop events as they are produced (not buffered until completion)."""
    import asyncio

    queue: asyncio.Queue = asyncio.Queue()

    def on_event(ev: LoopEvent):
        queue.put_nowait(ev)

    async def worker():
        try:
            final_state, exit_reason, final_content = await execute_query_loop(
                llm_service, state, on_event=on_event, **kwargs
            )
            if loop_out is not None:
                loop_out.update(
                    state=final_state,
                    exit_reason=exit_reason,
                    content=final_content,
                )
        except Exception as e:
            logger.exception("query_loop worker failed")
            on_event(LoopEvent(LoopEventType.ERROR, content=str(e)))
            if loop_out is not None:
                loop_out.update(
                    error=str(e),
                    exit_reason=LoopExitReason.ERROR,
                    content=str(e),
                )
        finally:
            await queue.put(None)

    task = asyncio.create_task(worker())
    try:
        while True:
            ev = await queue.get()
            if ev is None:
                break
            yield ev
    finally:
        await task


async def _call_model(
    llm_service,
    messages,
    system_prompt,
    tool_registry,
    on_token=None,
):
    full_messages = [{"role": "system", "content": system_prompt}] + messages
    tools = tool_registry.get_function_schemas() if tool_registry else None
    stream_fn = getattr(llm_service, "generate_response_stream", None)
    if (
        on_token
        and not tools
        and stream_fn is not None
        and inspect.iscoroutinefunction(stream_fn)
    ):
        return await stream_fn(messages=full_messages, on_token=on_token)
    return await llm_service.generate_response(messages=full_messages, tools=tools)
