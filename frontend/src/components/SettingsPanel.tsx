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
    defaultModel: "gpt-4o",
    models: ["gpt-4o", "gpt-4o-mini", "o1", "o1-mini", "o1-pro", "o3-mini", "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano"]
  },
  {
    id: "dashscope",
    name: "百炼 (阿里云)",
    baseUrl: "https://dashscope.aliyuncs.com/compatible-mode/v1",
    defaultModel: "qwen-max-latest",
    models: ["qwen-max-latest", "qwen-plus-latest", "qwen-turbo-latest", "qwen-long-latest", "qwen2.5-72b-instruct", "qwen2.5-32b-instruct", "qwen2.5-14b-instruct", "qwen2.5-7b-instruct", "qwq-32b"]
  },
  {
    id: "siliconflow",
    name: "硅基流动",
    baseUrl: "https://api.siliconflow.cn/v1",
    defaultModel: "Qwen/Qwen2.5-72B-Instruct",
    models: [
      "Qwen/Qwen2.5-7B-Instruct", "Qwen/Qwen2.5-14B-Instruct", "Qwen/Qwen2.5-32B-Instruct", "Qwen/Qwen2.5-72B-Instruct",
      "deepseek-ai/DeepSeek-V3", "deepseek-ai/DeepSeek-R1",
      "Pro/deepseek-ai/DeepSeek-V3", "Pro/deepseek-ai/DeepSeek-R1",
      "meta-llama/Meta-Llama-3.1-8B-Instruct", "meta-llama/Meta-Llama-3.1-70B-Instruct",
      "internlm/internlm2_5-7b-chat", "THUDM/glm-4-9b-chat"
    ]
  },
  {
    id: "xiaomi",
    name: "小米 (MiLM)",
    baseUrl: "https://api.xiaomi.com/v1",
    defaultModel: "milm-7b",
    models: ["milm-7b", "milm-13b", "milm-65b"]
  },
  {
    id: "zhipu",
    name: "智谱 (GLM)",
    baseUrl: "https://open.bigmodel.cn/api/paas/v4",
    defaultModel: "glm-4-plus",
    models: ["glm-4-plus", "glm-4-0520", "glm-4-air", "glm-4-airx", "glm-4-long", "glm-4-flash", "glm-4-flashx", "glm-4v-plus", "glm-4v", "codegeex-4"]
  },
  {
    id: "moonshot",
    name: "月之暗面 (Kimi)",
    baseUrl: "https://api.moonshot.cn/v1",
    defaultModel: "moonshot-v1-auto",
    models: ["moonshot-v1-auto", "moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"]
  },
  {
    id: "deepseek",
    name: "DeepSeek",
    baseUrl: "https://api.deepseek.com/v1",
    defaultModel: "deepseek-chat",
    models: ["deepseek-chat", "deepseek-reasoner", "deepseek-coder"]
  },
  {
    id: "baidu",
    name: "百度 (文心一言)",
    baseUrl: "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop",
    defaultModel: "ernie-4.0-8k",
    models: ["ernie-4.0-8k", "ernie-4.0-turbo-8k", "ernie-3.5-8k", "ernie-3.5-128k", "ernie-speed-128k", "ernie-lite-8k", "ernie-speed-appbuilder"]
  },
  {
    id: "bytedance",
    name: "字节 (豆包)",
    baseUrl: "https://ark.cn-beijing.volces.com/api/v3",
    defaultModel: "doubao-1.5-pro-256k",
    models: ["doubao-1.5-pro-256k", "doubao-1.5-pro-32k", "doubao-1.5-lite-32k", "doubao-pro-256k", "doubao-pro-32k", "doubao-pro-4k", "doubao-lite-32k", "doubao-lite-4k"]
  },
  {
    id: "minimax",
    name: "MiniMax",
    baseUrl: "https://api.minimax.chat/v1",
    defaultModel: "MiniMax-Text-01",
    models: ["MiniMax-Text-01", "abab7-chat", "abab6.5s-chat", "abab6.5-chat"]
  },
  {
    id: "spark",
    name: "讯飞 (星火)",
    baseUrl: "https://spark-api-open.xf-yun.com/v1",
    defaultModel: "4.0Ultra",
    models: ["4.0Ultra", "generalv3.5", "pro-128k", "generalv3", "max-32k"]
  },
  {
    id: "yi",
    name: "零一万物 (Yi)",
    baseUrl: "https://api.lingyiwanwu.com/v1",
    defaultModel: "yi-large",
    models: ["yi-large", "yi-large-turbo", "yi-medium", "yi-spark", "yi-large-fc", "yi-lightning"]
  },
  {
    id: "anthropic",
    name: "Anthropic (Claude)",
    baseUrl: "https://api.anthropic.com/v1",
    defaultModel: "claude-sonnet-4-20250514",
    models: ["claude-opus-4-20250514", "claude-sonnet-4-20250514", "claude-3-5-haiku-20241022", "claude-3-5-sonnet-20241022", "claude-3-opus-20240229"]
  },
  {
    id: "google",
    name: "Google (Gemini)",
    baseUrl: "https://generativelanguage.googleapis.com/v1beta",
    defaultModel: "gemini-2.0-flash",
    models: ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-1.5-pro", "gemini-1.5-flash"]
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
