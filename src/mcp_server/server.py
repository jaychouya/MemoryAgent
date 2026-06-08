"""MCP stdio server — run: python -m src.mcp_server.server"""

import os
import sys

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

_STORAGE = os.environ.get("MEMORYAGENT_STORAGE_DIR", "memories")


def _run_fastmcp():
    from mcp.server.fastmcp import FastMCP
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

    try:
        mcp = FastMCP("memoryagent-sidecar", instructions=get_mcp_instructions())
    except TypeError:
        mcp = FastMCP("memoryagent-sidecar")

    @mcp.tool()
    async def memory_recall(
        query: str,
        user_id: str = "",
        limit: int = 5,
        project_id: str = "",
    ) -> str:
        uid, pid = resolve_scope(user_id, project_id)
        return format_tool_json(
            await recall_memories(
                uid, query, limit=limit, storage_dir=_STORAGE,
                project_id=pid,
            )
        )

    @mcp.tool()
    async def memory_store(
        content: str,
        user_id: str = "",
        memory_type: str = "user",
        description: str = "",
        project_id: str = "",
        supersedes: str = "",
        source_session_id: str = "",
        source_turn: int = 0,
        source_quote: str = "",
    ) -> str:
        uid, pid = resolve_scope(user_id, project_id)
        return format_tool_json(
            await store_memory(
                user_id=uid,
                content=content,
                memory_type=memory_type,
                description=description or None,
                storage_dir=_STORAGE,
                project_id=pid,
                supersedes=supersedes or None,
                source_session_id=source_session_id or None,
                source_turn=source_turn or None,
                source_quote=source_quote or None,
            )
        )

    @mcp.tool()
    async def memory_update(
        memory_id: str,
        user_id: str = "",
        content: str = "",
        description: str = "",
        project_id: str = "",
    ) -> str:
        uid, _ = resolve_scope(user_id, project_id)
        return format_tool_json(
            await update_memory(
                memory_id=memory_id,
                user_id=uid,
                content=content or None,
                description=description or None,
                storage_dir=_STORAGE,
            )
        )

    @mcp.tool()
    async def memory_delete(memory_id: str, user_id: str = "", project_id: str = "") -> str:
        uid, _ = resolve_scope(user_id, project_id)
        return format_tool_json(
            await delete_memory(memory_id, uid, storage_dir=_STORAGE)
        )

    @mcp.tool()
    async def memory_list(
        user_id: str = "",
        limit: int = 20,
        project_id: str = "",
        memory_type: str = "",
    ) -> str:
        uid, pid = resolve_scope(user_id, project_id)
        return format_tool_json(
            await list_memories(
                user_id=uid,
                limit=limit,
                storage_dir=_STORAGE,
                project_id=pid,
                memory_type=memory_type or None,
            )
        )

    @mcp.tool()
    async def memory_export(
        query: str = "",
        user_id: str = "",
        limit: int = 10,
        project_id: str = "",
    ) -> str:
        uid, pid = resolve_scope(user_id, project_id)
        return format_tool_json(
            await export_memories(
                user_id=uid,
                query=query or None,
                limit=limit,
                storage_dir=_STORAGE,
                project_id=pid,
            )
        )

    @mcp.tool()
    async def memory_retrieve_blob(ref_id: str) -> str:
        """Load full tool/log content by CCR ref (Headroom-style reversible compression)."""
        from src.mcp_server.blob_tools import retrieve_blob_tool

        return format_tool_json(await retrieve_blob_tool(ref_id, _STORAGE))

    mcp.run(transport="stdio")


def main():
    try:
        _run_fastmcp()
    except ImportError:
        from src.mcp_server.minimal_stdio import run_stdio_server
        run_stdio_server(_STORAGE)


if __name__ == "__main__":
    main()
