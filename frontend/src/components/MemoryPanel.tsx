"use client";

import { useState, useEffect } from "react";
import { apiFetch, getUserId } from "@/lib/api";

interface MemoryStats {
  total: number;
  user: number;
  feedback: number;
  project: number;
  reference: number;
}

interface EvalMetrics {
  recall_at_5?: number;
  false_inject_rate?: number;
  evaluated_at?: string;
}

interface MetricsResponse {
  storage_stats: MemoryStats;
  vector_count: number;
  last_eval: EvalMetrics | null;
}

interface MemoryItem {
  memory_id: string;
  content: string;
  description?: string;
  memory_type?: string;
  layer?: string;
  source_session_id?: string;
  source_turn?: number;
  source_quote?: string;
  superseded_by?: string;
  valid_until?: string;
  conflict_reason?: string;
}

export default function MemoryPanel() {
  const [stats, setStats] = useState<MemoryStats | null>(null);
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draftContent, setDraftContent] = useState("");
  const [draftDescription, setDraftDescription] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [evalRunning, setEvalRunning] = useState(false);
  const [activeTab, setActiveTab] = useState<"overview" | "memories" | "quality">("overview");

  useEffect(() => {
    loadStats();
    loadMetrics();
    loadMemories();
  }, []);

  const loadStats = async () => {
    setIsLoading(true);
    try {
      const response = await apiFetch("/api/memory/stats");
      if (response.ok) {
        setStats(await response.json());
      }
    } catch (error) {
      console.error("Failed to load memory stats:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadMetrics = async () => {
    try {
      const response = await apiFetch("/api/memory/metrics");
      if (response.ok) {
        setMetrics(await response.json());
      }
    } catch (error) {
      console.error("Failed to load metrics:", error);
    }
  };

  const runEval = async () => {
    setEvalRunning(true);
    try {
      const response = await apiFetch("/api/memory/metrics/run-eval", {
        method: "POST",
      });
      if (response.ok) {
        await loadMetrics();
      }
    } catch (error) {
      console.error("Eval failed:", error);
    } finally {
      setEvalRunning(false);
    }
  };

  const loadMemories = async () => {
    try {
      const response = await apiFetch(`/api/memories?user_id=${encodeURIComponent(getUserId())}&limit=50`);
      if (response.ok) {
        setMemories(await response.json());
      }
    } catch (error) {
      console.error("Failed to load memories:", error);
    }
  };

  const startEdit = (memory: MemoryItem) => {
    setEditingId(memory.memory_id);
    setDraftContent(memory.content || "");
    setDraftDescription(memory.description || "");
  };

  const saveEdit = async (memoryId: string) => {
    const response = await apiFetch(`/api/memories/${encodeURIComponent(memoryId)}`, {
      method: "PATCH",
      body: JSON.stringify({
        user_id: getUserId(),
        content: draftContent,
        description: draftDescription,
      }),
    });
    if (response.ok) {
      setEditingId(null);
      await loadMemories();
      await loadStats();
    }
  };

  const deleteMemory = async (memoryId: string) => {
    if (!confirm("确定删除这条记忆吗？")) return;
    const response = await apiFetch(
      `/api/memories/${encodeURIComponent(memoryId)}?user_id=${encodeURIComponent(getUserId())}`,
      { method: "DELETE" }
    );
    if (response.ok) {
      await loadMemories();
      await loadStats();
    }
  };

  const typeLabels: Record<string, string> = {
    user: "用户画像",
    feedback: "行为反馈",
    project: "项目动态",
    reference: "外部引用",
  };

  const typeColors: Record<string, string> = {
    user: "bg-blue-500",
    feedback: "bg-green-500",
    project: "bg-purple-500",
    reference: "bg-amber-500",
  };

  if (isLoading && !stats) {
    return (
      <div className="p-4 text-center">
        <div className="animate-spin w-5 h-5 border-2 border-indigo-500 border-t-transparent rounded-full mx-auto"></div>
        <p className="text-xs text-slate-400 mt-2">加载中...</p>
      </div>
    );
  }

  const recallPct = metrics?.last_eval?.recall_at_5 != null
    ? Math.round(metrics.last_eval.recall_at_5 * 100)
    : null;

  return (
    <div className="p-3 space-y-3">
      <h3 className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
        记忆系统
      </h3>

      <div className="flex gap-1 text-[10px]">
        <button
          type="button"
          onClick={() => setActiveTab("overview")}
          className={`px-2 py-1 rounded ${activeTab === "overview" ? "bg-indigo-100 text-indigo-700" : "bg-slate-100 text-slate-600"}`}
        >
          概览
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("quality")}
          className={`px-2 py-1 rounded ${activeTab === "quality" ? "bg-indigo-100 text-indigo-700" : "bg-slate-100 text-slate-600"}`}
        >
          质量指标
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("memories")}
          className={`px-2 py-1 rounded ${activeTab === "memories" ? "bg-indigo-100 text-indigo-700" : "bg-slate-100 text-slate-600"}`}
        >
          记忆管理
        </button>
      </div>

      {activeTab === "overview" && stats && (
        <>
          <div className="grid grid-cols-2 gap-2">
            <div className="bg-slate-50 rounded-lg p-2 text-center">
              <p className="text-lg font-bold text-indigo-600">{stats.total}</p>
              <p className="text-[10px] text-slate-500">总记忆数</p>
            </div>
            {Object.entries(typeLabels).map(([type, label]) => (
              <div key={type} className="bg-slate-50 rounded-lg p-2 text-center">
                <p className="text-sm font-bold text-slate-700">
                  {stats[type as keyof MemoryStats] || 0}
                </p>
                <p className="text-[10px] text-slate-500">{label}</p>
              </div>
            ))}
          </div>
          <div className="space-y-1.5">
            {Object.entries(typeLabels).map(([type, label]) => (
              <div key={type} className="flex items-center gap-2">
                <div className={`w-2 h-2 ${typeColors[type]} rounded-full`}></div>
                <span className="text-[11px] text-slate-600">{label}</span>
              </div>
            ))}
          </div>
        </>
      )}

      {activeTab === "memories" && (
        <div className="space-y-2">
          <button
            type="button"
            onClick={loadMemories}
            className="w-full text-[11px] py-1.5 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200"
          >
            刷新记忆列表
          </button>
          {memories.length === 0 ? (
            <p className="text-[10px] text-slate-500">暂无记忆</p>
          ) : (
            memories.map((memory) => {
              const memoryType = memory.memory_type || memory.layer || "user";
              const isEditing = editingId === memory.memory_id;
              return (
                <div key={memory.memory_id} className="bg-slate-50 rounded-lg p-2 border border-slate-200 space-y-1.5">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-indigo-100 text-indigo-700">
                      {typeLabels[memoryType] || memoryType}
                    </span>
                    <div className="flex gap-1">
                      <button
                        type="button"
                        onClick={() => startEdit(memory)}
                        className="text-[10px] text-indigo-600"
                      >
                        编辑
                      </button>
                      <button
                        type="button"
                        onClick={() => deleteMemory(memory.memory_id)}
                        className="text-[10px] text-red-600"
                      >
                        删除
                      </button>
                    </div>
                  </div>
                  {isEditing ? (
                    <div className="space-y-1">
                      <input
                        value={draftDescription}
                        onChange={(e) => setDraftDescription(e.target.value)}
                        className="w-full text-[11px] border border-slate-200 rounded px-2 py-1"
                        placeholder="描述"
                      />
                      <textarea
                        value={draftContent}
                        onChange={(e) => setDraftContent(e.target.value)}
                        className="w-full text-[11px] border border-slate-200 rounded px-2 py-1 min-h-[70px]"
                      />
                      <div className="flex gap-2">
                        <button
                          type="button"
                          onClick={() => saveEdit(memory.memory_id)}
                          className="text-[10px] px-2 py-1 rounded bg-indigo-600 text-white"
                        >
                          保存
                        </button>
                        <button
                          type="button"
                          onClick={() => setEditingId(null)}
                          className="text-[10px] px-2 py-1 rounded bg-slate-200 text-slate-700"
                        >
                          取消
                        </button>
                      </div>
                    </div>
                  ) : (
                    <>
                      <p className="text-[11px] font-medium text-slate-700">
                        {memory.description || memory.memory_id}
                      </p>
                      <p className="text-[10px] text-slate-600 break-words">
                        {memory.content}
                      </p>
                    </>
                  )}
                  {(memory.source_quote || memory.superseded_by || memory.valid_until || memory.conflict_reason) && (
                    <div className="text-[9px] text-slate-500 space-y-0.5 border-t border-slate-200 pt-1">
                      {memory.source_quote && <p>证据: {memory.source_quote}</p>}
                      {memory.source_session_id && <p>来源会话: {memory.source_session_id}</p>}
                      {memory.superseded_by && <p>已被替代: {memory.superseded_by}</p>}
                      {memory.valid_until && <p>有效至: {memory.valid_until}</p>}
                      {memory.conflict_reason && <p>冲突原因: {memory.conflict_reason}</p>}
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      )}

      {activeTab === "quality" && (
        <div className="space-y-2">
          <div className="bg-slate-50 rounded-lg p-2">
            <p className="text-[10px] text-slate-500">向量索引（持久化）</p>
            <p className="text-sm font-bold text-slate-800">
              {metrics?.vector_count ?? "—"} 条
            </p>
          </div>
          {recallPct != null ? (
            <div className="bg-indigo-50 rounded-lg p-2 border border-indigo-100">
              <div className="flex justify-between text-[10px] text-slate-600 mb-1">
                <span>Recall@5</span>
                <span>{recallPct}%</span>
              </div>
              <div className="h-1.5 bg-indigo-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-indigo-500 rounded-full"
                  style={{ width: `${recallPct}%` }}
                />
              </div>
              <p className="text-[10px] text-slate-500 mt-1">
                误注入估计: {((metrics?.last_eval?.false_inject_rate ?? 0) * 100).toFixed(1)}%
              </p>
              {metrics?.last_eval?.evaluated_at && (
                <p className="text-[9px] text-slate-400 mt-0.5">
                  {metrics.last_eval.evaluated_at}
                </p>
              )}
            </div>
          ) : (
            <p className="text-[10px] text-slate-500">尚未运行评估</p>
          )}
          <button
            type="button"
            onClick={runEval}
            disabled={evalRunning}
            className="w-full text-[11px] py-1.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
          >
            {evalRunning ? "评估中…" : "重新评估 Recall@5"}
          </button>
        </div>
      )}

      <div className="bg-amber-50 rounded-lg p-2 border border-amber-200">
        <p className="text-[10px] text-amber-700">
          超过1天的记忆标记为陈旧，引用前会提醒验证。
        </p>
      </div>
    </div>
  );
}
