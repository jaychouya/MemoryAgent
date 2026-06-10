"use client";

import { useState, useEffect } from "react";
import ChatPanel from "@/components/ChatPanel";
import SettingsPanel, { ModelConfig } from "@/components/SettingsPanel";
import MemoryPanel from "@/components/MemoryPanel";
import { apiUrl, fetchBackendConfigured, saveModelConfig } from "@/lib/api";

export default function Home() {
  const [showSettings, setShowSettings] = useState(false);
  const [modelConfig, setModelConfig] = useState<ModelConfig | null>(null);
  const [crossSessionEnabled, setCrossSessionEnabled] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem("modelConfig");
    let savedCfg: ModelConfig | null = null;
    if (saved) {
      savedCfg = JSON.parse(saved);
      setModelConfig(savedCfg);
    }
    const crossSession = localStorage.getItem("crossSessionEnabled");
    if (crossSession) {
      setCrossSessionEnabled(JSON.parse(crossSession));
    }
    fetch(apiUrl("/api/config"))
      .then((r) => r.json())
      .then((data) => {
        if (data.configured) {
          setModelConfig((prev) => {
            if (prev?.apiKey) return prev;
            if (savedCfg?.apiKey) return savedCfg;
            if (data.base_url && data.model) {
              return {
                providerId: savedCfg?.providerId || "custom",
                apiKey: "",
                baseUrl: data.base_url,
                model: data.model,
              };
            }
            return prev;
          });
          return;
        }
        if (!savedCfg?.apiKey) {
          setShowSettings(true);
        }
      })
      .catch(() => {
        if (!savedCfg?.apiKey) {
          setShowSettings(true);
        }
      });
  }, []);

  const handleSaveConfig = async (config: ModelConfig) => {
    if (!config.apiKey?.trim()) {
      alert("请填写 API Key");
      return;
    }
    try {
      await saveModelConfig(config);
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "配置保存失败");
      return;
    }
    setModelConfig(config);
    localStorage.setItem("modelConfig", JSON.stringify(config));
    window.dispatchEvent(new CustomEvent("memory-agent:config-saved"));
  };

  return (
    <main className="h-screen flex flex-col bg-slate-50 overflow-hidden">
      {/* 顶部导航 */}
      <nav className="bg-white border-b border-slate-200 px-4 py-2 flex-shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center shadow-md shadow-indigo-500/20">
              <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <div>
              <h1 className="text-sm font-bold text-slate-900">MemoryAgent</h1>
              <p className="text-[10px] text-slate-400">认知记忆架构</p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            {modelConfig && (
              <div className="flex items-center gap-1.5 px-2 py-1 bg-green-50 rounded-md">
                <span className="w-1.5 h-1.5 bg-green-500 rounded-full"></span>
                <span className="text-[10px] text-green-700 font-medium">{modelConfig.model}</span>
              </div>
            )}
            <button
              onClick={() => setShowSettings(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 rounded-md transition-colors text-xs font-medium text-slate-700"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              配置
            </button>
          </div>
        </div>
      </nav>

      {/* 主内容区 */}
      <div className="flex-1 flex overflow-hidden">
        {/* 左侧信息栏 */}
        <aside className="w-56 bg-white border-r border-slate-200 flex flex-col overflow-y-auto flex-shrink-0 hidden lg:flex">
          {/* 记忆架构 */}
          <div className="p-3 border-b border-slate-100">
            <h3 className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-2">四类型记忆</h3>
            <div className="space-y-1.5">
              {[
                { name: "用户画像", desc: "偏好与角色", color: "bg-blue-500" },
                { name: "行为反馈", desc: "禁忌与要求", color: "bg-green-500" },
                { name: "项目动态", desc: "决策与截止", color: "bg-purple-500" },
                { name: "外部引用", desc: "链接与文档", color: "bg-amber-500" }
              ].map((item) => (
                <div key={item.name} className="flex items-center gap-2 px-2 py-1.5 rounded-md hover:bg-slate-50">
                  <div className={`w-2 h-2 ${item.color} rounded-full flex-shrink-0`}></div>
                  <div>
                    <p className="text-xs font-medium text-slate-700">{item.name}</p>
                    <p className="text-[10px] text-slate-400">{item.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 核心特性 */}
          <div className="p-3 border-b border-slate-100">
            <h3 className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-2">核心特性</h3>
            <div className="space-y-1">
              {["MCP 侧车", "可解释召回", "本地 Markdown", "冲突自动失效", "CCR 压缩"].map((feature) => (
                <div key={feature} className="flex items-center gap-2 px-2 py-1">
                  <svg className="w-3 h-3 text-green-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span className="text-[11px] text-slate-600">{feature}</span>
                </div>
              ))}
            </div>
          </div>

          {/* 记忆系统状态 */}
          <div className="border-b border-slate-100">
            <MemoryPanel />
          </div>

          {/* 跨会话记忆共享 */}
          <div className="p-3 border-b border-slate-100">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-[11px] font-medium text-slate-700">跨会话记忆共享</p>
                <p className="text-[10px] text-slate-400">不同对话间共享记忆</p>
              </div>
              <button
                onClick={() => {
                  const next = !crossSessionEnabled;
                  setCrossSessionEnabled(next);
                  localStorage.setItem("crossSessionEnabled", JSON.stringify(next));
                }}
                className={`relative w-10 h-5 rounded-full transition-colors ${crossSessionEnabled ? 'bg-indigo-600' : 'bg-slate-300'}`}
              >
                <div className={`absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform ${crossSessionEnabled ? 'translate-x-5' : ''}`}></div>
              </button>
            </div>
          </div>

          {/* 模型信息 */}
          <div className="p-3">
            <h3 className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-2">当前模型</h3>
            {modelConfig ? (
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 bg-green-500 rounded-full"></span>
                  <span className="text-[11px] text-slate-700 font-medium">已连接</span>
                </div>
                <div className="text-[10px] text-slate-500 space-y-0.5 px-2">
                  <p>厂商: {modelConfig.providerId}</p>
                  <p>模型: {modelConfig.model}</p>
                </div>
                <button
                  onClick={() => setShowSettings(true)}
                  className="text-[10px] text-indigo-600 hover:text-indigo-700 font-medium px-2"
                >
                  修改 →
                </button>
              </div>
            ) : (
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 bg-amber-500 rounded-full"></span>
                  <span className="text-[11px] text-slate-700">未配置</span>
                </div>
                <button
                  onClick={() => setShowSettings(true)}
                  className="w-full px-2 py-1.5 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors text-[11px] font-medium"
                >
                  配置模型
                </button>
              </div>
            )}
          </div>

          {/* 底部信息 */}
          <div className="mt-auto p-3 border-t border-slate-100">
            <p className="text-[10px] text-slate-400 text-center">支持 15+ 大模型厂商</p>
          </div>
        </aside>

        {/* 右侧聊天区 */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <ChatPanel
            modelConfig={modelConfig}
            crossSessionMemory={crossSessionEnabled}
          />
        </div>
      </div>

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
