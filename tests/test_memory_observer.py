import tempfile
import shutil
from pathlib import Path

import pytest

from src.memory.manager import MemoryManager
from src.memory.observer import MemoryObserver, extract_candidates


def test_extract_candidates():
    cands = extract_candidates("我喜欢 Python，讨厌 Java")
    assert len(cands) >= 1


@pytest.mark.asyncio
async def test_observer_stores_preference():
    tmp = tempfile.mkdtemp()
    try:
        mgr = MemoryManager(storage_dir=str(Path(tmp) / "memories"))
        obs = MemoryObserver(mgr)
        ids = await obs.observe_turn(
            "我喜欢 Kotlin 编程",
            "好的记住了",
            user_id="obs_user",
        )
        assert len(ids) >= 1
        results = await mgr.retrieve(query="编程语言", user_id="obs_user", top_k=5)
        text = " ".join(r.get("content", "") for r in results)
        assert "Kotlin" in text
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
