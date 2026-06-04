export const DEFAULT_USER_ID = "demo-user";

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
  return fetch(path, { ...init, headers });
}
