"use client";

import { useState, useEffect } from "react";

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

export default function MemoryPanel() {
  const [stats, setStats] = useState<MemoryStats | null>(null);
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [evalRunning, setEvalRunning] = useState(false);
  const [activeTab, setActiveTab] = useState<"overview" | "quality">("overview");

  useEffect(() => {
    loadStats();
    loadMetrics();
  }, []);

  const loadStats = async () => {
    setIsLoading(true);
    try {
      const response = await fetch("/api/memory/stats");
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
      const response = await fetch("/api/memory/metrics");
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
      const response = await fetch("/api/memory/metrics/run-eval", {
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
