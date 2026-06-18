"use client";

import { useCallback, useEffect, useState } from "react";
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
  const [inboundToken, setInboundToken] = useState<Record<string, string>>({});
  const [verificationToken, setVerificationToken] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const data = await listIntegrations();
      setItems(data.filter((i) => CHAT_IDS.has(i.id)));
    } catch (e) {
      setError(e instanceof Error ? e.message : "加载失败");
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const handleConnect = async (id: string) => {
    const url = (webhookUrl[id] || "").trim();
    if (!url.startsWith("http")) {
      setError("请填写有效的 Webhook 地址");
      return;
    }
    setBusy(id);
    setError(null);
    try {
      await connectIntegration(id, {
        webhook_url: url,
        secret: (secret[id] || "").trim(),
        inbound_token: (inboundToken[id] || "").trim(),
        verification_token: (verificationToken[id] || "").trim(),
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
    setError(null);
    try {
      await disconnectIntegration(id);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "断开失败");
    } finally {
      setBusy(null);
    }
  };

  const handleTest = async (id: string) => {
    setBusy(`${id}-test`);
    setError(null);
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
      <p className="text-xs text-slate-500 leading-relaxed">
        飞书 / 钉钉：出站通知 + 入站对话。保存 Webhook 后，将事件回调指向下方入站地址。
      </p>
      <div className="text-[10px] text-slate-500 bg-slate-50 border border-slate-100 rounded-lg px-3 py-2 space-y-1">
        <p>入站回调（需公网或内网穿透）：</p>
        <p className="font-mono text-indigo-700">POST /api/webhooks/feishu</p>
        <p className="font-mono text-indigo-700">POST /api/webhooks/dingtalk</p>
        <p className="pt-1">可选 ?token= 与环境变量 MEMORYAGENT_WEBHOOK_INBOUND_TOKEN 一致</p>
      </div>
      {error && (
        <p className="text-xs text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2">
          {error}
        </p>
      )}
      {items.map((item) => (
        <div
          key={item.id}
          className="border border-slate-200 rounded-xl p-3 space-y-2 bg-slate-50/50"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-800">{item.name}</p>
              <p className="text-[10px] text-slate-400">{item.description}</p>
            </div>
            {item.connected ? (
              <span className="text-[10px] text-green-700 bg-green-50 px-2 py-0.5 rounded-full">
                已连接
              </span>
            ) : (
              <span className="text-[10px] text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full">
                未连接
              </span>
            )}
          </div>
          {!item.connected && (
            <>
              <input
                type="url"
                value={webhookUrl[item.id] || ""}
                onChange={(e) =>
                  setWebhookUrl((s) => ({ ...s, [item.id]: e.target.value }))
                }
                placeholder="Webhook 地址"
                className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg"
              />
              <input
                type="password"
                value={secret[item.id] || ""}
                onChange={(e) =>
                  setSecret((s) => ({ ...s, [item.id]: e.target.value }))
                }
                placeholder="出站签名密钥（可选）"
                className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg"
              />
              <input
                type="password"
                value={inboundToken[item.id] || ""}
                onChange={(e) =>
                  setInboundToken((s) => ({ ...s, [item.id]: e.target.value }))
                }
                placeholder="入站 token（可选）"
                className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg"
              />
              {item.id === "feishu" && (
                <input
                  type="password"
                  value={verificationToken[item.id] || ""}
                  onChange={(e) =>
                    setVerificationToken((s) => ({ ...s, [item.id]: e.target.value }))
                  }
                  placeholder="飞书 Verification Token（可选）"
                  className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg"
                />
              )}
            </>
          )}
          <div className="flex gap-2">
            {item.connected ? (
              <>
                <button
                  type="button"
                  disabled={busy !== null}
                  onClick={() => handleTest(item.id)}
                  className="flex-1 text-xs py-2 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50"
                >
                  {busy === `${item.id}-test` ? "测试中…" : "发送测试"}
                </button>
                <button
                  type="button"
                  disabled={busy !== null}
                  onClick={() => handleDisconnect(item.id)}
                  className="text-xs py-2 px-3 rounded-lg border border-slate-200 text-slate-600 hover:bg-white disabled:opacity-50"
                >
                  断开
                </button>
              </>
            ) : (
              <button
                type="button"
                disabled={busy !== null}
                onClick={() => handleConnect(item.id)}
                className="w-full text-xs py-2 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50"
              >
                {busy === item.id ? "连接中…" : "保存并连接"}
              </button>
            )}
          </div>
        </div>
      ))}
      <p className="text-[10px] text-slate-400">
        出站：POST /api/integrations/&#123;feishu|dingtalk&#125;/notify ·
        入站测试：POST /api/webhooks/&#123;feishu|dingtalk&#125;/test-inbound
      </p>
    </div>
  );
}
