"""CCR-style reversible blob store (Headroom-inspired, local-first)."""

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from src.agent.content_router import compress_by_kind, detect_content_kind


def _blob_dir(storage_dir: str) -> Path:
    p = Path(storage_dir) / "ccr_blobs"
    p.mkdir(parents=True, exist_ok=True)
    return p


def store_blob(content: str, storage_dir: str, meta: Optional[Dict[str, Any]] = None) -> str:
    digest = hashlib.sha256(content.encode("utf-8", errors="replace")).hexdigest()[:16]
    ref_id = f"ccr_{digest}"
    path = _blob_dir(storage_dir) / f"{ref_id}.txt"
    if not path.exists():
        path.write_text(content, encoding="utf-8")
    sidecar = path.with_suffix(".json")
    if meta and not sidecar.exists():
        sidecar.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    return ref_id


def retrieve_blob(ref_id: str, storage_dir: str) -> Optional[str]:
    if not ref_id or not ref_id.startswith("ccr_"):
        return None
    path = _blob_dir(storage_dir) / f"{ref_id}.txt"
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def compress_with_ccr(
    content: str,
    storage_dir: str,
    offload_threshold: int,
    max_preview: int,
) -> Tuple[str, Optional[str], Dict[str, Any]]:
    text = content or ""
    kind = detect_content_kind(text)
    stats: Dict[str, Any] = {"kind": kind.value, "offloaded": False, "ref_id": None}

    if len(text) <= offload_threshold:
        preview, extra = compress_by_kind(text, kind, max_preview)
        stats.update(extra)
        return preview, None, stats

    ref_id = store_blob(text, storage_dir, meta={"kind": kind.value, "chars": len(text)})
    preview, extra = compress_by_kind(text, kind, max_preview)
    stats.update(extra)
    stats["offloaded"] = True
    stats["ref_id"] = ref_id
    stats["original_chars"] = len(text)

    trailer = (
        f"\n\n[memoryagent-ccr] full={len(text)} chars | ref={ref_id} | "
        f"retrieve via memory_retrieve_blob(ref_id=\"{ref_id}\")]"
    )
    return preview + trailer, ref_id, stats
