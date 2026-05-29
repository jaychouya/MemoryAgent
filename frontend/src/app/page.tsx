"use client";

import { useState, useEffect } from "react";
import ChatPanel from "@/components/ChatPanel";
import SettingsPanel, { ModelConfig } from "@/components/SettingsPanel";

export default function Home() {
  const [showSettings, setShowSettings] = useState(false);
  const [modelConfig, setModelConfig] = useState<ModelConfig | null>(null);

  useEffect(() => {
    const saved = localStorage.getItem("modelConfig");
    if (saved) {
      setModelConfig(JSON.parse(saved));
    }
  }, []);

  const handleSaveConfig = (config: ModelConfig) => {
    setModelConfig(config);
    localStorage.setItem("modelConfig", JSON.stringify(config));
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* 顶部导航 */}
      <nav className="bg-white/80 backdrop-blur-sm border-b border-slate-200 px-6 py-3 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-500/25">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <div>
              <h1 className="text-lg font-bold text-slate-900">MemoryAI</h1>
              <p className="text-[10px] text-slate-400 -mt-0.5">认知记忆架构 · 智能助手</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {modelConfig && (
              <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 bg-green-50 rounded-full">
                <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></span>
                <span className="text-xs text-green-700 font-medium">{modelConfig.providerId}</span>
              </div>
            )}
            <button
              onClick={() => setShowSettings(true)}
              className="flex items-center gap-2 px-4 py-2 bg-slate-900 text-white rounded-xl hover:bg-slate-800 transition-colors text-sm font-medium shadow-sm"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <span className="hidden sm:inline">模型配置</span>
            </button>
          </div>
        </div>
      </nav>

      {/* 主内容区 */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          
          {/* 左侧：信息面板 */}
          <aside className="lg:col-span-3 space-y-4">
            {/* 记忆架构 */}
            <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-sm">
              <h3 className="text-sm font-semibold text-slate-900 mb-3 flex items-center gap-2">
                <svg className="w-4 h-4 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                </svg>
                四层记忆架构
              </h3>
              <div className="space-y-2">
                {[
                  { name: "工作记忆", desc: "当前对话上下文", color: "indigo" },
                  { name: "短期记忆", desc: "近期对话摘要", color: "purple" },
                  { name: "长期记忆", desc: "稳定偏好知识", color: "pink" },
                  { name: "情景记忆", desc: "重要事件经历", color: "amber" }
                ].map((item) => (
                  <div key={item.name} className={`p-2.5 bg-${item.color}-50 rounded-lg border border-${item.color}-100`}>
                    <div className="flex items-center gap-2 mb-1">
                      <div className={`w-2 h-2 bg-${item.color}-500 rounded-full`}></div>
                      <span className={`text-xs font-medium text-${item.color}-900`}>{item.name}</span>
                    </div>
                    <p className={`text-[11px] text-${item.color}-600 pl-4`}>{item.desc}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* 核心特性 */}
            <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-sm">
              <h3 className="text-sm font-semibold text-slate-900 mb-3 flex items-center gap-2">
                <svg className="w-4 h-4 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                核心特性
              </h3>
              <ul className="space-y-2">
                {["自主性决策引擎", "记忆可解释性", "跨会话记忆共享", "智能记忆遗忘"].map((feature) => (
                  <li key={feature} className="flex items-center gap-2">
                    <svg className="w-3.5 h-3.5 text-green-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    <span className="text-xs text-slate-600">{feature}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* 模型状态 */}
            <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-sm">
              <h3 className="text-sm font-semibold text-slate-900 mb-3 flex items-center gap-2">
                <svg className="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
                </svg>
                模型状态
              </h3>
              {modelConfig ? (
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                    <span className="text-xs text-slate-700 font-medium">已配置</span>
                  </div>
                  <div className="text-[11px] text-slate-500 space-y-1 pl-4">
                    <p>厂商: {modelConfig.providerId}</p>
                    <p>模型: {modelConfig.model}</p>
                  </div>
                  <button
                    onClick={() => setShowSettings(true)}
                    className="text-xs text-indigo-600 hover:text-indigo-700 font-medium pl-4"
                  >
                    修改配置 →
                  </button>
                </div>
              ) : (
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 bg-amber-500 rounded-full"></span>
                    <span className="text-xs text-slate-700 font-medium">未配置</span>
                  </div>
                  <p className="text-[11px] text-slate-500 pl-4">
                    点击上方按钮配置模型
                  </p>
                  <button
                    onClick={() => setShowSettings(true)}
                    className="text-xs text-indigo-600 hover:text-indigo-700 font-medium pl-4"
                  >
                    立即配置 →
                  </button>
                </div>
              )}
            </div>
          </aside>
          
          {/* 右侧：聊天界面 */}
          <div className="lg:col-span-9">
            <ChatPanel modelConfig={modelConfig} />
          </div>
        </div>
      </div>
      
      {/* 底部 */}
      <footer className="bg-white border-t border-slate-200 px-6 py-3 mt-6">
        <div className="max-w-7xl mx-auto flex items-center justify-between text-xs text-slate-400">
          <p>MemoryAI · 基于认知记忆架构的个人AI助手</p>
          <p>支持 14+ 大模型厂商</p>
        </div>
      </footer>

      {/* Settings Modal */}
      <SettingsPanel
        isOpen={showSettings}
        onClose={() => setShowSettings(false)}
        onSave={handleSaveConfig}
        currentConfig={modelConfig || undefined}
      />
    </main>
  );
}
