"""MCP helpers for CCR blob retrieve."""

from typing import Any, Dict

from src.agent.ccr_store import retrieve_blob


async def retrieve_blob_tool(ref_id: str, storage_dir: str) -> Dict[str, Any]:
    content = retrieve_blob(ref_id, storage_dir)
    if content is None:
        return {"found": False, "ref_id": ref_id, "content": ""}
    return {
        "found": True,
        "ref_id": ref_id,
        "chars": len(content),
        "content": content,
    }
