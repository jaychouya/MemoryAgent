"""Workspace-visible sidecar status for IDE users (记→用→信)."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def _workspace_dir() -> str:
    for key in (
        "MEMORYAGENT_WORKSPACE_DIR",
        "CURSOR_PROJECT_DIR",
        "CLAUDE_PROJECT_DIR",
    ):
        val = os.environ.get(key, "").strip()
        if val and os.path.isdir(val):
            return os.path.abspath(val)
    return os.path.abspath(os.getcwd())


def status_file_path(storage_dir: str = "memories") -> Path:
    base = Path(storage_dir)
    if not base.is_absolute():
        base = Path.cwd() / base
    if base.name == "memories":
        return base.parent / "status.json"
    ws = Path(_workspace_dir()) / ".memoryagent" / "status.json"
    return ws


def _read_status(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def write_status(
    storage_dir: str,
    patch: Dict[str, Any],
) -> Path:
    path = status_file_path(storage_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = _read_status(path)
    data.update(patch)
    data["updated_at"] = datetime.now().isoformat()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def record_recall(
    storage_dir: str,
    *,
    user_id: str,
    query: str,
    count: int,
    health: Optional[Dict[str, Any]] = None,
) -> str:
    health = health or {}
    status = health.get("status", "ok")
    hints: List[str] = list(health.get("hints") or [])
    notice = _recall_notice(count, status, hints)
    write_status(
        storage_dir,
        {
            "last_recall": {
                "at": datetime.now().isoformat(),
                "user_id": user_id,
                "query": query[:200],
                "count": count,
                "status": status,
                "hints": hints,
            },
            "ide_notice": notice,
        },
    )
    return notice


def record_store(
    storage_dir: str,
    *,
    user_id: str,
    memory_id: str,
    memory_type: str,
    content: str,
    stored: bool,
    reason: str = "",
) -> str:
    if stored:
        notice = f"✓ 已写入记忆 [{memory_type}]：{content[:60]}"
    else:
        notice = f"✗ 记忆未写入：{reason or '未知原因'}"
    write_status(
        storage_dir,
        {
            "last_store": {
                "at": datetime.now().isoformat(),
                "user_id": user_id,
                "memory_id": memory_id,
                "memory_type": memory_type,
                "content": content[:200],
                "stored": stored,
                "reason": reason,
            },
            "ide_notice": notice,
        },
    )
    return notice


def record_update(
    storage_dir: str,
    *,
    user_id: str,
    memory_id: str,
    ok: bool,
) -> str:
    notice = f"✓ 已更正记忆 {memory_id[:12]}…" if ok else "✗ 记忆更正失败"
    write_status(
        storage_dir,
        {
            "last_update": {
                "at": datetime.now().isoformat(),
                "user_id": user_id,
                "memory_id": memory_id,
                "updated": ok,
            },
            "ide_notice": notice,
        },
    )
    return notice


def record_delete(
    storage_dir: str,
    *,
    user_id: str,
    memory_id: str,
    ok: bool,
) -> str:
    notice = f"✓ 已删除记忆 {memory_id[:12]}…" if ok else "✗ 记忆删除失败"
    write_status(
        storage_dir,
        {
            "last_delete": {
                "at": datetime.now().isoformat(),
                "user_id": user_id,
                "memory_id": memory_id,
                "deleted": ok,
            },
            "ide_notice": notice,
        },
    )
    return notice


def record_writes(
    storage_dir: str,
    *,
    user_id: str,
    stored: int,
    deleted: int,
) -> str:
    if stored == 0 and deleted == 0:
        return ""
    parts = []
    if stored:
        parts.append(f"沉淀 {stored} 条")
    if deleted:
        parts.append(f"删除 {deleted} 条")
    notice = f"✓ 对话后自动{'，'.join(parts)}"
    write_status(
        storage_dir,
        {
            "last_auto_write": {
                "at": datetime.now().isoformat(),
                "user_id": user_id,
                "stored": stored,
                "deleted": deleted,
            },
            "ide_notice": notice,
        },
    )
    return notice


def read_status(storage_dir: str = "memories") -> Dict[str, Any]:
    path = status_file_path(storage_dir)
    data = _read_status(path)
    if data:
        data["status_file"] = str(path)
    return data


def _recall_notice(count: int, status: str, hints: List[str]) -> str:
    if status == "empty_unexpected":
        tip = hints[0] if hints else "检查记忆面板或换更短关键词"
        return f"⚠ 召回异常（0 条）：{tip}"
    if count > 0:
        return f"✓ 已召回 {count} 条记忆"
    if status == "empty_no_corpus":
        return "ℹ 尚无长期记忆，可在对话中说明偏好"
    return "ℹ 本轮未命中记忆（可能问题与已有记忆无关）"
