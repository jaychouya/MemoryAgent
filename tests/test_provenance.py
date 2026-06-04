import json
import tempfile
import shutil
from pathlib import Path

import pytest

from src.memory.provenance import (
    append_l0_turn,
    load_l0_turn,
    pick_source_quote,
    l0_path,
)


def test_append_l0_and_load_turn():
    tmp = tempfile.mkdtemp()
    try:
        t1 = append_l0_turn(tmp, "u1", "s1", "我喜欢 Kotlin", "好的")
        t2 = append_l0_turn(tmp, "u1", "s1", "第二句", "收到")
        assert t1 == 1
        assert t2 == 2
        rel = str(l0_path(tmp, "u1", "s1").relative_to(Path(tmp)))
        rec = load_l0_turn(tmp, rel, 1)
        assert rec and "Kotlin" in rec["user"]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_pick_source_quote():
    q = pick_source_quote("我偏好用 Python 写后端", "用户偏好 Python")
    assert "Python" in q


@pytest.mark.asyncio
async def test_write_pipeline_provenance_metadata(monkeypatch):
    import uuid
    from unittest.mock import AsyncMock
    from src.memory.manager import MemoryManager
    from src.memory.write_pipeline import persist_turn_memories
    from src.utils.config import settings

    monkeypatch.setattr(settings, "MEMORY_EXTRACT_LLM_MIN_CHARS", 10_000)
    tmp = tempfile.mkdtemp()
    try:
        mgr = MemoryManager(storage_dir=str(Path(tmp) / "memories"))
        tag = uuid.uuid4().hex[:6]
        ids = await persist_turn_memories(
            mgr,
            "我讨厌使用 mock 数据库做测试",
            "明白了",
            user_id=f"pv_{tag}",
            session_id=f"sess_{tag}",
        )
        assert ids
        mem = await mgr.storage.retrieve(ids[0])
        assert mem.metadata.get("evidence_level") == "L1"
        assert mem.metadata.get("source_session_id") == f"sess_{tag}"
        assert mem.metadata.get("source_quote")
        assert mem.metadata.get("l0_path")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
