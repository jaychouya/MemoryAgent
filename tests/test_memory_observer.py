import tempfile
import shutil
import uuid
from pathlib import Path

import pytest

from src.memory.manager import MemoryManager
from src.memory.observer import MemoryObserver
from src.memory.auto_write import extract_candidates
from src.memory.types import MemoryType


def test_extract_candidates():
    cands = extract_candidates("我喜欢 Python，讨厌 Java")
    assert len(cands) >= 1


def test_extract_candidates_stores_project_decision():
    cands = extract_candidates("本项目决定使用 SQLite FTS 做本地索引。")
    assert ("本项目决定使用 SQLite FTS 做本地索引", MemoryType.PROJECT) in cands


def test_extract_candidates_ignores_memory_meta_question():
    assert extract_candidates("你记住这个了吗？") == []


def test_extract_candidates_ignores_transient_greeting():
    assert extract_candidates("你好！") == []
    assert extract_candidates("谢谢") == []


def test_extract_candidates_remember_yields_single_memory():
    cands = extract_candidates("记住：我偏好代码直接、少解释、不要过度设计")
    assert len(cands) == 1
    assert cands[0][0] == "我偏好代码直接、少解释、不要过度设计"


@pytest.mark.asyncio
async def test_persist_turn_memories_no_triple_write_for_remember_phrase(tmp_path):
    from src.memory.write_pipeline import persist_turn_memories
    from unittest.mock import AsyncMock
    mgr = MemoryManager(storage_dir=str(tmp_path / "memories"))
    llm = AsyncMock()
    llm.client = object()
    llm.generate_response = AsyncMock(return_value={
        "content": '[{"content": "用户偏好代码直接、少解释、不要过度设计", "type": "user"}]',
    })
    mgr.llm = llm
    uid = f"dedupe_{uuid.uuid4().hex[:8]}"
    msg = "记住：我偏好代码直接、少解释、不要过度设计"
    outcome = await persist_turn_memories(mgr, msg, "好的", user_id=uid)
    assert len(outcome.stored) == 1
    assert outcome.stored[0]["content"] == "我偏好代码直接、少解释、不要过度设计"


@pytest.mark.asyncio
async def test_observer_stores_preference():
    tmp = tempfile.mkdtemp()
    try:
        mgr = MemoryManager(storage_dir=str(Path(tmp) / "memories"))
        obs = MemoryObserver(mgr)
        tag = uuid.uuid4().hex[:8]
        outcome = await obs.observe_turn(
            f"我喜欢 Kotlin 编程 {tag}",
            "好的记住了",
            user_id=f"obs_user_{tag}",
        )
        assert len(outcome.stored) >= 1
        results = await mgr.retrieve(query="Kotlin", user_id=f"obs_user_{tag}", top_k=5)
        text = " ".join(r.get("content", "") for r in results)
        assert "Kotlin" in text
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
