import pytest
from unittest.mock import AsyncMock

from src.agent.loop_state import LoopState, LoopExitReason
from src.agent.query_loop import execute_query_loop, LoopEventType


@pytest.mark.asyncio
async def test_query_loop_emits_per_token():
    llm = AsyncMock()
    seen = []

    async def on_token(t):
        seen.append(t)

    async def stream_gen(**kwargs):
        cb = kwargs.get("on_token")
        if cb:
            await cb("A")
            await cb("B")
        return {"content": "AB", "stop_reason": "stop", "streamed": True}

    llm.generate_response_stream = stream_gen
    events = []

    def collect(ev):
        events.append(ev)

    state = LoopState(messages=[{"role": "user", "content": "hi"}], system_prompt="sys")
    await execute_query_loop(llm, state, tool_registry=None, max_turns=3, on_event=collect)

    token_contents = [e.content for e in events if e.type == LoopEventType.TOKEN]
    assert token_contents == ["A", "B"]
    assert "AB" not in token_contents or len(token_contents) == 2
