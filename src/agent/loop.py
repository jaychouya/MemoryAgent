"""
Agent Loop - Core execution engine for MemoryAI.

Implements Claude Code's Tool-Use Loop pattern:
- Simple while(true) loop
- Trust model's reasoning (no explicit Thought steps)
- Native tool_use/end_turn signals
- Minimal application framework

This is the "brain" of the Agent that coordinates:
1. Context compression
2. LLM API calls
3. Tool execution orchestration
4. Termination decisions
"""

import logging
from typing import List, Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from datetime import datetime
import json

from src.agent.prompts.assembler import get_prompt_assembler
from src.agent.context import ContextCompressor

logger = logging.getLogger(__name__)


class StopReason(str, Enum):
    """Why the agent loop stopped."""
    END_TURN = "end_turn"          # Model decided it's done
    MAX_TURNS = "max_turns"        # Hit turn limit
    ERROR = "error"                # Unrecoverable error
    USER_ABORT = "user_abort"      # User cancelled


@dataclass
class AgentState:
    """Mutable state for the agent loop."""
    messages: List[Dict[str, Any]] = field(default_factory=list)
    turn_count: int = 0
    tokens_used: int = 0
    tools_called: List[str] = field(default_factory=list)
    memories_used: List[str] = field(default_factory=list)
    is_plan_mode: bool = False


@dataclass
class AgentResult:
    """Final result from the agent loop."""
    content: str
    stop_reason: StopReason
    state: AgentState
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentLoop:
    """
    Core agent execution loop.
    
    Follows Claude Code's Tool-Use Loop pattern:
    ```
    while True:
        1. Compress context (5-step strategy)
        2. Call LLM API
        3. If end_turn → break
        4. Execute tool calls
        5. Update state → continue
    ```
    
    Key design principles:
    - Trust model's reasoning (Extended Thinking handles it)
    - Use native tool_use/end_turn signals
    - Keep framework minimal
    """
    
    def __init__(
        self,
        llm_service,
        tool_registry=None,
        memory_manager=None,
        context_manager=None,
        max_turns: int = 50
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
        user_id: str = None
    ) -> AgentResult:
        """
        Run the agent loop until completion.
        
        Args:
            user_message: User's input message
            system_prompt: System prompt (will be assembled if not provided)
            context_messages: Previous conversation messages
            session_id: Current session ID
            user_id: Current user ID
            
        Returns:
            AgentResult with final response
        """
        # 保存用户上下文
        self.user_id = user_id
        self.session_id = session_id
        
        state = AgentState(
            messages=context_messages or []
        )
        
        # Add user message
        state.messages.append({
            "role": "user",
            "content": user_message
        })
        
        # Retrieve relevant memories if available
        memories = []
        if self.memory and user_id:
            try:
                memories = await self.memory.retrieve(
                    user_id=user_id,
                    query=user_message,
                    session_id=session_id,
                    top_k=5
                )
                state.memories_used = [m.get("content", "") for m in memories[:3] if isinstance(m, dict)]
            except Exception as e:
                logger.warning(f"Memory retrieval failed: {e}")
        
        # Build system prompt with memories
        if not system_prompt:
            system_prompt = self._build_system_prompt(memories)
        
        # Main loop
        while state.turn_count < self.max_turns:
            state.turn_count += 1
            logger.info(f"Agent turn {state.turn_count}")
            
            # Step 1: Compress context if needed
            if self.context:
                state.messages = await self.context.compress(state.messages)
            
            # Step 2: Call LLM
            try:
                response = await self._call_llm(
                    messages=state.messages,
                    system_prompt=system_prompt,
                    tools=self.tools.get_function_schemas() if self.tools else None
                )
            except Exception as e:
                logger.error(f"LLM call failed: {e}")
                return AgentResult(
                    content=f"抱歉，AI服务出现错误: {str(e)}",
                    stop_reason=StopReason.ERROR,
                    state=state
                )
            
            # Step 3: Check stop reason
            if response.get("stop_reason") == "end_turn":
                # Model is done - return final content
                return AgentResult(
                    content=response.get("content", ""),
                    stop_reason=StopReason.END_TURN,
                    state=state,
                    metadata={
                        "turns": state.turn_count,
                        "tools_called": state.tools_called,
                        "memories_used": state.memories_used
                    }
                )
            
            # Step 4: Handle tool calls
            tool_calls = response.get("tool_calls", [])
            if tool_calls:
                # Add assistant message with tool calls
                state.messages.append({
                    "role": "assistant",
                    "content": response.get("content", ""),
                    "tool_calls": tool_calls
                })
                
                # Execute tools
                tool_results = await self._execute_tools(tool_calls)
                
                # Add tool results to messages
                for result in tool_results:
                    state.messages.append({
                        "role": "tool",
                        "tool_call_id": result.get("tool_call_id"),
                        "content": result.get("content", "")
                    })
                    state.tools_called.append(result.get("tool_name", "unknown"))
                
                # Continue loop
                continue
            
            # No tool calls and not end_turn - treat as end_turn
            return AgentResult(
                content=response.get("content", ""),
                stop_reason=StopReason.END_TURN,
                state=state
            )
        
        # Hit max turns
        return AgentResult(
            content="抱歉，我已经达到了最大思考轮次。请尝试简化您的问题。",
            stop_reason=StopReason.MAX_TURNS,
            state=state
        )
    
    async def _call_llm(
        self,
        messages: List[Dict],
        system_prompt: str,
        tools: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Call the LLM API.
        
        Returns:
            Dict with 'content', 'stop_reason', and optional 'tool_calls'
        """
        # Prepare messages with system prompt
        full_messages = [{"role": "system", "content": system_prompt}] + messages
        
        # Call LLM
        response = await self.llm.generate_response(
            messages=full_messages,
            tools=tools
        )
        
        return response
    
    async def _execute_tools(self, tool_calls: List[Dict]) -> List[Dict]:
        """
        Execute tool calls with error handling.
        
        Args:
            tool_calls: List of tool call requests
            
        Returns:
            List of tool results
        """
        if not self.tools:
            return [{
                "tool_call_id": tc.get("id"),
                "tool_name": tc.get("function", {}).get("name"),
                "content": "错误：工具系统未初始化"
            } for tc in tool_calls]
        
        results = []
        
        calls = []
        for tc in tool_calls:
            func = tc.get("function", {})
            arguments = func.get("arguments", {})
            
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except:
                    arguments = {}
            
            # 注入用户上下文到工具参数
            if self.user_id:
                arguments["user_id"] = self.user_id
            if self.session_id:
                arguments["session_id"] = self.session_id
            
            calls.append({
                "tool": func.get("name"),
                "params": arguments,
                "tool_call_id": tc.get("id")
            })
        
        try:
            tool_results = await self.tools.execute_parallel(calls)
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return [{
                "tool_call_id": call["tool_call_id"],
                "tool_name": call["tool"],
                "content": f"工具执行失败: {str(e)}"
            } for call in calls]
        
        for call, result in zip(calls, tool_results):
            if result.success:
                content = result.content
            else:
                content = f"工具 '{call['tool']}' 执行失败: {result.error}"
                logger.warning(f"Tool {call['tool']} failed: {result.error}")
            
            results.append({
                "tool_call_id": call["tool_call_id"],
                "tool_name": call["tool"],
                "content": content
            })
        
        return results
    
    def _build_system_prompt(self, memories: List = None) -> str:
        """
        Build system prompt with memories using the PromptAssembler.
        
        Follows Claude Code's dynamic assembly pattern:
        - Static sections (cached)
        - Cache boundary
        - Dynamic sections (environment, memories)
        """
        assembler = get_prompt_assembler()
        
        environment_info = {
            "timestamp": datetime.now().isoformat(),
            "session_id": "current"
        }
        
        memory_index = None
        if memories:
            memory_index = "相关记忆：\n"
            for mem in memories:
                if isinstance(mem, dict):
                    memory_index += f"- {mem.get('content', '')}\n"
                else:
                    memory_index += f"- {mem}\n"
        
        return assembler.assemble(
            environment_info=environment_info,
            memory_index=memory_index
        )
