import json
import tempfile
import shutil

from src.agent.content_router import (
    compress_json_skeleton,
    detect_content_kind,
    ContentKind,
)
from src.agent.ccr_store import compress_with_ccr, retrieve_blob, store_blob


def test_detect_json():
    assert detect_content_kind('[{"a":1},{"a":2}]') == ContentKind.JSON


def test_json_skeleton_shrinks():
    data = [{"id": i, "text": "x" * 500} for i in range(50)]
    raw = json.dumps(data)
    out = compress_json_skeleton(raw, max_chars=3000)
    assert len(out) < len(raw)
    assert "more items" in out or "…" in out


def test_ccr_roundtrip():
    tmp = tempfile.mkdtemp()
    try:
        big = "line\n" * 5000
        preview, ref, stats = compress_with_ccr(big, tmp, 1000, 500)
        assert stats["offloaded"]
        assert ref and ref.startswith("ccr_")
        assert len(preview) < len(big)
        full = retrieve_blob(ref, tmp)
        assert full == big
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
