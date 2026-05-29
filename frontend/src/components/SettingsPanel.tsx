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
    defaultModel: "gpt-5.5",
    models: ["gpt-5.5", "gpt-5.5-mini", "gpt-5.5-nano", "gpt-5", "gpt-5-mini", "o3", "o3-mini", "o3-pro", "o4-mini", "gpt-4.1", "gpt-4.1-mini"]
  },
  {
    id: "dashscope",
    name: "百炼 (阿里云)",
    baseUrl: "https://dashscope.aliyuncs.com/compatible-mode/v1",
    defaultModel: "qwen3.7-max",
    models: ["qwen3.7-max", "qwen3.7-plus", "qwen3.7-turbo", "qwen3.7-lite", "qwen3-235b-a22b", "qwen3-32b", "qwen3-14b", "qwen3-8b", "qwq-32b", "qwen2.5-72b-instruct"]
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
    baseUrl: "https://api.xiaomi.com/v1",
    defaultModel: "mimo-v2.5-pro",
    models: ["mimo-v2.5-pro", "mimo-v2.5", "mimo-v2-pro", "mimo-v2", "mimo-v1.5-pro", "mimo-v1.5"]
  },
  {
    id: "zhipu",
    name: "智谱 (GLM)",
    baseUrl: "https://open.bigmodel.cn/api/paas/v4",
    defaultModel: "glm-5-plus",
    models: ["glm-5-plus", "glm-5", "glm-5-air", "glm-5-flash", "glm-4-plus", "glm-4-air", "glm-4-flash", "glm-4v-plus", "codegeex-4-plus"]
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
    defaultModel: "deepseek-r1-0528",
    models: ["deepseek-r1-0528", "deepseek-v3-0324", "deepseek-r1", "deepseek-v3", "deepseek-coder-v2"]
  },
  {
    id: "baidu",
    name: "百度 (文心一言)",
    baseUrl: "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop",
    defaultModel: "ernie-5.0",
    models: ["ernie-5.0", "ernie-5.0-lite", "ernie-4.5-8k", "ernie-4.5-turbo-8k", "ernie-4.0-8k", "ernie-4.0-turbo-8k", "ernie-x1"]
  },
  {
    id: "bytedance",
    name: "字节 (豆包)",
    baseUrl: "https://ark.cn-beijing.volces.com/api/v3",
    defaultModel: "doubao-2.0-pro-256k",
    models: ["doubao-2.0-pro-256k", "doubao-2.0-pro-32k", "doubao-2.0-lite-32k", "doubao-1.5-pro-256k", "doubao-1.5-pro-32k", "doubao-1.5-lite-32k"]
  },
  {
    id: "minimax",
    name: "MiniMax",
    baseUrl: "https://api.minimax.chat/v1",
    defaultModel: "MiniMax-M1",
    models: ["MiniMax-M1", "MiniMax-M1-mini", "MiniMax-Text-01", "abab7-chat"]
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
    defaultModel: "yi-3.5-large",
    models: ["yi-3.5-large", "yi-3.5-medium", "yi-3.5-light", "yi-large", "yi-large-turbo", "yi-lightning"]
  },
  {
    id: "anthropic",
    name: "Anthropic (Claude)",
    baseUrl: "https://api.anthropic.com/v1",
    defaultModel: "claude-opus-4-20250514",
    models: ["claude-opus-4-20250514", "claude-sonnet-4-20250514", "claude-3-5-haiku-20241022"]
  },
  {
    id: "google",
    name: "Google (Gemini)",
    baseUrl: "https://generativelanguage.googleapis.com/v1beta",
    defaultModel: "gemini-2.5-pro",
    models: ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.5-pro-preview", "gemini-2.0-flash", "gemini-2.0-flash-lite"]
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
