"use client";

import { useState } from "react";

interface ModelProvider {
  id: string;
  name: string;
  baseUrl: string;
  defaultModel: string;
  models: string[];
}

const PROVIDERS: ModelProvider[] = [
  {
    id: "openai",
    name: "OpenAI",
    baseUrl: "https://api.openai.com/v1",
    defaultModel: "gpt-4",
    models: ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"]
  },
  {
    id: "dashscope",
    name: "百炼 (阿里云)",
    baseUrl: "https://dashscope.aliyuncs.com/compatible-mode/v1",
    defaultModel: "qwen-turbo",
    models: ["qwen-turbo", "qwen-plus", "qwen-max", "qwen-long"]
  },
  {
    id: "siliconflow",
    name: "硅基流动",
    baseUrl: "https://api.siliconflow.cn/v1",
    defaultModel: "Qwen/Qwen2-7B-Instruct",
    models: ["Qwen/Qwen2-7B-Instruct", "Qwen/Qwen2-72B-Instruct", "deepseek-ai/DeepSeek-V2-Chat"]
  },
  {
    id: "xiaomi",
    name: "小米 (MiLM)",
    baseUrl: "https://api.xiaomi.com/v1",
    defaultModel: "milm-6b",
    models: ["milm-6b", "milm-13b"]
  },
  {
    id: "zhipu",
    name: "智谱 (GLM)",
    baseUrl: "https://open.bigmodel.cn/api/paas/v4",
    defaultModel: "glm-4",
    models: ["glm-4", "glm-4-flash", "glm-3-turbo"]
  },
  {
    id: "moonshot",
    name: "月之暗面 (Kimi)",
    baseUrl: "https://api.moonshot.cn/v1",
    defaultModel: "moonshot-v1-8k",
    models: ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"]
  },
  {
    id: "deepseek",
    name: "DeepSeek",
    baseUrl: "https://api.deepseek.com/v1",
    defaultModel: "deepseek-chat",
    models: ["deepseek-chat", "deepseek-coder"]
  }
];

interface SettingsPanelProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (config: ModelConfig) => void;
  currentConfig?: ModelConfig;
}

export interface ModelConfig {
  providerId: string;
  apiKey: string;
  baseUrl: string;
  model: string;
}

export default function SettingsPanel({ isOpen, onClose, onSave, currentConfig }: SettingsPanelProps) {
  const [selectedProvider, setSelectedProvider] = useState<string>(
    currentConfig?.providerId || "dashscope"
  );
  const [apiKey, setApiKey] = useState(currentConfig?.apiKey || "");
  const [baseUrl, setBaseUrl] = useState(currentConfig?.baseUrl || "");
  const [model, setModel] = useState(currentConfig?.model || "");

  const provider = PROVIDERS.find(p => p.id === selectedProvider);

  const handleProviderChange = (providerId: string) => {
    setSelectedProvider(providerId);
    const p = PROVIDERS.find(pr => pr.id === providerId);
    if (p) {
      setBaseUrl(p.baseUrl);
      setModel(p.defaultModel);
    }
  };

  const handleSave = () => {
    onSave({
      providerId: selectedProvider,
      apiKey,
      baseUrl: baseUrl || provider?.baseUrl || "",
      model: model || provider?.defaultModel || ""
    });
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl w-full max-w-lg mx-4 overflow-hidden shadow-xl">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-200 bg-slate-50">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">模型配置</h2>
            <button
              onClick={onClose}
              className="w-8 h-8 rounded-lg hover:bg-slate-200 flex items-center justify-center transition-colors"
            >
              <svg className="w-5 h-5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-5">
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
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-200 bg-slate-50 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-slate-700 hover:bg-slate-200 rounded-lg transition-colors text-sm font-medium"
          >
            取消
          </button>
          <button
            onClick={handleSave}
            disabled={!apiKey.trim()}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm font-medium"
          >
            保存配置
          </button>
        </div>
      </div>
    </div>
  );
}
