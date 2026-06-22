"use client";

import { useState, useEffect } from "react";
import {
  connectIntegration,
  disconnectIntegration,
  listIntegrations,
  testIntegration,
  type IntegrationInfo,
} from "@/lib/api";

const CHAT_IDS = new Set(["feishu", "dingtalk"]);

export default function IntegrationsPanel() {
  const [items, setItems] = useState<IntegrationInfo[]>([]);
  const [webhookUrl, setWebhookUrl] = useState<Record<string, string>>({});
  const [secret, setSecret] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = async () => {
    try {
      const data = await listIntegrations();
      setItems(data.filter((i) => CHAT_IDS.has(i.id)));
    } catch (e) {
      setError(e instanceof Error ? e.message : "加载失败");
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  const handleConnect = async (id: string) => {
    const url = (webhookUrl[id] || "").trim();
    if (!url.startsWith("http")) {
      setError("请填写 Webhook 地址");
      return;
    }
    setBusy(id);
    setError(null);
    try {
      await connectIntegration(id, {
        webhook_url: url,
        secret: (secret[id] || "").trim(),
      });
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "连接失败");
    } finally {
      setBusy(null);
    }
  };

  const handleDisconnect = async (id: string) => {
    setBusy(id);
    try {
      await disconnectIntegration(id);
      await refresh();
    } finally {
      setBusy(null);
    }
  };

  const handleTest = async (id: string) => {
    setBusy(`${id}-test`);
    try {
      await testIntegration(id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "测试失败");
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-500">绑定群机器人后，重要记忆变更会推送到群聊。</p>
      {error && <p className="text-xs text-red-600">{error}</p>}
      {items.map((item) => (
        <div key={item.id} className="rounded-xl border border-slate-100 p-3 space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium text-slate-800">{item.name}</span>
            <span className="text-xs text-slate-400">{item.connected ? "已连接" : "未连接"}</span>
          </div>
          {!item.connected && (
            <>
              <input
                type="url"
                value={webhookUrl[item.id] || ""}
                onChange={(e) => setWebhookUrl((s) => ({ ...s, [item.id]: e.target.value }))}
                placeholder="Webhook 地址"
                className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg"
              />
              <input
                type="password"
                value={secret[item.id] || ""}
                onChange={(e) => setSecret((s) => ({ ...s, [item.id]: e.target.value }))}
                placeholder="签名密钥（可选）"
                className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg"
              />
            </>
          )}
          <div className="flex gap-2">
            {item.connected ? (
              <>
                <button
                  type="button"
                  disabled={!!busy}
                  onClick={() => handleTest(item.id)}
                  className="flex-1 text-sm py-2 rounded-lg bg-indigo-600 text-white"
                >
                  测试
                </button>
                <button
                  type="button"
                  disabled={!!busy}
                  onClick={() => handleDisconnect(item.id)}
                  className="text-sm py-2 px-3 rounded-lg border border-slate-200"
                >
                  断开
                </button>
              </>
            ) : (
              <button
                type="button"
                disabled={!!busy}
                onClick={() => handleConnect(item.id)}
                className="w-full text-sm py-2 rounded-lg bg-indigo-600 text-white"
              >
                连接
              </button>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
