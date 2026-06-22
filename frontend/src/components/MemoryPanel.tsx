"use client";

import { useState, useEffect } from "react";
import { apiFetch, getUserId } from "@/lib/api";

interface MemoryItem {
  memory_id: string;
  content: string;
  description?: string;
  memory_type?: string;
}

export default function MemoryPanel() {
  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(true);

  const loadMemories = async () => {
    try {
      const uid = encodeURIComponent(getUserId());
      const res = await apiFetch(`/api/memories?user_id=${uid}&limit=50`);
      if (res.ok) setMemories(await res.json());
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMemories();
    const onWrites = () => loadMemories();
    window.addEventListener("memory-agent:writes", onWrites);
    return () => window.removeEventListener("memory-agent:writes", onWrites);
  }, []);

  const saveEdit = async (id: string) => {
    const res = await apiFetch(`/api/memories/${encodeURIComponent(id)}`, {
      method: "PATCH",
      body: JSON.stringify({ user_id: getUserId(), content: draft }),
    });
    if (res.ok) {
      setEditingId(null);
      loadMemories();
    }
  };

  const deleteMemory = async (id: string) => {
    if (!confirm("删除这条记忆？")) return;
    const res = await apiFetch(
      `/api/memories/${encodeURIComponent(id)}?user_id=${encodeURIComponent(getUserId())}`,
      { method: "DELETE" }
    );
    if (res.ok) loadMemories();
  };

  if (loading) {
    return <p className="p-4 text-sm text-slate-400 text-center">加载中…</p>;
  }

  return (
    <div className="flex flex-col h-full">
      <div className="px-4 py-3 border-b border-slate-100">
        <h2 className="text-sm font-semibold text-slate-800">我的记忆</h2>
        <p className="text-xs text-slate-400 mt-0.5">{memories.length} 条</p>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {memories.length === 0 ? (
          <p className="text-sm text-slate-400 text-center py-8">
            还没有记忆。聊天时说的偏好和习惯会自动记在这里。
          </p>
        ) : (
          memories.map((m) => (
            <div
              key={m.memory_id}
              className="rounded-xl border border-slate-100 bg-slate-50/80 p-3"
            >
              {editingId === m.memory_id ? (
                <div className="space-y-2">
                  <textarea
                    value={draft}
                    onChange={(e) => setDraft(e.target.value)}
                    className="w-full text-sm border border-slate-200 rounded-lg px-2 py-1.5 min-h-[72px]"
                  />
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => saveEdit(m.memory_id)}
                      className="text-xs px-3 py-1 rounded-lg bg-indigo-600 text-white"
                    >
                      保存
                    </button>
                    <button
                      type="button"
                      onClick={() => setEditingId(null)}
                      className="text-xs px-3 py-1 rounded-lg bg-slate-200 text-slate-600"
                    >
                      取消
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  <p className="text-sm text-slate-700 leading-relaxed">{m.content}</p>
                  <div className="flex gap-3 mt-2">
                    <button
                      type="button"
                      onClick={() => {
                        setEditingId(m.memory_id);
                        setDraft(m.content);
                      }}
                      className="text-xs text-indigo-600"
                    >
                      编辑
                    </button>
                    <button
                      type="button"
                      onClick={() => deleteMemory(m.memory_id)}
                      className="text-xs text-red-500"
                    >
                      删除
                    </button>
                  </div>
                </>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
