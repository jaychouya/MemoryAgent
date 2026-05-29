"use client";

import { useState, useEffect } from "react";

interface MemoryStats {
  total: number;
  user: number;
  feedback: number;
  project: number;
  reference: number;
}

interface MemoryItem {
  id: string;
  type: string;
  description: string;
  age_days: number;
  is_stale: boolean;
}

export default function MemoryPanel() {
  const [stats, setStats] = useState<MemoryStats | null>(null);
  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedType, setSelectedType] = useState<string | null>(null);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    setIsLoading(true);
    try {
      const response = await fetch("/api/memory/stats");
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error("Failed to load memory stats:", error);
    } finally {
      setIsLoading(false);
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

  if (isLoading) {
    return (
      <div className="p-4 text-center">
        <div className="animate-spin w-5 h-5 border-2 border-indigo-500 border-t-transparent rounded-full mx-auto"></div>
        <p className="text-xs text-slate-400 mt-2">加载中...</p>
      </div>
    );
  }

  return (
    <div className="p-3 space-y-3">
      <h3 className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
        记忆系统
      </h3>

      {/* Stats Overview */}
      {stats && (
        <div className="grid grid-cols-2 gap-2">
          <div className="bg-slate-50 rounded-lg p-2 text-center">
            <p className="text-lg font-bold text-indigo-600">{stats.total}</p>
            <p className="text-[10px] text-slate-500">总记忆数</p>
          </div>
          {Object.entries(typeLabels).map(([type, label]) => (
            <div
              key={type}
              className={`bg-slate-50 rounded-lg p-2 text-center cursor-pointer transition-colors ${
                selectedType === type ? "ring-2 ring-indigo-500" : ""
              }`}
              onClick={() => setSelectedType(selectedType === type ? null : type)}
            >
              <p className="text-sm font-bold text-slate-700">
                {stats[type as keyof MemoryStats] || 0}
              </p>
              <p className="text-[10px] text-slate-500">{label}</p>
            </div>
          ))}
        </div>
      )}

      {/* Memory Type Legend */}
      <div className="space-y-1.5">
        <p className="text-[10px] font-medium text-slate-500 uppercase">记忆类型</p>
        {Object.entries(typeLabels).map(([type, label]) => (
          <div key={type} className="flex items-center gap-2">
            <div className={`w-2 h-2 ${typeColors[type]} rounded-full`}></div>
            <span className="text-[11px] text-slate-600">{label}</span>
          </div>
        ))}
      </div>

      {/* Staleness Warning */}
      <div className="bg-amber-50 rounded-lg p-2 border border-amber-200">
        <p className="text-[10px] text-amber-700">
          ⚠️ 超过1天的记忆会被标记为"陈旧"，在引用前会提醒验证。
        </p>
      </div>
    </div>
  );
}
