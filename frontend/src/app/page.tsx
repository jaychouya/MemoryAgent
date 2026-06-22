"use client";

import { useState, useEffect } from "react";
import ChatPanel from "@/components/ChatPanel";
import SettingsPanel, { ModelConfig } from "@/components/SettingsPanel";
import MemoryPanel from "@/components/MemoryPanel";
import { apiUrl, saveModelConfig } from "@/lib/api";

export default function Home() {
  const [showSettings, setShowSettings] = useState(false);
  const [showMemories, setShowMemories] = useState(false);
  const [modelConfig, setModelConfig] = useState<ModelConfig | null>(null);
  const [crossSessionEnabled, setCrossSessionEnabled] = useState(false);
  const [needsConfig, setNeedsConfig] = useState(false);
  const [backendConfigured, setBackendConfigured] = useState(false);
  const [backendUnreachable, setBackendUnreachable] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem("modelConfig");
    let savedCfg: ModelConfig | null = null;
    if (saved) {
      try {
        savedCfg = JSON.parse(saved);
        setModelConfig(savedCfg);
      } catch {
        localStorage.removeItem("modelConfig");
      }
    }
    const crossSession = localStorage.getItem("crossSessionEnabled");
    if (crossSession) setCrossSessionEnabled(JSON.parse(crossSession));

    const hadBackend = sessionStorage.getItem("backendConfigured") === "true";
    if (hadBackend) {
      setBackendConfigured(true);
      setNeedsConfig(false);
    }

    fetch(apiUrl("/health"))
      .then((r) => {
        if (!r.ok) throw new Error("health");
        setBackendUnreachable(false);
        return fetch(apiUrl("/api/config"));
      })
      .then((r) => r.json())
      .then((data: { configured?: boolean; base_url?: string; model?: string }) => {
        if (data.configured) {
          setBackendConfigured(true);
          setNeedsConfig(false);
          sessionStorage.setItem("backendConfigured", "true");
          setModelConfig((prev) => {
            if (prev?.apiKey) return prev;
            if (savedCfg?.apiKey) return savedCfg;
            if (data.base_url && data.model) {
              const isMimo =
                data.base_url.includes("xiaomimimo") || String(data.model).startsWith("mimo");
              return {
                providerId: isMimo ? "xiaomi" : savedCfg?.providerId || "custom",
                apiKey: "",
                baseUrl: data.base_url,
                model: data.model,
              };
            }
            return prev;
          });
        } else if (!savedCfg?.apiKey) {
          setNeedsConfig(true);
        }
      })
      .catch(() => {
        setBackendUnreachable(true);
        if (!hadBackend && !savedCfg?.apiKey) setNeedsConfig(true);
      });
  }, []);

  const handleSaveConfig = async (config: ModelConfig) => {
    if (!config.apiKey?.trim() && !backendConfigured) {
      alert("请填写 API Key");
      return false;
    }
    if (config.apiKey?.trim()) {
      try {
        await saveModelConfig({
          apiKey: config.apiKey,
          baseUrl: config.baseUrl,
          model: config.model,
          memoryModel: config.memoryModel,
        });
      } catch (e: unknown) {
        alert(e instanceof Error ? e.message : "保存失败");
        return false;
      }
      setBackendConfigured(true);
      sessionStorage.setItem("backendConfigured", "true");
    }
    setModelConfig(config);
    setNeedsConfig(false);
    localStorage.setItem("modelConfig", JSON.stringify(config));
    window.dispatchEvent(new CustomEvent("memory-agent:config-saved"));
    return true;
  };

  return (
    <main className="h-screen flex flex-col bg-white overflow-hidden">
      <header className="flex items-center justify-between px-4 h-12 border-b border-slate-100 flex-shrink-0">
        <span className="text-sm font-semibold text-slate-900">MemoryAgent</span>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setShowMemories(true)}
            className="text-sm text-slate-600 hover:text-slate-900 px-2 py-1"
          >
            记忆
          </button>
          <button
            type="button"
            onClick={() => setShowSettings(true)}
            className="text-sm text-slate-600 hover:text-slate-900 px-2 py-1"
          >
            设置
          </button>
        </div>
      </header>

      {backendUnreachable && (
        <div className="px-4 py-2 bg-red-50 text-xs text-red-700 border-b border-red-100">
          服务未启动，请在项目目录运行 bash scripts/dev.sh
        </div>
      )}

      {needsConfig && !backendConfigured && !modelConfig?.apiKey && !backendUnreachable && (
        <div className="px-4 py-2 bg-amber-50 text-xs text-amber-800 border-b border-amber-100 flex justify-between items-center">
          <span>请先配置 API Key</span>
          <button type="button" onClick={() => setShowSettings(true)} className="font-medium underline">
            去设置
          </button>
        </div>
      )}

      <div className="flex-1 min-h-0">
        <ChatPanel modelConfig={modelConfig} crossSessionMemory={crossSessionEnabled} />
      </div>

      {showMemories && (
        <div className="fixed inset-0 z-40 flex justify-end">
          <button
            type="button"
            aria-label="关闭"
            className="absolute inset-0 bg-black/20"
            onClick={() => setShowMemories(false)}
          />
          <div className="relative w-full max-w-sm h-full bg-white shadow-xl flex flex-col">
            <MemoryPanel />
            <button
              type="button"
              onClick={() => setShowMemories(false)}
              className="m-3 py-2 text-sm text-center rounded-lg bg-slate-100 text-slate-600"
            >
              关闭
            </button>
          </div>
        </div>
      )}

      <SettingsPanel
        isOpen={showSettings}
        onClose={() => setShowSettings(false)}
        onSave={handleSaveConfig}
        currentConfig={modelConfig || undefined}
        backendConfigured={backendConfigured}
        crossSessionEnabled={crossSessionEnabled}
        onCrossSessionChange={(v) => {
          setCrossSessionEnabled(v);
          localStorage.setItem("crossSessionEnabled", JSON.stringify(v));
        }}
      />
    </main>
  );
}
