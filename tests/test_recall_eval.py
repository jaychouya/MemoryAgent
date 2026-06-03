import tempfile
import shutil
from pathlib import Path

import pytest

from src.memory.manager import MemoryManager
from src.memory.eval import run_recall_eval, GOLDEN_PATH


@pytest.mark.asyncio
async def test_recall_eval_meets_threshold():
    tmp = tempfile.mkdtemp()
    try:
        mgr = MemoryManager(storage_dir=str(Path(tmp) / "memories"))
        report = await run_recall_eval(mgr, fixture_path=GOLDEN_PATH, top_k=5)
        assert report.recall_at_5 >= 0.9
        assert len(report.cases) >= 10
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
