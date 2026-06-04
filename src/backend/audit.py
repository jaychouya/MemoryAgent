import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

_AUDIT_PATH = Path(".memoryai/audit.jsonl")


def log_memory_event(
    action: str,
    user_id: str,
    memory_id: Optional[str] = None,
    detail: Optional[Dict[str, Any]] = None,
) -> None:
    _AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "at": datetime.now().isoformat(),
        "action": action,
        "user_id": user_id,
        "memory_id": memory_id,
        "detail": detail or {},
    }
    with _AUDIT_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
