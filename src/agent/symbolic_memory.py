"""Mermaid symbolic working memory — compact task topology for tool-heavy loops."""

SYMBOLIC_MARKER = "memoryagent-symbolic-v1"

import hashlib
import os
import re
from typing import Any, Dict, List, Tuple


def _tool_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for i, m in enumerate(messages):
        if m.get("role") == "tool":
            out.append({**m, "_idx": i})
    return out


def build_mermaid_task_graph(
    messages: List[Dict[str, Any]],
    file_storage_dir: str,
) -> Tuple[str, Dict[str, str]]:
    """
    Build flowchart from tool messages. Returns (mermaid_source, node_id -> detail_ref).
    """
    tools = _tool_messages(messages)
    if not tools:
        return "", {}

    os.makedirs(file_storage_dir, exist_ok=True)
    lines = ["flowchart TD"]
    node_refs: Dict[str, str] = {}
    prev_id = None

    for i, msg in enumerate(tools):
        content = str(msg.get("content", ""))
        name = "tool"
        if "tool_name" in msg:
            name = str(msg["tool_name"])
        else:
            m = re.search(r"\[工具[:\s]*([^\]]+)\]", content)
            if m:
                name = m.group(1).strip()[:32]
        label = re.sub(r"[^\w\-]", "_", name)[:24] or "tool"
        node_id = f"n{i + 1}"
        short = content[:80].replace("\n", " ").replace('"', "'")
        lines.append(f'  {node_id}["{label}: {short}..."]')

        if len(content) > 2048:
            fid = hashlib.md5(content.encode()).hexdigest()[:10]
            fpath = os.path.join(file_storage_dir, f"sym_{fid}.txt")
            if not os.path.exists(fpath):
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write(content)
            node_refs[node_id] = fpath

        if prev_id:
            lines.append(f"  {prev_id} --> {node_id}")
        prev_id = node_id

    return "\n".join(lines), node_refs


def format_symbolic_system_message(
    mermaid: str,
    node_refs: Dict[str, str],
) -> str:
    if not mermaid:
        return ""
    parts = [
        f"## 任务状态图（符号化工作记忆）",
        SYMBOLIC_MARKER,
        "用拓扑理解进度；需要细节时用节点 ID 对应路径读取原文。",
        "```mermaid",
        mermaid,
        "```",
    ]
    if node_refs:
        parts.append("### 节点详情索引")
        for nid, path in node_refs.items():
            parts.append(f"- `{nid}` → `{path}`")
    return "\n".join(parts)


def should_inject_symbolic(messages: List[Dict[str, Any]], min_tools: int) -> bool:
    return len(_tool_messages(messages)) >= min_tools


def inject_symbolic_message(
    messages: List[Dict[str, Any]],
    file_storage_dir: str,
    min_tools: int = 3,
) -> List[Dict[str, Any]]:
    if not should_inject_symbolic(messages, min_tools):
        return messages
    mermaid, refs = build_mermaid_task_graph(messages, file_storage_dir)
    body = format_symbolic_system_message(mermaid, refs)
    if not body:
        return messages
    if any(SYMBOLIC_MARKER in str(m.get("content", "")) for m in messages if m.get("role") == "system"):
        return messages
    return messages + [{"role": "system", "content": body}]
