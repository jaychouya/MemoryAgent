import pytest

from src.memory.eval import get_last_report, load_golden_cases, GOLDEN_PATH


def test_golden_fixture_loads():
    data = load_golden_cases(GOLDEN_PATH)
    assert data["user_id"] == "eval_user"
    assert len(data["cases"]) >= 10


@pytest.mark.asyncio
async def test_get_last_report_after_eval():
    import tempfile
    import shutil
    from pathlib import Path
    from src.memory.manager import MemoryManager
    from src.memory.eval import run_recall_eval

    tmp = tempfile.mkdtemp()
    try:
        mgr = MemoryManager(storage_dir=str(Path(tmp) / "memories"))
        await run_recall_eval(mgr, fixture_path=GOLDEN_PATH)
        report = get_last_report()
        assert report is not None
        assert report.recall_at_5 >= 0.9
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
