"""
Agent Loop — delegates to queryLoop (Claude Code-style main loop).
"""

import logging
from typing import List, Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from src.agent.prompts.assembler import get_prompt_assembler
from src.agent.context import ContextCompressor
from src.agent.query_loop import execute_query_loop, query_loop, LoopEvent, LoopEventType
from src.agent.loop_state import LoopState, LoopExitReason
from src.memory.citations import build_citations, citations_to_legacy_strings

logger = logging.getLogger(__name__)


class StopReason(str, Enum):
    END_TURN = "end_turn"
    MAX_TURNS = "max_turns"
    ERROR = "error"
    USER_ABORT = "user_abort"
    PROMPT_TOO_LONG = "prompt_too_long"
    OUTPUT_TRUNCATED = "max_output_tokens_recovery"


_REASON_MAP = {
    LoopExitReason.COMPLETED: StopReason.END_TURN,
    LoopExitReason.MAX_TURNS: StopReason.MAX_TURNS,
    LoopExitReason.ERROR: StopReason.ERROR,
    LoopExitReason.PROMPT_TOO_LONG: StopReason.PROMPT_TOO_LONG,
    LoopExitReason.OUTPUT_TRUNCATED: StopReason.OUTPUT_TRUNCATED,
    LoopExitReason.USER_ABORT: StopReason.USER_ABORT,
}


@dataclass
class AgentState:
    messages: List[Dict[str, Any]] = field(default_factory=list)
    turn_count: int = 0
    tokens_used: int = 0
    tools_called: List[str] = field(default_factory=list)
    memories_used: List[str] = field(default_factory=list)
    memory_citations: List = field(default_factory=list)
    is_plan_mode: bool = False
    has_attempted_reactive_compact: bool = False
    output_recovery_count: int = 0


@dataclass
class AgentResult:
    content: str
    stop_reason: StopReason
    state: AgentState
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentLoop:
    def __init__(
        self,
        llm_service,
        tool_registry=None,
        memory_manager=None,
        context_manager=None,
        max_turns: int = 50,
    ):
        self.llm = llm_service
        self.tools = tool_registry
        self.memory = memory_manager
        self.context = context_manager or ContextCompressor(llm_service)
        self.max_turns = max_turns
        self.user_id = None
        self.session_id = None

    async def run(
        self,
        user_message: str,
        system_prompt: str = None,
        context_messages: List[Dict] = None,
        session_id: str = None,
        user_id: str = None,
        project_id: str = None,
    ) -> AgentResult:
        self.user_id = user_id
        self.session_id = session_id
        self._project_id = project_id

        messages = list(context_messages or [])
        messages.append({"role": "user", "content": user_message})

        memories = []
        memory_citations = []
        if self.memory and user_id:
            try:
                memories = await self.memory.retrieve(
                    user_id=user_id,
                    query=user_message,
                    session_id=session_id,
                    project_id=project_id,
                    top_k=5,
                )
                memory_citations = build_citations(memories[:5])
            except Exception as e:
                logger.warning(f"Memory retrieval failed: {e}")

        if not system_prompt:
            system_prompt = self._build_system_prompt(memories)

        loop_state = LoopState(
            messages=messages,
            memory_citations=memory_citations,
            memories_used=citations_to_legacy_strings(memory_citations),
            system_prompt=system_prompt,
        )

        loop_state, exit_reason, final_content = await execute_query_loop(
            llm_service=self.llm,
            state=loop_state,
            tool_registry=self.tools,
            context_compressor=self.context,
            max_turns=self.max_turns,
            user_id=user_id,
            session_id=session_id,
        )

        agent_state = self._to_agent_state(loop_state)
        stop = _REASON_MAP.get(exit_reason, StopReason.ERROR)

        return AgentResult(
            content=final_content,
            stop_reason=stop,
            state=agent_state,
            metadata={
                "turns": agent_state.turn_count,
                "tools_called": agent_state.tools_called,
                "memories_used": agent_state.memories_used,
                "exit_reason": exit_reason.value,
            },
        )

    async def run_stream(
        self,
        user_message: str,
        system_prompt: str = None,
        context_messages: List[Dict] = None,
        session_id: str = None,
        user_id: str = None,
        project_id: str = None,
        loop_out: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[LoopEvent, None]:
        self.user_id = user_id
        self.session_id = session_id
        self._project_id = project_id
        messages = list(context_messages or [])
        messages.append({"role": "user", "content": user_message})

        memories = []
        if self.memory and user_id:
            try:
                memories = await self.memory.retrieve(
                    user_id=user_id,
                    query=user_message,
                    session_id=session_id,
                    project_id=project_id,
                    top_k=5,
                )
            except Exception as e:
                logger.warning(f"Memory retrieval failed: {e}")

        if not system_prompt:
            system_prompt = self._build_system_prompt(memories)

        citations = build_citations(memories[:5]) if memories else []
        loop_state = LoopState(
            messages=messages,
            system_prompt=system_prompt,
            memory_citations=citations,
            memories_used=citations_to_legacy_strings(citations),
        )

        async for event in query_loop(
            self.llm,
            loop_state,
            tool_registry=self.tools,
            context_compressor=self.context,
            max_turns=self.max_turns,
            user_id=user_id,
            session_id=session_id,
            loop_out=loop_out,
        ):
            yield event

    def _to_agent_state(self, loop_state: LoopState) -> AgentState:
        return AgentState(
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

    def _build_system_prompt(self, memories: List = None) -> str:
        assembler = get_prompt_assembler()
        environment_info = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id or "current",
        }
        memory_index = None
        if memories:
            memory_index = "相关记忆：\n"
            for mem in memories:
                if isinstance(mem, dict):
                    memory_index += f"- {mem.get('content', '')}\n"
        return assembler.assemble(
            environment_info=environment_info,
            memory_index=memory_index,
        )
