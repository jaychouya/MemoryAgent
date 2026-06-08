from src.memory.store_schema import validate_store_payload


def test_store_schema_valid():
    m, err = validate_store_payload("u1", "用户喜欢 Python 编程")
    assert err is None
    assert m.user_id == "u1"


def test_store_schema_accepts_provenance_and_supersedes():
    m, err = validate_store_payload(
        "u1",
        "用户现在喜欢 Rust 编程",
        supersedes="u1_user_old",
        source_session_id="session-1",
        source_turn=3,
        source_quote="我现在喜欢 Rust",
    )
    assert err is None
    assert m.supersedes == "u1_user_old"
    assert m.source_session_id == "session-1"
    assert m.source_turn == 3
    assert m.source_quote == "我现在喜欢 Rust"


def test_store_schema_rejects_short():
    m, err = validate_store_payload("u1", "短")
    assert m is None
    assert err


def test_store_schema_rejects_bad_type():
    m, err = validate_store_payload("u1", "用户喜欢 Python", memory_type="invalid")
    assert m is None
