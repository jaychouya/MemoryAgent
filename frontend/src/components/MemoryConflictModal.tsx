"use client";

import { useState } from "react";
import { apiUrl, getUserId } from "@/lib/api";

export interface PendingConflict {
  new_content: string;
  memory_type: string;
  candidates: {
    memory_id: string;
    content: string;
    conflict_reason?: string;
  }[];
}

interface Props {
  conflict: PendingConflict;
  sessionId: string;
  onResolved: () => void;
  onDismiss: () => void;
}

export default function MemoryConflictModal({
  conflict,
  sessionId,
  onResolved,
  onDismiss,
}: Props) {
  const [busy, setBusy] = useState(false);

  const resolve = async (keepExistingId: string | null, supersedeIds: string[]) => {
    setBusy(true);
    try {
      const res = await fetch(apiUrl("/api/memory/conflicts/resolve"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: getUserId(),
          new_content: conflict.new_content,
          memory_type: conflict.memory_type,
          keep_existing_id: keepExistingId,
          supersede_ids: supersedeIds,
          session_id: sessionId,
        }),
      });
      if (!res.ok) throw new Error("resolve failed");
      onResolved();
    } catch {
      alert("记忆冲突处理失败，请稍后重试。");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-lg w-full p-4 text-sm">
        <h3 className="font-semibold text-slate-800 mb-2">检测到记忆冲突</h3>
        <p className="text-slate-600 mb-3">新记忆与已有条目可能矛盾，请选择保留哪条：</p>
        <div className="bg-amber-50 border border-amber-100 rounded-lg p-2 mb-3 text-slate-700">
          <div className="text-[10px] text-amber-700 mb-1">新记忆</div>
          {conflict.new_content}
        </div>
        <ul className="space-y-2 mb-4 max-h-48 overflow-y-auto">
          {conflict.candidates.map((c) => (
            <li key={c.memory_id} className="border border-slate-200 rounded-lg p-2">
              <div className="text-[10px] text-slate-400 mb-1">{c.memory_id}</div>
              <div className="text-slate-700">{c.content}</div>
            </li>
          ))}
        </ul>
        <div className="flex flex-wrap gap-2 justify-end">
          <button
            type="button"
            disabled={busy}
            onClick={onDismiss}
            className="px-3 py-1.5 text-slate-600 hover:bg-slate-100 rounded-lg"
          >
            稍后处理
          </button>
          {conflict.candidates.map((c) => (
            <button
              key={`keep-${c.memory_id}`}
              type="button"
              disabled={busy}
              onClick={() => resolve(c.memory_id, [])}
              className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 rounded-lg"
            >
              保留旧记忆
            </button>
          ))}
          <button
            type="button"
            disabled={busy}
            onClick={() =>
              resolve(
                null,
                conflict.candidates.map((c) => c.memory_id)
              )
            }
            className="px-3 py-1.5 bg-indigo-600 text-white hover:bg-indigo-700 rounded-lg"
          >
            使用新记忆
          </button>
        </div>
      </div>
    </div>
  );
}
