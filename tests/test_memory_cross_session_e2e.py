"""E2E: store preference in session A, recall in session B for same user."""
import pytest
import tempfile
import shutil
from pathlib import Path

from src.memory.manager import MemoryManager


@pytest.mark.asyncio
async def test_cross_session_recall_same_user():
    tmp = tempfile.mkdtemp()
    try:
        mgr = MemoryManager(storage_dir=str(Path(tmp) / "memories"))
        stored = await mgr.store_user_preference(
            "用户喜欢 Python，讨厌 Java",
            user_id="golden_user"
        )
        assert stored is not None

        results = await mgr.retrieve(
            query="写排序函数用什么语言",
            user_id="golden_user",
            top_k=5,
        )
        assert len(results) >= 1
        contents = " ".join(r.get("content", "") for r in results)
        assert "Python" in contents
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@pytest.mark.asyncio
async def test_cross_session_isolates_users():
    tmp = tempfile.mkdtemp()
    try:
        mgr = MemoryManager(storage_dir=str(Path(tmp) / "memories"))
        await mgr.store_user_preference("用户A喜欢Python", user_id="user_a")
        await mgr.store_user_preference("用户B喜欢Java", user_id="user_b")

        results_a = await mgr.retrieve(query="用户A Python", user_id="user_a", top_k=5)
        results_b = await mgr.retrieve(query="用户B Java", user_id="user_b", top_k=5)

        text_a = " ".join(r.get("content", "") for r in results_a)
        text_b = " ".join(r.get("content", "") for r in results_b)

        assert "Python" in text_a
        assert "Java" in text_b
        assert "Java" not in text_a
        assert "Python" not in text_b
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
