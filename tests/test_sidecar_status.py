"""Tests for workspace sidecar status."""

import json
import tempfile
from pathlib import Path

from src.memory.sidecar_status import (
    record_recall,
    record_store,
    read_status,
    status_file_path,
)


def test_status_file_under_memoryagent():
    with tempfile.TemporaryDirectory() as tmp:
        storage = str(Path(tmp) / ".memoryagent" / "memories")
        Path(storage).mkdir(parents=True)
        p = status_file_path(storage)
        assert p.name == "status.json"
        assert p.parent.name == ".memoryagent"


def test_record_recall_writes_notice():
    with tempfile.TemporaryDirectory() as tmp:
        storage = str(Path(tmp) / ".memoryagent" / "memories")
        Path(storage).mkdir(parents=True)
        notice = record_recall(
            storage,
            user_id="u1",
            query="python",
            count=2,
            health={"status": "ok"},
        )
        assert "2" in notice
        data = read_status(storage)
        assert data["last_recall"]["count"] == 2
        assert data["ide_notice"] == notice


def test_record_store_success():
    with tempfile.TemporaryDirectory() as tmp:
        storage = str(Path(tmp) / ".memoryagent" / "memories")
        Path(storage).mkdir(parents=True)
        notice = record_store(
            storage,
            user_id="u1",
            memory_id="m1",
            memory_type="user",
            content="喜欢 Python",
            stored=True,
        )
        assert "已写入" in notice
        assert read_status(storage)["last_store"]["stored"] is True
