import os
import tempfile
from unittest.mock import patch

from src.mcp_server.workspace import (
    default_project_id,
    default_user_id,
    resolve_scope,
)


def test_default_user_from_workspace_basename():
    with tempfile.TemporaryDirectory(prefix="My Cool App_") as tmp:
        ws = os.path.join(tmp, "My Cool App")
        os.makedirs(ws)
        with patch.dict(os.environ, {"MEMORYAGENT_WORKSPACE_DIR": ws}, clear=False):
            assert default_user_id() == "My_Cool_App"
            assert default_project_id() == "My_Cool_App"


def test_explicit_override():
    with patch.dict(
        os.environ,
        {
            "MEMORYAGENT_WORKSPACE_DIR": "/tmp/foo",
            "MEMORYAGENT_USER_ID": "team-a",
            "MEMORYAGENT_PROJECT_ID": "repo-b",
        },
        clear=False,
    ):
        uid, pid = resolve_scope("", "")
        assert uid == "team-a"
        assert pid == "repo-b"


def test_resolve_scope_pass_through():
    uid, pid = resolve_scope("custom", "proj")
    assert uid == "custom"
    assert pid == "proj"


def test_git_repo_project_id(monkeypatch):
    import subprocess
    from src.mcp_server import workspace as ws

    with patch.dict(os.environ, {"MEMORYAGENT_WORKSPACE_DIR": "/tmp/ws"}, clear=False):
        monkeypatch.setattr(ws, "_git_repo_basename", lambda _: "my_repo")
        assert ws.default_project_id() == "my_repo"


def test_effective_chat_scope_anonymous():
    from src.mcp_server.workspace import effective_chat_scope

    with patch.dict(os.environ, {"MEMORYAGENT_USER_ID": "team-x"}, clear=False):
        uid, pid = effective_chat_scope("anonymous", None)
        assert uid == "team-x"
