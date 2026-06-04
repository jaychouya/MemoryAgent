from src.memory.store_schema import validate_store_payload


def test_store_schema_valid():
    m, err = validate_store_payload("u1", "用户喜欢 Python 编程")
    assert err is None
    assert m.user_id == "u1"


def test_store_schema_rejects_short():
    m, err = validate_store_payload("u1", "短")
    assert m is None
    assert err


def test_store_schema_rejects_bad_type():
    m, err = validate_store_payload("u1", "用户喜欢 Python", memory_type="invalid")
    assert m is None
