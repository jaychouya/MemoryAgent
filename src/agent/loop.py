"""
Agent Loop — delegates to queryLoop (Claude Code-style main loop).
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from src.agent.prompts.assembler import get_prompt_assembler
from src.agent.context import ContextCompressor
from src.agent.query_loop import execute_query_loop, query_loop, LoopEvent, LoopEventType
from src.agent.loop_state import LoopState, LoopExitReason
from src.memory.citations import citations_to_legacy_strings
from src.memory.recall_bundle import recall_for_prompt
from src.memory.inject import format_mandatory_memory_block
from src.agent.prompts.scene import detect_scene
from src.backend.chat_utils import build_user_message_content

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

    def _append_user_message(
        self,
        messages: List[Dict],
        user_message: str,
        attachments: Optional[List[Dict]] = None,
    ) -> str:
        content, att_meta = build_user_message_content(user_message, attachments)
        user_msg: Dict[str, Any] = {
            "role": "user",
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }
        if att_meta:
            user_msg["attachments"] = att_meta
        messages.append(user_msg)
        if isinstance(content, str):
            return content
        texts = [p.get("text", "") for p in content if isinstance(p, dict) and p.get("type") == "text"]
        if texts:
            return " ".join(texts)
        if att_meta:
            return f"用户上传了 {len(att_meta)} 个附件"
        return user_message

    async def run(
        self,
        user_message: str,
        system_prompt: str = None,
        context_messages: List[Dict] = None,
        session_id: str = None,
        user_id: str = None,
        project_id: str = None,
        attachments: Optional[List[Dict]] = None,
    ) -> AgentResult:
        self.user_id = user_id
        self.session_id = session_id
        self._project_id = project_id

        messages = list(context_messages or [])
        query_text = self._append_user_message(messages, user_message, attachments)

        memories, memory_citations, _health = await self._recall_for_turn(
            query_text, user_id, project_id=project_id,
        )

        if not system_prompt:
            system_prompt = self._build_system_prompt(memories, query_text)

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
        attachments: Optional[List[Dict]] = None,
    ) -> AsyncGenerator[LoopEvent, None]:
        self.user_id = user_id
        self.session_id = session_id
        self._project_id = project_id
        messages = list(context_messages or [])
        query_text = self._append_user_message(messages, user_message, attachments)

        memories, citations, health = await self._recall_for_turn(
            query_text, user_id, project_id=project_id,
        )

        if not system_prompt:
            system_prompt = self._build_system_prompt(memories, query_text)

        from src.agent.query_loop import LoopEvent, LoopEventType

        yield LoopEvent(
            LoopEventType.MEMORY_INJECTED,
            metadata={
                "citations": [c.to_dict() for c in citations],
                "count": len(citations),
                "health": health,
            },
        )
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

    async def _recall_for_turn(
        self,
        query_text: str,
        user_id: str,
        project_id: str = None,
        top_k: int = 5,
    ):
        return await recall_for_prompt(
            self.memory,
            query_text,
            user_id,
            project_id=project_id,
            session_id=self.session_id,
            top_k=top_k,
            fast=True,
        )

    def _build_system_prompt(self, memories: List = None, user_message: str = "") -> str:
        assembler = get_prompt_assembler()
        scene = detect_scene(user_message)
        environment_info = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id or "current",
        }
        memory_index = format_mandatory_memory_block(memories or [])
        return assembler.assemble(
            environment_info=environment_info,
            memory_index=memory_index,
            scene=scene,
        )
