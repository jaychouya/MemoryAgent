"""Tool execution with parallel read / serial write and missing tool_result repair."""

import json
import logging
from typing import Any, Dict, List, Optional

from src.agent.tools.registry import ToolRegistry
from src.agent.tools.base import ToolResult

logger = logging.getLogger(__name__)


def parse_tool_calls(raw_calls: List[Dict]) -> List[Dict]:
    calls = []
    for tc in raw_calls:
        func = tc.get("function", {})
        arguments = func.get("arguments", {})
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                arguments = {}
        calls.append({
            "tool": func.get("name"),
            "params": arguments,
            "tool_call_id": tc.get("id"),
        })
    return calls


def inject_context(calls: List[Dict], user_id: str = None, session_id: str = None) -> List[Dict]:
    out = []
    for call in calls:
        params = {**call["params"]}
        if user_id:
            params["user_id"] = user_id
        if session_id:
            params["session_id"] = session_id
        out.append({**call, "params": params})
    return out


def build_tool_result_messages(
    tool_calls: List[Dict],
    results: List[Dict],
) -> List[Dict[str, Any]]:
    """Ensure every tool_use has a paired tool_result (yieldMissingToolResultBlocks)."""
    by_id = {r["tool_call_id"]: r for r in results if r.get("tool_call_id")}
    messages = []
    for tc in tool_calls:
        tid = tc.get("id")
        if not tid:
            continue
        if tid in by_id:
            r = by_id[tid]
            content = r.get("content", "")
            if r.get("is_error"):
                content = f"[工具错误] {content}"
        else:
            content = "[工具未执行：未收到执行结果，已合成错误占位以便继续对话]"
            r = {"is_error": True}
        messages.append({
            "role": "tool",
            "tool_call_id": tid,
            "content": content,
        })
    return messages


class ToolCallExecutor:
    """Runs tool_use blocks; read-only tools in parallel, writes serially."""

    def __init__(self, registry: Optional[ToolRegistry]):
        self.registry = registry

    async def execute(
        self,
        tool_calls: List[Dict],
        user_id: str = None,
        session_id: str = None,
    ) -> List[Dict]:
        if not self.registry:
            return [
                {
                    "tool_call_id": tc.get("id"),
                    "tool_name": tc.get("function", {}).get("name"),
                    "content": "错误：工具系统未初始化",
                    "is_error": True,
                }
                for tc in tool_calls
            ]

        calls = inject_context(parse_tool_calls(tool_calls), user_id, session_id)
        try:
            tool_results: List[ToolResult] = await self.registry.execute_parallel(calls)
        except Exception as e:
            logger.error(f"Tool batch failed: {e}")
            return [
                {
                    "tool_call_id": c["tool_call_id"],
                    "tool_name": c["tool"],
                    "content": f"工具执行失败: {e}",
                    "is_error": True,
                }
                for c in calls
            ]

        results = []
        for call, result in zip(calls, tool_results):
            if isinstance(result, Exception):
                results.append({
                    "tool_call_id": call["tool_call_id"],
                    "tool_name": call["tool"],
                    "content": str(result),
                    "is_error": True,
                })
                continue
            if result.success:
                content = result.content
                is_error = False
            else:
                content = result.error or "未知错误"
                is_error = True
            results.append({
                "tool_call_id": call["tool_call_id"],
                "tool_name": call["tool"],
                "content": content if isinstance(content, str) else str(content),
                "is_error": is_error,
            })
        return results


class StreamingToolExecutor(ToolCallExecutor):
    """
    Schedule each tool as soon as its tool_use block is known.
    With non-streaming LLM, schedule_all fires every task immediately.
    """

    def __init__(self, registry: Optional[ToolRegistry]):
        super().__init__(registry)
        self._tasks: Dict[str, Any] = {}

    def schedule(self, tool_call: Dict, user_id: str = None, session_id: str = None):
        calls = inject_context(parse_tool_calls([tool_call]), user_id, session_id)
        if not calls:
            return
        call = calls[0]
        tid = call["tool_call_id"]
        if tid in self._tasks:
            return

        async def _run():
            results = await ToolCallExecutor.execute(
                self, [tool_call], user_id, session_id
            )
            return results[0] if results else {
                "tool_call_id": tid,
                "tool_name": call["tool"],
                "content": "工具无返回",
                "is_error": True,
            }

        import asyncio
        self._tasks[tid] = asyncio.create_task(_run())

    def schedule_all(self, tool_calls: List[Dict], user_id: str = None, session_id: str = None):
        for tc in tool_calls:
            self.schedule(tc, user_id, session_id)

    async def collect(self, tool_calls: List[Dict]) -> List[Dict]:
        import asyncio
        if not self._tasks:
            return await self.execute(tool_calls, user_id=None, session_id=None)

        ordered = []
        for tc in tool_calls:
            tid = tc.get("id")
            if tid and tid in self._tasks:
                try:
                    ordered.append(await self._tasks[tid])
                except Exception as e:
                    ordered.append({
                        "tool_call_id": tid,
                        "tool_name": tc.get("function", {}).get("name"),
                        "content": str(e),
                        "is_error": True,
                    })
        self._tasks.clear()
        return ordered
