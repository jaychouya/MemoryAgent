"use client";

import { useState, useEffect } from "react";
import { apiFetch, fetchSidecarHealth, fetchSidecarStatus, getUserId, memoryExportUrl, type SidecarHealth, type SidecarStatus } from "@/lib/api";

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
  const [archivedMemories, setArchivedMemories] = useState<MemoryItem[]>([]);
  const [showArchived, setShowArchived] = useState(false);
  const [notice, setNotice] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [sidecarStatus, setSidecarStatus] = useState<SidecarStatus | null>(null);
  const [sidecarHealth, setSidecarHealth] = useState<SidecarHealth | null>(null);

  const loadSidecarStatus = async () => {
    try {
      setSidecarStatus(await fetchSidecarStatus());
      setSidecarHealth(await fetchSidecarHealth());
    } catch {
      setSidecarStatus(null);
      setSidecarHealth(null);
    }
  };

  useEffect(() => {
    loadStats();
    loadMetrics();
    loadMemories();
    loadSidecarStatus();
    const onWrites = () => {
      loadMemories();
      loadStats();
      loadSidecarStatus();
    };
    window.addEventListener("memory-agent:writes", onWrites);
    return () => window.removeEventListener("memory-agent:writes", onWrites);
  }, []);

  const loadStats = async () => {
    setIsLoading(true);
    try {
      const response = await apiFetch(
        `/api/memory/stats?user_id=${encodeURIComponent(getUserId())}`
      );
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
    setNotice(null);
    try {
      const response = await apiFetch("/api/memory/metrics/run-eval", {
        method: "POST",
      });
      if (response.ok) {
        await loadMetrics();
        setNotice({ type: "success", text: "评估完成，质量指标已更新。" });
      } else {
        setNotice({ type: "error", text: "评估失败，请检查后端服务。" });
      }
    } catch (error) {
      console.error("Eval failed:", error);
      setNotice({ type: "error", text: "评估失败，请稍后重试。" });
    } finally {
      setEvalRunning(false);
    }
  };

  const loadMemories = async () => {
    try {
      const uid = encodeURIComponent(getUserId());
      const [activeRes, archivedRes] = await Promise.all([
        apiFetch(`/api/memories?user_id=${uid}&limit=50`),
        apiFetch(`/api/memories/archived?user_id=${uid}&limit=30`),
      ]);
      if (activeRes.ok) {
        setMemories(await activeRes.json());
      }
      if (archivedRes.ok) {
        setArchivedMemories(await archivedRes.json());
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
    setNotice(null);
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
      setNotice({ type: "success", text: "记忆已更新。" });
    } else {
      setNotice({ type: "error", text: "保存失败，请检查权限或内容。" });
    }
  };

  const deleteMemory = async (memoryId: string) => {
    if (!confirm("确定删除这条记忆吗？")) return;
    setNotice(null);
    const response = await apiFetch(
      `/api/memories/${encodeURIComponent(memoryId)}?user_id=${encodeURIComponent(getUserId())}`,
      { method: "DELETE" }
    );
    if (response.ok) {
      await loadMemories();
      await loadStats();
      setNotice({ type: "success", text: "记忆已删除。" });
    } else {
      setNotice({ type: "error", text: "删除失败，请检查权限。" });
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

      {notice && (
        <div className={`text-[10px] rounded-lg px-2 py-1.5 border ${
          notice.type === "success"
            ? "bg-green-50 text-green-700 border-green-200"
            : "bg-red-50 text-red-700 border-red-200"
        }`}>
          {notice.text}
        </div>
      )}

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
          {sidecarHealth?.scope && (
            <div className="text-[10px] text-slate-500 bg-slate-50 rounded-lg p-2 border border-slate-100">
              <p>scope: {sidecarHealth.scope.user_id}
                {sidecarHealth.scope.project_id ? ` / ${sidecarHealth.scope.project_id}` : ""}
              </p>
            </div>
          )}
          {sidecarHealth?.checks && sidecarHealth.checks.length > 0 && (
            <div className="rounded-lg border border-slate-200 p-2 space-y-1">
              <p className="text-[10px] font-medium text-slate-700">记→用→信 检查</p>
              {sidecarHealth.checks.map((c) => (
                <div key={c.id} className="flex items-start gap-1.5 text-[10px]">
                  <span className={c.ok ? "text-green-600" : "text-amber-600"}>
                    {c.ok ? "✓" : "○"}
                  </span>
                  <span className="text-slate-600">
                    {c.label}
                    {c.optional ? "（可选）" : ""}
                  </span>
                </div>
              ))}
              {sidecarHealth.tips?.[0] && (
                <p className="text-[10px] text-indigo-700 pt-1 border-t border-slate-100 mt-1">
                  {sidecarHealth.tips[0]}
                </p>
              )}
            </div>
          )}
          {sidecarStatus?.ide_notice && (
            <div className="rounded-lg border border-indigo-100 bg-indigo-50/80 p-2 text-[10px] text-indigo-900">
              <p className="font-medium text-indigo-800">侧车状态</p>
              <p className="mt-0.5">{sidecarStatus.ide_notice}</p>
              {sidecarStatus.last_recall?.query && (
                <p className="mt-1 text-indigo-600/80">
                  最近召回：{sidecarStatus.last_recall.query.slice(0, 40)}
                  {sidecarStatus.last_recall.count != null
                    ? ` · ${sidecarStatus.last_recall.count} 条`
                    : ""}
                </p>
              )}
            </div>
          )}
          <div className="grid grid-cols-2 gap-2">
            <div className="bg-slate-50 rounded-lg p-2 text-center">
              <p className="text-lg font-bold text-indigo-600">{stats.total}</p>
              <p className="text-[10px] text-slate-500">有效记忆</p>
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
          <div className="bg-green-50 rounded-lg p-2 border border-green-100">
            <p className="text-[10px] font-medium text-green-800">纠错与导出</p>
            <p className="text-[10px] text-green-700 mt-0.5">
              对话中说「记错了…」「忘记…」可触发删除；或在「记忆管理」编辑。导出记忆可分享给团队。
            </p>
            <a
              href={memoryExportUrl(getUserId(), sidecarHealth?.scope?.project_id)}
              target="_blank"
              rel="noreferrer"
              className="inline-block mt-1.5 text-[10px] text-indigo-700 hover:underline"
            >
              导出当前 scope 记忆 (JSON)
            </a>
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
            <div className="bg-indigo-50 rounded-lg p-3 border border-indigo-100">
              <p className="text-[11px] font-semibold text-indigo-800">暂无记忆</p>
              <p className="text-[10px] text-indigo-700 mt-1">
                在聊天中说明需要长期记住的项目信息或规则，系统会自动沉淀，你可在此编辑或删除。
              </p>
            </div>
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
          {archivedMemories.length > 0 && (
            <details
              className="bg-amber-50 rounded-lg border border-amber-100"
              open={showArchived}
              onToggle={(e) => setShowArchived((e.target as HTMLDetailsElement).open)}
            >
              <summary className="cursor-pointer text-[11px] font-medium text-amber-900 px-2 py-2">
                已废弃记忆 ({archivedMemories.length})
              </summary>
              <div className="px-2 pb-2 space-y-2">
                {archivedMemories.map((memory) => (
                  <div
                    key={memory.memory_id}
                    className="bg-white/80 rounded p-2 border border-amber-100 text-[10px] text-slate-600"
                  >
                    <p className="font-medium text-slate-700">
                      {memory.description || memory.memory_id}
                    </p>
                    <p className="mt-0.5 line-clamp-3">{memory.content}</p>
                    {memory.superseded_by && (
                      <p className="text-amber-800 mt-1">替代者: {memory.superseded_by}</p>
                    )}
                    {memory.valid_until && (
                      <p className="text-slate-400">废弃于: {memory.valid_until}</p>
                    )}
                  </div>
                ))}
              </div>
            </details>
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
          记忆可编辑、可删除；超过1天的记忆标记为陈旧，引用前会提醒验证。
        </p>
      </div>
    </div>
  );
}
