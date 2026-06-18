#!/usr/bin/env python3
"""30-second sidecar verification: store → recall golden preference."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys

GOLDEN_TEXT = "MemoryAgent 首胜测试：用户偏好使用 Python，讨厌 Java"
GOLDEN_QUERY = "用户编程语言偏好"


async def run_verify(storage_dir: str, user_id: str) -> int:
    from src.mcp_server.tools import recall_memories, store_memory

    os.environ.setdefault("MEMORYAGENT_STORAGE_DIR", storage_dir)

    stored = await store_memory(
        user_id=user_id,
        content=GOLDEN_TEXT,
        memory_type="user",
        description="首胜验证",
        storage_dir=storage_dir,
    )
    if stored.get("stored"):
        print(f"OK 写入 memory_id={stored.get('memory_id')}")
    else:
        reason = stored.get("reason", "")
        print(f"SKIP 写入跳过 ({reason})，继续召回测试")

    recalled = await recall_memories(
        user_id=user_id,
        query=GOLDEN_QUERY,
        limit=5,
        storage_dir=storage_dir,
    )
    count = recalled.get("count", 0)
    hits = [
        m.get("content", "")
        for m in recalled.get("memories", [])
        if "Python" in m.get("content", "") or "Java" in m.get("content", "")
    ]
    if count > 0 and hits:
        print(f"OK 召回 {count} 条，命中首胜记忆")
        notice = recalled.get("ide_notice", "")
        if notice:
            print(f"    {notice}")
        return 0

    health = recalled.get("recall_health") or {}
    hints = health.get("hints") or []
    print(f"FAIL 召回未命中 (count={count})")
    for h in hints[:3]:
        print(f"  · {h}")
    print("  · 确认 MCP 已重载；记忆目录:", storage_dir)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify MemoryAgent sidecar store/recall")
    parser.add_argument("--storage", default=os.environ.get("MEMORYAGENT_STORAGE_DIR", ""))
    parser.add_argument("--user-id", default=os.environ.get("MEMORYAGENT_USER_ID", "verify-user"))
    args = parser.parse_args()
    storage = args.storage.strip()
    if not storage:
        print("FAIL 需要 --storage 或 MEMORYAGENT_STORAGE_DIR")
        return 1
    return asyncio.run(run_verify(storage, args.user_id))


if __name__ == "__main__":
    sys.exit(main())
