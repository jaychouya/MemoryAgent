"""Derive user_id / project_id from workspace (zero-config for Cursor/Claude Code)."""

import os
import re
import subprocess
from typing import Optional, Tuple


def _sanitize(name: str) -> str:
    s = (name or "default").strip()
    s = re.sub(r"[^\w\-.]", "_", s, flags=re.UNICODE)
    return s[:64] or "default"


def _git_repo_basename(start_dir: str) -> Optional[str]:
    try:
        proc = subprocess.run(
            ["git", "-C", start_dir, "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return _sanitize(os.path.basename(proc.stdout.strip()))
    except (OSError, subprocess.SubprocessError):
        pass
    return None


def get_workspace_dir() -> str:
    for key in (
        "MEMORYAGENT_WORKSPACE_DIR",
        "CURSOR_PROJECT_DIR",
        "CLAUDE_PROJECT_DIR",
        "VSCODE_CWD",
    ):
        val = os.environ.get(key, "").strip()
        if val and os.path.isdir(val):
            return os.path.abspath(val)
    return os.path.abspath(os.getcwd())


def default_user_id() -> str:
    explicit = os.environ.get("MEMORYAGENT_USER_ID", "").strip()
    if explicit:
        return _sanitize(explicit)
    return _sanitize(os.path.basename(get_workspace_dir()))


def default_project_id() -> str:
    explicit = os.environ.get("MEMORYAGENT_PROJECT_ID", "").strip()
    if explicit:
        return _sanitize(explicit)
    git_name = _git_repo_basename(get_workspace_dir())
    if git_name:
        return git_name
    return default_user_id()


def effective_chat_scope(
    user_id: str = "anonymous",
    project_id: Optional[str] = None,
) -> Tuple[str, Optional[str]]:
    """HTTP chat: map anonymous + empty project to workspace/git defaults."""
    uid_in = (user_id or "").strip()
    if uid_in in ("", "anonymous"):
        uid_in = ""
    pid_in = (project_id or "").strip()
    return resolve_scope(uid_in, pid_in)


def resolve_scope(
    user_id: str = "",
    project_id: str = "",
) -> Tuple[str, Optional[str]]:
    uid = (user_id or "").strip() or default_user_id()
    pid = (project_id or "").strip() or default_project_id()
    return uid, pid or None


def scope_summary() -> str:
    uid, pid = resolve_scope()
    ws = get_workspace_dir()
    return f"user_id={uid}, project_id={pid}, workspace={ws}"
