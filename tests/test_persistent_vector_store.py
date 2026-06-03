import tempfile
import shutil
from pathlib import Path

import pytest

from src.memory.persistent_vector import PersistentVectorStore


@pytest.fixture
def tmp_db():
    tmp = tempfile.mkdtemp()
    db = str(Path(tmp) / "index.db")
    yield db
    shutil.rmtree(tmp, ignore_errors=True)


def test_upsert_and_reload(tmp_db):
    store1 = PersistentVectorStore(tmp_db)
    store1.upsert("mem1", "用户喜欢 Python", user_id="u1", memory_type="user")
    assert store1.memory_store.size() == 1

    store2 = PersistentVectorStore(tmp_db)
    assert store2.memory_store.size() == 1
    doc = store2.memory_store.get("mem1")
    assert doc is not None
    assert "Python" in doc["text"]


def test_delete_sync(tmp_db):
    store = PersistentVectorStore(tmp_db)
    store.upsert("mem1", "test content", user_id="u1")
    store.delete("mem1")
    assert store.memory_store.size() == 0
