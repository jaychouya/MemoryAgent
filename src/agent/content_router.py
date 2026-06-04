"""Headroom-inspired content-type routing for tool/context compression."""

import json
import re
from enum import Enum
from typing import Any, Dict, List, Tuple


class ContentKind(str, Enum):
    JSON = "json"
    CODE = "code"
    TEXT = "text"


def detect_content_kind(text: str) -> ContentKind:
    s = (text or "").strip()
    if not s:
        return ContentKind.TEXT
    if s.startswith("{") or s.startswith("["):
        try:
            json.loads(s)
            return ContentKind.JSON
        except json.JSONDecodeError:
            pass
    if re.search(r"^\s*(def |class |import |function |const |#include)", s, re.M):
        return ContentKind.CODE
    if "```" in s:
        return ContentKind.CODE
    return ContentKind.TEXT


def _crush_json_value(val: Any, depth: int = 0, max_depth: int = 4) -> Any:
    if depth > max_depth:
        return "…"
    if isinstance(val, list):
        if len(val) == 0:
            return []
        sample = [_crush_json_value(val[0], depth + 1, max_depth)]
        if len(val) > 1:
            return sample + [f"…+{len(val) - 1} more items"]
        return sample
    if isinstance(val, dict):
        out = {}
        for i, (k, v) in enumerate(val.items()):
            if i >= 12:
                out["…"] = f"+{len(val) - 12} keys"
                break
            out[k] = _crush_json_value(v, depth + 1, max_depth)
        return out
    if isinstance(val, str) and len(val) > 200:
        return val[:200] + "…"
    return val


def compress_json_skeleton(text: str, max_chars: int = 4000) -> str:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return text[:max_chars]
    crushed = _crush_json_value(data)
    out = json.dumps(crushed, ensure_ascii=False, indent=0)
    if len(out) > max_chars:
        return out[: max_chars - 20] + '\n…[json truncated]'
    return out


def compress_code_skeleton(text: str, max_lines: int = 40, max_chars: int = 4000) -> str:
    lines = text.splitlines()
    total = len(lines)
    if total <= max_lines and len(text) <= max_chars:
        return text
    head = lines[:max_lines]
    body = "\n".join(head)
    note = f"\n…[{total - max_lines} lines omitted — use memory_retrieve_blob with ref to load full file]"
    if total > max_lines:
        body += note
    return body[:max_chars]


def compress_text_preview(text: str, max_chars: int = 2048) -> str:
    if len(text) <= max_chars:
        return text
    half = max_chars // 2
    return text[:half] + f"\n\n…[{len(text) - max_chars} chars omitted]…\n\n" + text[-half:]


def compress_by_kind(text: str, kind: ContentKind, max_preview: int) -> Tuple[str, Dict[str, Any]]:
    if kind == ContentKind.JSON:
        preview = compress_json_skeleton(text, max_chars=max_preview)
    elif kind == ContentKind.CODE:
        preview = compress_code_skeleton(text, max_chars=max_preview)
    else:
        preview = compress_text_preview(text, max_chars=max_preview)
    ratio = 1.0 - (len(preview) / max(len(text), 1))
    return preview, {
        "kind": kind.value,
        "original_chars": len(text),
        "preview_chars": len(preview),
        "saved_ratio": round(max(0.0, ratio), 3),
    }
