"""Sidecar onboarding health (记→用→信 checklist)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from src.memory.paths import default_storage_dir
from src.memory.sidecar_status import read_status


async def build_sidecar_health() -> Dict[str, Any]:
    from src.mcp_server.workspace import get_workspace_dir, resolve_scope
    from src.memory.service import get_shared_memory_manager
    from src.backend.config_manager import ConfigManager

    storage = default_storage_dir()
    user_id, project_id = resolve_scope()
    workspace = get_workspace_dir()
    status = read_status(storage)
    storage_path = Path(storage)
    memories_path = storage_path if storage_path.name == "memories" else storage_path / "memories"

    manager = get_shared_memory_manager()
    memory_count = await manager.count_memories(user_id, project_id)

    cfg = ConfigManager().load_config() or {}
    model_configured = bool((cfg.get("api_key") or "").strip())

    cursor_mcp = Path(workspace) / ".cursor" / "mcp.json"
    sidecar_rule = Path(workspace) / ".cursor" / "rules" / "memory-sidecar.mdc"
    status_file = (
        storage_path.parent / "status.json"
        if storage_path.name == "memories"
        else Path(workspace) / ".memoryagent" / "status.json"
    )

    checks: List[Dict[str, Any]] = [
        {
            "id": "storage",
            "ok": memories_path.exists(),
            "label": "记忆目录",
            "hint": "运行 bash scripts/install-sidecar.sh .",
        },
        {
            "id": "cursor_mcp",
            "ok": cursor_mcp.exists(),
            "label": "Cursor MCP 配置",
            "hint": "install-sidecar.sh 会写入 .cursor/mcp.json",
        },
        {
            "id": "cursor_rule",
            "ok": sidecar_rule.exists(),
            "label": "侧车规则",
            "hint": "重载 MCP 后 Agent 每轮会 recall",
        },
        {
            "id": "has_memories",
            "ok": memory_count > 0,
            "label": "已有记忆",
            "hint": "在对话中说「记住：…」或跑 verify-sidecar.sh",
        },
        {
            "id": "model",
            "ok": model_configured,
            "label": "Web 模型配置",
            "hint": "仅 Web 控制台需要；Cursor 侧车可跳过",
            "optional": True,
        },
    ]

    tips: List[str] = []
    if not cursor_mcp.exists():
        tips.append("主路径：在业务项目执行 install-sidecar.sh，然后在 Cursor 重载 MCP。")
    if memory_count == 0:
        tips.append("尚无记忆：说「记住我喜欢 Python」或运行 verify-sidecar.sh 完成首胜。")
    if status.get("ide_notice"):
        tips.append(f"最近侧车：{status['ide_notice']}")
    if not tips:
        tips.append("记→用→信：写入有 ide_notice；召回看消息标签；纠错说「记错了…」或到记忆管理编辑。")

    core_ok = all(c["ok"] for c in checks if not c.get("optional"))

    return {
        "scope": {
            "user_id": user_id,
            "project_id": project_id,
            "workspace": workspace,
            "storage_dir": str(storage_path),
        },
        "memory_count": memory_count,
        "status_file": str(status_file) if status_file.exists() else None,
        "sidecar_status": status,
        "checks": checks,
        "cursor_ready": core_ok,
        "web_ready": core_ok and model_configured,
        "tips": tips,
    }
