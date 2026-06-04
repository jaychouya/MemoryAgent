"""Stdio MCP JSON-RPC server (stdlib only, Python 3.9+)."""

import asyncio
import json
import sys
from typing import Any, Callable, Dict, List, Optional

from src.mcp_server.tools import (
    delete_memory,
    export_memories,
    format_tool_json,
    list_memories,
    recall_memories,
    store_memory,
    update_memory,
)
from src.mcp_server.workspace import resolve_scope
from src.mcp_server.instructions import get_mcp_instructions

TOOLS = [
    {
        "name": "memory_recall",
        "description": "Retrieve relevant memories. user_id/project_id optional (default from workspace dir name).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "user_id": {"type": "string", "default": ""},
                "limit": {"type": "integer", "default": 5},
                "project_id": {"type": "string", "default": ""},
            },
            "required": ["query"],
        },
    },
    {
        "name": "memory_store",
        "description": "Store durable memory. user_id/project_id optional (workspace defaults).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "content": {"type": "string"},
                "user_id": {"type": "string", "default": ""},
                "memory_type": {"type": "string", "default": "user"},
                "description": {"type": "string", "default": ""},
                "project_id": {"type": "string", "default": ""},
            },
            "required": ["content"],
        },
    },
    {
        "name": "memory_update",
        "description": "Update an existing memory by id.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "memory_id": {"type": "string"},
                "user_id": {"type": "string"},
                "content": {"type": "string", "default": ""},
                "description": {"type": "string", "default": ""},
            },
            "required": ["memory_id"],
        },
    },
    {
        "name": "memory_delete",
        "description": "Delete a memory by id.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "memory_id": {"type": "string"},
                "user_id": {"type": "string"},
            },
            "required": ["memory_id"],
        },
    },
    {
        "name": "memory_list",
        "description": "List memories for a user (optional project filter).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "limit": {"type": "integer", "default": 20},
                "project_id": {"type": "string", "default": ""},
                "memory_type": {"type": "string", "default": ""},
            },
            "required": [],
        },
    },
    {
        "name": "memory_export",
        "description": "Export memories for IDE context injection (sidecar v2).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "query": {"type": "string", "default": ""},
                "limit": {"type": "integer", "default": 10},
                "project_id": {"type": "string", "default": ""},
            },
            "required": [],
        },
    },
]

_HANDLERS: Dict[str, Callable] = {}


def _register_handlers(storage_dir: str):
    async def memory_recall(args: dict) -> str:
        uid, pid = resolve_scope(args.get("user_id", ""), args.get("project_id", ""))
        return format_tool_json(await recall_memories(
            uid, args["query"],
            limit=int(args.get("limit", 5)),
            storage_dir=storage_dir,
            project_id=pid,
        ))

    async def memory_store(args: dict) -> str:
        uid, pid = resolve_scope(args.get("user_id", ""), args.get("project_id", ""))
        return format_tool_json(await store_memory(
            user_id=uid,
            content=args["content"],
            memory_type=args.get("memory_type", "user"),
            description=args.get("description") or None,
            storage_dir=storage_dir,
            project_id=pid,
        ))

    async def memory_update(args: dict) -> str:
        uid, _ = resolve_scope(args.get("user_id", ""), args.get("project_id", ""))
        return format_tool_json(await update_memory(
            memory_id=args["memory_id"],
            user_id=uid,
            content=args.get("content") or None,
            description=args.get("description") or None,
            storage_dir=storage_dir,
        ))

    async def memory_delete(args: dict) -> str:
        uid, _ = resolve_scope(args.get("user_id", ""), args.get("project_id", ""))
        return format_tool_json(await delete_memory(
            args["memory_id"], uid, storage_dir=storage_dir
        ))

    async def memory_list(args: dict) -> str:
        uid, pid = resolve_scope(args.get("user_id", ""), args.get("project_id", ""))
        return format_tool_json(await list_memories(
            user_id=uid,
            limit=int(args.get("limit", 20)),
            storage_dir=storage_dir,
            project_id=pid,
            memory_type=args.get("memory_type") or None,
        ))

    async def memory_export(args: dict) -> str:
        uid, pid = resolve_scope(args.get("user_id", ""), args.get("project_id", ""))
        return format_tool_json(await export_memories(
            user_id=uid,
            query=args.get("query") or None,
            limit=int(args.get("limit", 10)),
            storage_dir=storage_dir,
            project_id=pid,
        ))

    _HANDLERS.update({
        "memory_recall": memory_recall,
        "memory_store": memory_store,
        "memory_update": memory_update,
        "memory_delete": memory_delete,
        "memory_list": memory_list,
        "memory_export": memory_export,
    })


def _send(msg: dict):
    body = json.dumps(msg, ensure_ascii=False).encode("utf-8")
    sys.stdout.buffer.write(f"Content-Length: {len(body)}\r\n\r\n".encode("ascii"))
    sys.stdout.buffer.write(body)
    sys.stdout.buffer.flush()


def _read_message() -> Optional[dict]:
    headers: Dict[str, str] = {}
    while True:
        line = sys.stdin.buffer.readline()
        if not line:
            return None
        decoded = line.decode("utf-8", errors="replace").strip()
        if decoded == "":
            break
        if ":" in decoded:
            k, v = decoded.split(":", 1)
            headers[k.strip().lower()] = v.strip()
    length = int(headers.get("content-length", "0"))
    if length <= 0:
        return None
    raw = sys.stdin.buffer.read(length)
    return json.loads(raw.decode("utf-8"))


async def _handle(msg: dict, storage_dir: str) -> Optional[dict]:
    method = msg.get("method")
    req_id = msg.get("id")
    params = msg.get("params") or {}

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "memoryagent-sidecar", "version": "0.2.0"},
                "instructions": get_mcp_instructions(),
            },
        }

    if method == "notifications/initialized":
        return None

    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}

    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments") or {}
        if name not in _HANDLERS:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Unknown tool: {name}"},
            }
        text = await _HANDLERS[name](args)
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [{"type": "text", "text": text}],
                "isError": False,
            },
        }

    if req_id is not None:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"},
        }
    return None


def run_stdio_server(storage_dir: str = "memories"):
    _register_handlers(storage_dir)
    while True:
        msg = _read_message()
        if msg is None:
            break
        resp = asyncio.run(_handle(msg, storage_dir))
        if resp is not None:
            _send(resp)
