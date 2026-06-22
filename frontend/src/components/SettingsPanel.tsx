"use client";

import { useState } from "react";
import IntegrationsPanel from "@/components/IntegrationsPanel";

interface ModelProvider {
  id: string;
  name: string;
  baseUrl: string;
  defaultModel: string;
  models: string[];
}

export const PROVIDERS: ModelProvider[] = [
  {
    id: "openai",
    name: "OpenAI",
    baseUrl: "https://api.openai.com/v1",
    defaultModel: "gpt-4.1",
    models: ["gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano", "o3", "o3-mini", "o3-pro", "o4-mini", "gpt-4o", "gpt-4o-mini"]
  },
  {
    id: "dashscope",
    name: "百炼 (阿里云)",
    baseUrl: "https://dashscope.aliyuncs.com/compatible-mode/v1",
    defaultModel: "qwen-max",
    models: ["qwen-max", "qwen-plus", "qwen-turbo", "qwen-long", "qwen-vl-max", "qwen-vl-plus", "deepseek-v4-pro", "deepseek-v4-flash", "deepseek-r1"]
  },
  {
    id: "siliconflow",
    name: "硅基流动",
    baseUrl: "https://api.siliconflow.cn/v1",
    defaultModel: "Qwen/Qwen3-235B-A22B",
    models: [
      "Qwen/Qwen3-235B-A22B", "Qwen/Qwen3-32B", "Qwen/Qwen3-14B", "Qwen/Qwen3-8B",
      "deepseek-ai/DeepSeek-R1-0528", "deepseek-ai/DeepSeek-V3-0324",
      "Pro/deepseek-ai/DeepSeek-R1-0528", "Pro/deepseek-ai/DeepSeek-V3-0324",
      "meta-llama/Llama-4-Maverick-17B-128E-Instruct", "meta-llama/Llama-4-Scout-17B-16E-Instruct",
      "THUDM/GLM-Z1-32B-0414", "internlm/internlm3-8b-instruct"
    ]
  },
  {
    id: "xiaomi",
    name: "小米 (MiMo)",
    baseUrl: "https://token-plan-cn.xiaomimimo.com/v1",
    defaultModel: "mimo-v2.5-pro",
    models: ["mimo-v2.5-pro", "mimo-v2.5", "mimo-v2-pro", "mimo-v2", "mimo-v1.5-pro", "mimo-v1.5"]
  },
  {
    id: "zhipu",
    name: "智谱 (GLM)",
    baseUrl: "https://open.bigmodel.cn/api/paas/v4",
    defaultModel: "glm-5.1",
    models: ["glm-5.1", "glm-5", "glm-5-air", "glm-5-flash", "glm-4-plus", "glm-4-air", "glm-4-flash", "glm-4v-plus", "codegeex-4-plus"]
  },
  {
    id: "moonshot",
    name: "月之暗面 (Kimi)",
    baseUrl: "https://api.moonshot.cn/v1",
    defaultModel: "kimi-k2",
    models: ["kimi-k2", "kimi-k2-mini", "moonshot-v1-auto", "moonshot-v1-128k", "moonshot-v1-32k"]
  },
  {
    id: "deepseek",
    name: "DeepSeek",
    baseUrl: "https://api.deepseek.com/v1",
    defaultModel: "deepseek-v4-pro",
    models: ["deepseek-v4-pro", "deepseek-v4-flash", "deepseek-v3.2", "deepseek-v3.1", "deepseek-r1", "deepseek-v3"]
  },
  {
    id: "baidu",
    name: "百度 (千帆)",
    baseUrl: "https://qianfan.baidubce.com/v2",
    defaultModel: "ernie-5.1",
    models: ["ernie-5.1", "ernie-5.1-preview", "ernie-4.5-turbo-128k", "ernie-4.5-turbo-32k", "ernie-x1", "deepseek-v4-pro", "deepseek-r1"]
  },
  {
    id: "bytedance",
    name: "字节 (豆包)",
    baseUrl: "https://ark.cn-beijing.volces.com/api/v3",
    defaultModel: "doubao-seed-1-8-251228",
    models: ["doubao-seed-1-8-251228", "doubao-seed-1-6-251015", "doubao-2.0-pro-256k", "doubao-2.0-pro-32k", "doubao-2.0-lite-32k", "doubao-1.5-pro-256k", "doubao-1.5-pro-32k"]
  },
  {
    id: "minimax",
    name: "MiniMax",
    baseUrl: "https://api.minimaxi.com/v1",
    defaultModel: "MiniMax-M2.7",
    models: ["MiniMax-M2.7", "MiniMax-M2.5", "MiniMax-M2.1", "MiniMax-M2", "MiniMax-Text-01"]
  },
  {
    id: "spark",
    name: "讯飞 (星火)",
    baseUrl: "https://spark-api-open.xf-yun.com/v1",
    defaultModel: "spark-5.0-ultra",
    models: ["spark-5.0-ultra", "spark-5.0", "spark-4.0-ultra", "spark-4.0", "spark-max", "spark-pro"]
  },
  {
    id: "yi",
    name: "零一万物 (Yi)",
    baseUrl: "https://api.lingyiwanwu.com/v1",
    defaultModel: "yi-lightning",
    models: ["yi-lightning", "yi-large", "yi-large-turbo", "yi-medium", "yi-spark"]
  },
  {
    id: "anthropic",
    name: "Anthropic (Claude)",
    baseUrl: "https://api.anthropic.com/v1",
    defaultModel: "claude-sonnet-4-20250514",
    models: ["claude-opus-4-20250514", "claude-sonnet-4-20250514", "claude-3-5-haiku-20241022"]
  },
  {
    id: "google",
    name: "Google (Gemini)",
    baseUrl: "https://generativelanguage.googleapis.com/v1beta",
    defaultModel: "gemini-2.5-flash",
    models: ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite"]
  },
  {
    id: "openrouter",
    name: "OpenRouter",
    baseUrl: "https://openrouter.ai/api/v1",
    defaultModel: "anthropic/claude-sonnet-4",
    models: ["anthropic/claude-sonnet-4", "anthropic/claude-opus-4", "google/gemini-2.5-pro", "google/gemini-2.5-flash", "meta-llama/llama-4-maverick", "deepseek/deepseek-r1"]
  },
  {
    id: "custom",
    name: "自定义 (OpenAI兼容)",
    baseUrl: "",
    defaultModel: "",
    models: []
  }
];

interface SettingsPanelProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (config: ModelConfig) => Promise<boolean>;
  currentConfig?: ModelConfig;
  backendConfigured?: boolean;
}

export interface ModelConfig {
  providerId: string;
  apiKey: string;
  baseUrl: string;
  model: string;
  memoryModel?: string;
}

export default function SettingsPanel({
  isOpen,
  onClose,
  onSave,
  currentConfig,
  backendConfigured = false,
}: SettingsPanelProps) {
  const [tab, setTab] = useState<"model" | "integrations">("model");
  const [selectedProvider, setSelectedProvider] = useState<string>(
    currentConfig?.providerId || "dashscope"
  );
  const [apiKey, setApiKey] = useState(currentConfig?.apiKey || "");
  const [baseUrl, setBaseUrl] = useState(currentConfig?.baseUrl || "");
  const [model, setModel] = useState(currentConfig?.model || "");
  const [memoryModel, setMemoryModel] = useState(currentConfig?.memoryModel || "auto");

  const provider = PROVIDERS.find(p => p.id === selectedProvider);

  const handleProviderChange = (providerId: string) => {
    setSelectedProvider(providerId);
    const p = PROVIDERS.find(pr => pr.id === providerId);
    if (p) {
      setBaseUrl(p.baseUrl);
      setModel(p.defaultModel);
    }
  };

  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    try {
      const ok = await onSave({
        providerId: selectedProvider,
        apiKey,
        baseUrl: baseUrl || provider?.baseUrl || "",
        model: model || provider?.defaultModel || "",
        memoryModel: memoryModel || "auto",
      });
      if (ok) onClose();
    } finally {
      setSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <button
        type="button"
        aria-label="关闭配置"
        className="absolute inset-0 bg-black/25"
        onClick={onClose}
      />
      <div className="relative w-full max-w-sm h-full max-h-screen bg-white shadow-2xl flex flex-col border-l border-slate-200">
        <div className="px-4 py-3 border-b border-slate-200 bg-slate-50 flex-shrink-0">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-base font-semibold text-slate-900">设置</h2>
            <button
              type="button"
              onClick={onClose}
              className="w-8 h-8 rounded-lg hover:bg-slate-200 flex items-center justify-center transition-colors"
            >
              <svg className="w-5 h-5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div className="flex gap-1 p-0.5 bg-slate-200/60 rounded-lg">
            <button
              type="button"
              onClick={() => setTab("model")}
              className={`flex-1 text-xs py-1.5 rounded-md font-medium transition-colors ${
                tab === "model" ? "bg-white text-slate-900 shadow-sm" : "text-slate-600"
              }`}
            >
              模型
            </button>
            <button
              type="button"
              onClick={() => setTab("integrations")}
              className={`flex-1 text-xs py-1.5 rounded-md font-medium transition-colors ${
                tab === "integrations" ? "bg-white text-slate-900 shadow-sm" : "text-slate-600"
              }`}
            >
              飞书 / 钉钉
            </button>
          </div>
        </div>

        <div className="p-4 space-y-3 overflow-y-auto flex-1">
          {tab === "integrations" ? (
            <IntegrationsPanel />
          ) : (
          <>
          {backendConfigured && !apiKey.trim() && (
            <p className="text-xs text-green-700 bg-green-50 border border-green-100 rounded-lg px-3 py-2">
              服务端已配置，可直接对话。仅修改模型时 Key 可留空。
            </p>
          )}
          {/* Provider Selection */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              选择厂商
            </label>
            <select
              value={selectedProvider}
              onChange={(e) => handleProviderChange(e.target.value)}
              className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm"
            >
              {PROVIDERS.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>

          {/* API Key */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              API Key
            </label>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="输入你的 API Key"
              className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm placeholder:text-slate-400"
            />
          </div>

          {/* Base URL */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              API 地址
            </label>
            <input
              type="text"
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
              placeholder="API 基础地址"
              className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm placeholder:text-slate-400"
            />
            <p className="text-xs text-slate-400 mt-1">
              选择厂商后自动填入，也可手动修改
            </p>
          </div>

          {/* Model Selection */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              模型
            </label>
            <select
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm"
            >
              {provider?.models.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              记忆模型
            </label>
            <select
              value={memoryModel}
              onChange={(e) => setMemoryModel(e.target.value)}
              className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm"
            >
              <option value="auto">自动（轻量，用于沉淀/召回）</option>
              {provider?.models.map((m) => (
                <option key={`mem-${m}`} value={m}>
                  {m}
                </option>
              ))}
            </select>
            <p className="text-xs text-slate-400 mt-1">
              对话与记忆可分工：记忆提取默认用更轻的模型省成本
            </p>
          </div>

          {/* Info */}
          <div className="bg-blue-50 rounded-xl p-4 border border-blue-100">
            <div className="flex gap-3">
              <svg className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div>
                <p className="text-sm text-blue-700 font-medium">配置说明</p>
                <p className="text-xs text-blue-600 mt-1">
                  选择厂商后，API地址和模型会自动填入。你只需要填写 API Key 即可开始使用。
                </p>
                {selectedProvider === "anthropic" && (
                  <p className="text-xs text-amber-600 mt-1 font-medium">
                    ⚠️ Anthropic Claude 使用专用API格式，需要通过 OpenRouter 等兼容服务接入
                  </p>
                )}
                {selectedProvider === "google" && (
                  <p className="text-xs text-amber-600 mt-1 font-medium">
                    ⚠️ Google Gemini 使用专用API格式，需要通过 OpenRouter 等兼容服务接入
                  </p>
                )}
              </div>
            </div>
          </div>
          </>
          )}
        </div>

        {/* Footer */}
        {tab === "model" && (
        <div className="px-4 py-3 border-t border-slate-200 bg-slate-50 flex justify-end gap-2 flex-shrink-0">
          <button
            onClick={onClose}
            className="px-4 py-2 text-slate-700 hover:bg-slate-200 rounded-lg transition-colors text-sm font-medium"
          >
            取消
          </button>
          <button
            type="button"
            onClick={() => void handleSave()}
            disabled={(!apiKey.trim() && !backendConfigured) || saving}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm font-medium"
          >
            {saving ? "保存中…" : "保存配置"}
          </button>
        </div>
        )}
      </div>
    </div>
  );
}
