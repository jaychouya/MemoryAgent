import tempfile
import shutil
import uuid
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from src.memory.manager import MemoryManager
from src.memory.write_pipeline import persist_turn_memories
from src.utils.config import settings


@pytest.mark.asyncio
async def test_write_pipeline_llm_extract(monkeypatch):
    monkeypatch.setattr(settings, "MEMORY_EXTRACT_LLM_MIN_CHARS", 0)
    tmp = tempfile.mkdtemp()
    try:
        mgr = MemoryManager(storage_dir=str(Path(tmp) / "memories"))
        llm = AsyncMock()
        llm.client = object()
        llm.generate_response = AsyncMock(return_value={
            "content": '[{"content": "用户偏好使用 TypeScript", "type": "user"}]',
        })
        mgr.llm = llm
        tag = uuid.uuid4().hex[:6]
        ids = await persist_turn_memories(
            mgr,
            "帮我写个组件",
            "好的",
            user_id=f"wp_{tag}",
        )
        assert len(ids) >= 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
