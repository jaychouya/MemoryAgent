import pytest

from src.mcp_server.tools import delete_memory, store_memory, update_memory


@pytest.mark.asyncio
async def test_update_memory_rejects_wrong_user(tmp_path):
    storage = str(tmp_path / "memories")
    stored = await store_memory(
        "u1",
        "用户喜欢 Python 编程",
        storage_dir=storage,
    )

    result = await update_memory(
        stored["memory_id"],
        "u2",
        content="用户喜欢 Rust 编程",
        storage_dir=storage,
    )

    assert result["updated"] is False
    assert result["reason"] == "forbidden"


@pytest.mark.asyncio
async def test_delete_memory_rejects_wrong_user(tmp_path):
    storage = str(tmp_path / "memories")
    stored = await store_memory(
        "u1",
        "用户喜欢 Python 编程",
        storage_dir=storage,
    )

    result = await delete_memory(stored["memory_id"], "u2", storage_dir=storage)

    assert result["deleted"] is False
    assert result["reason"] == "forbidden"


@pytest.mark.asyncio
async def test_update_memory_rejects_prefix_collision_user(tmp_path):
    storage = str(tmp_path / "memories")
    stored = await store_memory(
        "user_a",
        "用户喜欢 Python 编程",
        storage_dir=storage,
    )

    result = await update_memory(
        stored["memory_id"],
        "user",
        content="用户喜欢 Rust 编程",
        storage_dir=storage,
    )

    assert result["updated"] is False
    assert result["reason"] == "forbidden"
