export const DEFAULT_USER_ID = "demo-user";

export const API_ORIGIN =
  typeof window !== "undefined"
    ? process.env.NEXT_PUBLIC_API_ORIGIN || "http://localhost:8000"
    : "http://localhost:8000";

export function apiUrl(path: string): string {
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${API_ORIGIN}${p}`;
}

export function streamChatUrl(): string {
  return apiUrl("/api/chat/stream");
}

export function uploadUrl(userId: string): string {
  return `${API_ORIGIN}/api/upload?user_id=${encodeURIComponent(userId)}`;
}

export function uploadRawUrl(userId: string, filename: string): string {
  return `${API_ORIGIN}/api/uploads/${encodeURIComponent(userId)}/${encodeURIComponent(filename)}/raw`;
}

export async function uploadFile(
  file: File,
  userId: string
): Promise<{ filename: string; path: string; size: number }> {
  const form = new FormData();
  form.append("file", file);
  const headers: Record<string, string> = {};
  const apiKey = getSidecarApiKey();
  if (apiKey) headers["X-API-Key"] = apiKey;
  const res = await fetch(uploadUrl(userId), { method: "POST", body: form, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || `上传失败 (${res.status})`);
  }
  return res.json();
}

export function streamChatHeaders(): HeadersInit {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  const apiKey = getSidecarApiKey();
  if (apiKey) headers["X-API-Key"] = apiKey;
  return headers;
}

export interface StoredModelConfig {
  providerId: string;
  apiKey: string;
  baseUrl: string;
  model: string;
}

export function getStoredModelConfig(): StoredModelConfig | null {
  if (typeof window === "undefined") return null;
  const saved = localStorage.getItem("modelConfig");
  if (!saved) return null;
  try {
    const parsed = JSON.parse(saved) as StoredModelConfig;
    if (!parsed.apiKey?.trim()) return null;
    return {
      providerId: parsed.providerId || "custom",
      apiKey: parsed.apiKey.trim(),
      baseUrl: (parsed.baseUrl || "").trim(),
      model: (parsed.model || "").trim(),
    };
  } catch {
    return null;
  }
}

export function resolveModelConfig(
  modelConfig?: StoredModelConfig | null,
  backendConfigured = false
): StoredModelConfig | null {
  if (backendConfigured) {
    if (modelConfig?.baseUrl && modelConfig?.model) {
      return {
        providerId: modelConfig.providerId || "custom",
        apiKey: "",
        baseUrl: modelConfig.baseUrl.trim(),
        model: modelConfig.model.trim(),
      };
    }
    return null;
  }
  const stored = getStoredModelConfig();
  if (stored?.apiKey) return stored;
  if (modelConfig?.apiKey?.trim()) {
    return {
      providerId: modelConfig.providerId || "custom",
      apiKey: modelConfig.apiKey.trim(),
      baseUrl: (modelConfig.baseUrl || "").trim(),
      model: (modelConfig.model || "").trim(),
    };
  }
  return null;
}

export async function saveModelConfig(config: {
  apiKey: string;
  baseUrl: string;
  model: string;
}): Promise<void> {
  const res = await fetch(apiUrl("/api/config"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      api_key: config.apiKey.trim(),
      base_url: config.baseUrl.trim(),
      model: config.model.trim(),
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || "配置保存失败");
  }
}

export async function fetchBackendConfigured(): Promise<boolean> {
  try {
    const res = await fetch(apiUrl("/api/config"));
    const data = await res.json();
    return !!data.configured;
  } catch {
    return false;
  }
}

export function getUserId(): string {
  if (typeof window === "undefined") return DEFAULT_USER_ID;
  return localStorage.getItem("memoryagent_user_id") || DEFAULT_USER_ID;
}

export function setUserId(userId: string): void {
  localStorage.setItem("memoryagent_user_id", userId.trim() || DEFAULT_USER_ID);
}

export function getSidecarApiKey(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("memoryagent_api_key");
}

export function setSidecarApiKey(key: string): void {
  const v = key.trim();
  if (v) localStorage.setItem("memoryagent_api_key", v);
  else localStorage.removeItem("memoryagent_api_key");
}

export async function apiFetch(
  path: string,
  init: RequestInit = {}
): Promise<Response> {
  const headers = new Headers(init.headers);
  if (!headers.has("Content-Type") && init.body) {
    headers.set("Content-Type", "application/json");
  }
  const apiKey = getSidecarApiKey();
  if (apiKey) headers.set("X-API-Key", apiKey);
  const url = path.startsWith("http") ? path : apiUrl(path);
  return fetch(url, { ...init, headers });
}

export interface IntegrationInfo {
  id: string;
  name: string;
  type: string;
  description: string;
  enabled: boolean;
  connected: boolean;
}

export async function listIntegrations(): Promise<IntegrationInfo[]> {
  const res = await apiFetch("/api/integrations");
  if (!res.ok) throw new Error("加载集成列表失败");
  return res.json();
}

export async function connectIntegration(
  integrationId: string,
  credentials: Record<string, string>
): Promise<void> {
  const res = await apiFetch("/api/integrations/connect", {
    method: "POST",
    body: JSON.stringify({ integration_id: integrationId, credentials }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || "连接失败");
  }
}

export async function disconnectIntegration(integrationId: string): Promise<void> {
  const res = await apiFetch(`/api/integrations/${integrationId}/disconnect`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("断开失败");
}

export async function testIntegration(integrationId: string): Promise<void> {
  const res = await apiFetch(`/api/integrations/${integrationId}/test`, {
    method: "POST",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || "测试失败");
  }
}

export async function notifyIntegration(
  integrationId: string,
  message: string
): Promise<void> {
  const res = await apiFetch(`/api/integrations/${integrationId}/notify`, {
    method: "POST",
    body: JSON.stringify({ message }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || "发送失败");
  }
}

export interface SidecarStatus {
  ide_notice?: string;
  updated_at?: string;
  status_file?: string;
  last_recall?: {
    at?: string;
    query?: string;
    count?: number;
    status?: string;
    hints?: string[];
  };
  last_store?: {
    at?: string;
    content?: string;
    stored?: boolean;
    memory_type?: string;
  };
  last_auto_write?: {
    at?: string;
    stored?: number;
    deleted?: number;
  };
}

export async function fetchSidecarStatus(): Promise<SidecarStatus> {
  const res = await apiFetch("/api/sidecar/status");
  if (!res.ok) return {};
  return res.json();
}

export interface SidecarHealthCheck {
  id: string;
  ok: boolean;
  label: string;
  hint?: string;
  optional?: boolean;
}

export interface SidecarHealth {
  scope?: { user_id?: string; project_id?: string; workspace?: string; storage_dir?: string };
  memory_count?: number;
  cursor_ready?: boolean;
  web_ready?: boolean;
  checks?: SidecarHealthCheck[];
  tips?: string[];
  sidecar_status?: SidecarStatus;
}

export async function fetchSidecarHealth(): Promise<SidecarHealth> {
  const res = await apiFetch("/api/sidecar/health");
  if (!res.ok) return {};
  return res.json();
}

export function memoryExportUrl(userId: string, projectId?: string): string {
  const q = new URLSearchParams({ user_id: userId, limit: "50" });
  if (projectId) q.set("project_id", projectId);
  return apiUrl(`/api/memory/export?${q.toString()}`);
}
