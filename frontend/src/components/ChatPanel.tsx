"use client";

import { useState, useEffect, useRef } from "react";
import {
  apiUrl,
  fetchBackendConfigured,
  getUserId,
  resolveModelConfig,
  streamChatUrl,
  streamChatHeaders,
  uploadFile,
  uploadRawUrl,
} from "@/lib/api";
import MarkdownMessage from "@/components/MarkdownMessage";

interface MemoryWrite {
  type: string;
  content: string;
  layer: string;
  action: "stored" | "deleted" | "used";
}

interface MemoryCitation {
  memory_id: string;
  memory_type: string;
  description: string;
  content_snippet: string;
  score: number;
  age_days: number;
  is_stale: boolean;
  selection_reason: string;
  source_quote?: string;
  judge_reason?: string;
}

interface MessageAttachment {
  filename: string;
  kind: "file" | "image";
  path?: string;
}

interface PendingAttachment {
  id: string;
  file: File;
  kind: "file" | "image";
  previewUrl?: string;
}

interface Message {
  id: string;
  content: string;
  role: "user" | "assistant";
  timestamp: Date;
  attachments?: MessageAttachment[];
  metadata?: {
    turns?: number;
    tools_called?: string[];
    memories_used?: string[];
    memory_citations?: MemoryCitation[];
    memory_writes?: MemoryWrite[];
    stop_reason?: string;
  };
}

interface Session {
  session_id: string;
  name?: string;
  message_count: number;
  last_message?: string;
  last_timestamp?: string;
  created_at?: string;
}

interface ModelConfig {
  providerId: string;
  apiKey: string;
  baseUrl: string;
  model: string;
}

interface ChatPanelProps {
  modelConfig?: ModelConfig | null;
  crossSessionMemory?: boolean;
}

const IMAGE_TYPES = new Set(["image/jpeg", "image/png", "image/gif", "image/webp"]);

function formatMessageContent(content: unknown): string {
  if (typeof content === "string") return content;
  if (Array.isArray(content)) {
    return content
      .filter((p) => p && typeof p === "object" && (p as { type?: string }).type === "text")
      .map((p) => (p as { text?: string }).text || "")
      .join("\n");
  }
  return content ? String(content) : "";
}

function isImageFile(file: File): boolean {
  return IMAGE_TYPES.has(file.type) || /\.(jpe?g|png|gif|webp)$/i.test(file.name);
}

export default function ChatPanel({
  modelConfig,
  crossSessionMemory = false,
}: ChatPanelProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [streamingMessageId, setStreamingMessageId] = useState<string | null>(null);
  const [currentSessionId, setCurrentSessionId] = useState("default");
  const [sessions, setSessions] = useState<Session[]>([]);
  const [showSessions, setShowSessions] = useState(true);
  const [showMetadata, setShowMetadata] = useState(true);
  const [pendingAttachments, setPendingAttachments] = useState<PendingAttachment[]>([]);
  const [backendConfigured, setBackendConfigured] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const imageInputRef = useRef<HTMLInputElement | null>(null);
  const sessionBootstrapped = useRef(false);

  const loadSessions = async (): Promise<Session[]> => {
    try {
      const response = await fetch(apiUrl(`/api/sessions?user_id=${encodeURIComponent(getUserId())}`));
      const data = await response.json();
      const list: Session[] = (data.sessions || []).sort(
        (a: Session, b: Session) =>
          (b.last_timestamp || "").localeCompare(a.last_timestamp || "")
      );
      setSessions(list);
      return list;
    } catch (error) {
      console.error("Failed to load sessions:", error);
      return [];
    }
  };

  const refreshBackendConfig = async () => {
    setBackendConfigured(await fetchBackendConfigured());
  };

  useEffect(() => {
    (async () => {
      await refreshBackendConfig();
      const list = await loadSessions();
      if (!sessionBootstrapped.current && list.length > 0) {
        sessionBootstrapped.current = true;
        await switchSession(list[0].session_id);
      }
    })();
    const onConfigSaved = () => { refreshBackendConfig(); };
    window.addEventListener("memory-agent:config-saved", onConfigSaved);
    return () => window.removeEventListener("memory-agent:config-saved", onConfigSaved);
  }, []);

  const deleteSession = async (sessionId: string) => {
    if (!confirm("确定要删除这个会话吗？")) return;
    
    try {
      await fetch(apiUrl(`/api/sessions/${sessionId}?user_id=${encodeURIComponent(getUserId())}`), {
        method: "DELETE",
      });
      
      // 如果删除的是当前会话，创建新会话
      if (sessionId === currentSessionId) {
        createNewSession();
      }
      
      loadSessions();
    } catch (error) {
      console.error("Failed to delete session:", error);
    }
  };

  const clearCurrentChat = () => {
    if (!confirm("确定要清空当前聊天记录吗？")) return;
    setMessages([]);
  };

  const generateSessionName = (firstMessage: string) => {
    const msg = firstMessage.substring(0, 20);
    const now = new Date();
    const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
    return `${msg} - ${timeStr}`;
  };

  const createNewSession = () => {
    const newSessionId = `session-${Date.now()}`;
    setCurrentSessionId(newSessionId);
    setMessages([]);
    setShowSessions(false);
    loadSessions();
  };

  const switchSession = async (sessionId: string) => {
    setCurrentSessionId(sessionId);
    setShowSessions(false);
    
    try {
      const response = await fetch(
        apiUrl(`/api/sessions/${sessionId}/messages?user_id=${encodeURIComponent(getUserId())}`)
      );
      const data = await response.json();
      
      if (data.messages && data.messages.length > 0) {
        const loadedMessages: Message[] = data.messages
          .filter((m: { role?: string }) => m.role === "user" || m.role === "assistant")
          .map((m: {
            content: string | unknown;
            role: string;
            timestamp?: string;
            attachments?: MessageAttachment[];
          }, index: number) => ({
            id: `loaded-${index}`,
            content: formatMessageContent(m.content),
            role: m.role as "user" | "assistant",
            timestamp: new Date(m.timestamp || Date.now()),
            attachments: (m.attachments || []).map((a) => ({
              ...a,
              path: a.path,
            })),
          }));
        setMessages(loadedMessages);
      } else {
        setMessages([]);
      }
    } catch (error) {
      console.error("Failed to load session messages:", error);
      setMessages([]);
    }
  };

  const addFiles = (files: FileList | null, forceKind?: "file" | "image") => {
    if (!files?.length) return;
    const next: PendingAttachment[] = [];
    Array.from(files).forEach((file) => {
      const kind = forceKind || (isImageFile(file) ? "image" : "file");
      next.push({
        id: `${Date.now()}-${file.name}`,
        file,
        kind,
        previewUrl: kind === "image" ? URL.createObjectURL(file) : undefined,
      });
    });
    setPendingAttachments((prev) => [...prev, ...next]);
  };

  const removePendingAttachment = (id: string) => {
    setPendingAttachments((prev) => {
      const target = prev.find((a) => a.id === id);
      if (target?.previewUrl) URL.revokeObjectURL(target.previewUrl);
      return prev.filter((a) => a.id !== id);
    });
  };

  const attachmentUrl = (att: MessageAttachment) =>
    uploadRawUrl(getUserId(), att.filename);

  const renderMessageAttachments = (attachments?: MessageAttachment[]) => {
    if (!attachments?.length) return null;
    return (
      <div className="mt-2 flex flex-wrap gap-2">
        {attachments.map((att) =>
          att.kind === "image" ? (
            <a
              key={att.filename}
              href={attachmentUrl(att)}
              target="_blank"
              rel="noreferrer"
              className="block"
            >
              <img
                src={attachmentUrl(att)}
                alt={att.filename}
                className="max-h-40 rounded-md border border-white/20"
              />
            </a>
          ) : (
            <span
              key={att.filename}
              className="text-[10px] px-2 py-1 rounded bg-black/10"
            >
              📎 {att.filename}
            </span>
          )
        )}
      </div>
    );
  };

  const sendMessage = async () => {
    if (!input.trim() && pendingAttachments.length === 0) return;

    const messageText = input.trim();
    const userId = getUserId();
    let uploadedAttachments: MessageAttachment[] = [];
    try {
      if (pendingAttachments.length > 0) {
        const results = await Promise.all(
          pendingAttachments.map(async (att) => {
            const saved = await uploadFile(att.file, userId);
            return {
              filename: saved.filename,
              path: saved.path,
              kind: att.kind,
            } as MessageAttachment;
          })
        );
        uploadedAttachments = results;
      }
    } catch (error: unknown) {
      const msg = error instanceof Error ? error.message : "上传失败";
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          content: msg,
          role: "assistant",
          timestamp: new Date(),
        },
      ]);
      return;
    }

    pendingAttachments.forEach((a) => {
      if (a.previewUrl) URL.revokeObjectURL(a.previewUrl);
    });
    setPendingAttachments([]);

    const userMessage: Message = {
      id: Date.now().toString(),
      content: messageText || (uploadedAttachments.length ? `[已上传 ${uploadedAttachments.length} 个附件]` : ""),
      role: "user",
      timestamp: new Date(),
      attachments: uploadedAttachments,
    };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    const activeConfig = resolveModelConfig(modelConfig);
    if (!activeConfig?.apiKey?.trim() && !backendConfigured) {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          content: "未配置 AI 模型。请点击左上角「配置」→ 选择厂商（如百炼/硅基流动）→ 填写 API Key → 点击保存。",
          role: "assistant",
          timestamp: new Date(),
        },
      ]);
      setIsLoading(false);
      return;
    }
    const streamTimeout = window.setTimeout(() => abortController.abort(), 120_000);
    const requestBody = {
      message: messageText,
      session_id: currentSessionId,
      user_id: userId,
      cross_session_memory: crossSessionMemory,
      attachments: uploadedAttachments.map((a) => ({
        filename: a.filename,
        path: a.path,
        kind: a.kind,
      })),
      llm_config: activeConfig?.apiKey?.trim() ? {
        api_key: activeConfig.apiKey,
        base_url: activeConfig.baseUrl,
        model: activeConfig.model || "gpt-4o-mini",
      } : null,
    };

    const assistantId = (Date.now() + 1).toString();
    setStreamingMessageId(assistantId);
    let streamedContent = "";
    let displayContent = "";
    const thinkingHint = "正在搜索记忆并生成回复…";
    displayContent = thinkingHint;
    let toolsCalled: string[] = [];
    let memoriesUsed: string[] = [];
    let memoryCitations: MemoryCitation[] = [];
    let memoryWrites: MemoryWrite[] = [];

    setMessages((prev) => [
      ...prev,
      {
        id: assistantId,
        content: thinkingHint,
        role: "assistant",
        timestamp: new Date(),
      },
    ]);

    const applyStreamPayload = (payload: {
      type: string;
      content?: string;
      metadata?: Record<string, unknown>;
    }) => {
      if (payload.type === "token" && payload.content) {
        streamedContent += payload.content;
        displayContent = streamedContent;
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId ? { ...m, content: displayContent } : m
          )
        );
      } else if (payload.type === "error") {
        displayContent = payload.content || displayContent || "请求失败，请稍后重试。";
        streamedContent = displayContent;
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId ? { ...m, content: displayContent } : m
          )
        );
        setIsLoading(false);
      } else if (payload.type === "done") {
        const response = payload.metadata?.response;
        if (typeof response === "string" && response.trim()) {
          if (!streamedContent || streamedContent === thinkingHint) {
            streamedContent = response;
          }
          displayContent = streamedContent;
        }
        if (displayContent && displayContent !== thinkingHint) {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId ? { ...m, content: displayContent } : m
            )
          );
        }
        setIsLoading(false);
      } else if (
        payload.type === "tool_call"
        && payload.content
        && !streamedContent.trim()
      ) {
        displayContent = `正在调用 ${payload.content}…`;
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId ? { ...m, content: displayContent } : m
          )
        );
      } else if (
        payload.type === "tool_result"
        && payload.metadata?.source === "status"
        && payload.content
        && !streamedContent.trim()
      ) {
        displayContent = payload.content as string;
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId ? { ...m, content: displayContent } : m
          )
        );
      } else if (payload.type === "tool_result" && payload.metadata?.citation) {
        memoryCitations.push(payload.metadata.citation as MemoryCitation);
        memoriesUsed.push(
          (payload.metadata.citation as MemoryCitation).content_snippet
        );
      } else if (payload.type === "tool_result" && payload.metadata?.source === "memory") {
        memoriesUsed.push(payload.content || "");
      } else if (payload.type === "tool_result" && payload.metadata?.tool_name) {
        toolsCalled.push(payload.metadata.tool_name as string);
      } else if (
        (payload.type === "done" || payload.type === "memory_writes")
        && payload.metadata?.memory_writes
      ) {
        memoryWrites = payload.metadata.memory_writes as MemoryWrite[];
      }
    };

    const parseSseBuffer = (raw: string) => {
      const parts = raw.split("\n\n");
      const rest = parts.pop() || "";
      for (const part of parts) {
        const line = part.trim();
        if (!line.startsWith("data:")) continue;
        try {
          applyStreamPayload(JSON.parse(line.replace(/^data:\s*/, "")));
        } catch {
          /* ignore malformed SSE chunks */
        }
      }
      return rest;
    };

    try {
      const streamResponse = await fetch(streamChatUrl(), {
        method: "POST",
        headers: streamChatHeaders(),
        body: JSON.stringify(requestBody),
        signal: abortController.signal,
      });

      if (streamResponse.ok && streamResponse.body) {
        const reader = streamResponse.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (value) {
            buffer += decoder.decode(value, { stream: true });
            buffer = parseSseBuffer(buffer);
          }
          if (done) break;
        }
        if (buffer.trim()) {
          parseSseBuffer(`${buffer}\n\n`);
        }

        const hasReply = Boolean(
          (streamedContent && streamedContent !== thinkingHint)
          || (displayContent && displayContent !== thinkingHint)
        );
        const fallbackContent = toolsCalled.length > 0
          ? "工具已执行，但模型未返回最终文字，请重试。"
          : "未收到回复，请检查左上角模型配置或稍后重试。";
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? {
                  ...m,
                  content: hasReply
                    ? (streamedContent && streamedContent !== thinkingHint
                        ? streamedContent
                        : displayContent)
                    : fallbackContent,
                  metadata: {
                    tools_called: toolsCalled,
                    memories_used: memoriesUsed,
                    memory_citations: memoryCitations,
                    memory_writes: memoryWrites,
                    stop_reason: "end_turn",
                  },
                }
              : m
          )
        );
        if (memoryWrites.length > 0) {
          window.dispatchEvent(new CustomEvent("memory-agent:writes"));
        }
        loadSessions();
        return;
      }

      if (!streamResponse.ok) {
        let errMsg = `请求失败 (${streamResponse.status})`;
        try {
          const errBody = await streamResponse.json();
          if (typeof errBody.detail === "string") {
            errMsg = errBody.detail;
          }
        } catch {
          /* ignore */
        }
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId ? { ...m, content: errMsg } : m
          )
        );
        return;
      }

      const response = await fetch(apiUrl("/api/chat"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody),
        signal: abortController.signal,
      });

      const data = await response.json();

      const assistantMessage: Message = {
        id: assistantId,
        content: data.response,
        role: "assistant",
        timestamp: new Date(),
        metadata: {
          turns: data.decision_explanation?.confidence > 0 ? 1 : 0,
          tools_called: [],
          memories_used: data.memory_citations?.map((c: MemoryCitation) => c.content_snippet)
            || data.memory_updates?.map((m: any) => m.content) || [],
          memory_citations: data.memory_citations || [],
          memory_writes: (data.memory_updates || []).filter(
            (m: MemoryWrite) => m.action === "stored" || m.action === "deleted"
          ),
          stop_reason: data.decision_explanation?.action || "end_turn",
        }
      };

      setMessages((prev) => [...prev, assistantMessage]);
      if (assistantMessage.metadata?.memory_writes?.length) {
        window.dispatchEvent(new CustomEvent("memory-agent:writes"));
      }
    } catch (error: any) {
      if (error.name === "AbortError") {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? { ...m, content: streamedContent || "（已终止回复）" }
              : m
          )
        );
      } else {
        console.error("Failed to send message:", error);
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? {
                  ...m,
                  content: "连接失败，请确认后端已启动（端口 8000）并重试。",
                }
              : m
          )
        );
      }
    } finally {
      window.clearTimeout(streamTimeout);
      setIsLoading(false);
      setStreamingMessageId(null);
      abortControllerRef.current = null;
    }
  };

  const stopGeneration = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  };

  const renderMetadata = (metadata: NonNullable<Message["metadata"]>) => {
    if (!showMetadata) return null;

    return (
      <div className="mt-2 pt-2 border-t border-slate-200/50">
        <div className="flex flex-wrap gap-1.5">
          {metadata.stop_reason && (
            <span className="text-[10px] px-1.5 py-0.5 bg-slate-200 rounded text-slate-600">
              {metadata.stop_reason}
            </span>
          )}
          {metadata.turns && metadata.turns > 1 && (
            <span className="text-[10px] px-1.5 py-0.5 bg-blue-100 rounded text-blue-700">
              {metadata.turns} 轮对话
            </span>
          )}
          {metadata.tools_called && metadata.tools_called.length > 0 && (
            <span className="text-[10px] px-1.5 py-0.5 bg-green-100 rounded text-green-700">
              使用工具: {metadata.tools_called.join(", ")}
            </span>
          )}
          {metadata.memory_citations && metadata.memory_citations.length > 0 ? (
            <span className="text-[10px] px-1.5 py-0.5 bg-purple-100 rounded text-purple-700">
              使用 {metadata.memory_citations.length} 条记忆
            </span>
          ) : metadata.memories_used && metadata.memories_used.length > 0 ? (
            <span className="text-[10px] px-1.5 py-0.5 bg-purple-100 rounded text-purple-700">
              使用 {metadata.memories_used.length} 条记忆
            </span>
          ) : (
            <span className="text-[10px] px-1.5 py-0.5 bg-slate-100 rounded text-slate-500">
              未命中记忆
            </span>
          )}
          {metadata.memory_writes?.filter((w) => w.action === "stored").length ? (
            <span className="text-[10px] px-1.5 py-0.5 bg-emerald-100 rounded text-emerald-700">
              沉淀 {metadata.memory_writes.filter((w) => w.action === "stored").length} 条
            </span>
          ) : null}
          {metadata.memory_writes?.filter((w) => w.action === "deleted").length ? (
            <span className="text-[10px] px-1.5 py-0.5 bg-rose-100 rounded text-rose-700">
              删除 {metadata.memory_writes.filter((w) => w.action === "deleted").length} 条
            </span>
          ) : null}
        </div>
        {metadata.memory_writes && metadata.memory_writes.length > 0 && (
          <details className="mt-2 text-[10px] text-slate-600">
            <summary className="cursor-pointer text-emerald-700 font-medium">
              查看记忆变更
            </summary>
            <ul className="mt-1 space-y-1 pl-1">
              {metadata.memory_writes.map((w, i) => (
                <li key={`${w.action}-${i}`} className="line-clamp-2">
                  {w.action === "deleted" ? "删除" : "沉淀"}: {w.content}
                </li>
              ))}
            </ul>
          </details>
        )}
        {metadata.memory_citations && metadata.memory_citations.length > 0 && (
          <details className="mt-2 text-[10px] text-slate-600">
            <summary className="cursor-pointer text-purple-700 font-medium">
              查看记忆引用
            </summary>
            <ul className="mt-1 space-y-1.5 pl-1">
              {metadata.memory_citations.map((c) => (
                <li key={c.memory_id} className="bg-purple-50 rounded p-1.5 border border-purple-100">
                  <div className="flex justify-between gap-1">
                    <span className="font-medium">{c.description || c.memory_id}</span>
                    <span className="text-slate-400">{c.score.toFixed(2)}</span>
                  </div>
                  <div className="text-slate-500">{c.memory_type} · {c.selection_reason}</div>
                  <div className="mt-0.5 line-clamp-2">{c.content_snippet}</div>
                  {c.source_quote && (
                    <div className="text-slate-500 mt-0.5">原话: {c.source_quote}</div>
                  )}
                  {c.judge_reason && (
                    <div className="text-slate-400 mt-0.5">裁判: {c.judge_reason}</div>
                  )}
                  {c.is_stale && (
                    <div className="text-amber-600 mt-0.5">陈旧 {c.age_days} 天</div>
                  )}
                </li>
              ))}
            </ul>
          </details>
        )}
      </div>
    );
  };

  return (
    <div className="flex flex-1 overflow-hidden">
      {/* Session Sidebar */}
      {showSessions && (
        <div className="w-56 border-r border-slate-200 bg-white flex flex-col flex-shrink-0">
          <div className="p-3 border-b border-slate-100">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-xs font-semibold text-slate-700">会话列表</h3>
              <button
                onClick={() => setShowSessions(false)}
                className="w-5 h-5 rounded hover:bg-slate-100 flex items-center justify-center"
              >
                <svg className="w-3.5 h-3.5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <button
              onClick={createNewSession}
              className="w-full px-2 py-1.5 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors text-[11px] font-medium"
            >
              + 新建会话
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-1.5">
            {sessions.length === 0 ? (
              <p className="text-[11px] text-slate-400 text-center py-4">暂无会话</p>
            ) : (
              sessions.map((session) => (
                <div
                  key={session.session_id}
                  className={`group relative px-2 py-1.5 rounded-md mb-1 transition-colors ${
                    currentSessionId === session.session_id
                      ? "bg-indigo-50 text-indigo-700"
                      : "hover:bg-slate-50 text-slate-600"
                  }`}
                >
                  <button
                    onClick={() => switchSession(session.session_id)}
                    className="w-full text-left"
                  >
                    <p className="text-[11px] font-medium truncate">{session.name || session.session_id}</p>
                    <div className="flex items-center justify-between">
                      <p className="text-[10px] text-slate-400">{session.message_count} 条消息</p>
                      {session.last_timestamp && (
                        <p className="text-[10px] text-slate-400">
                          {new Date(session.last_timestamp).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })}
                        </p>
                      )}
                    </div>
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteSession(session.session_id);
                    }}
                    className="absolute right-1 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 w-5 h-5 rounded hover:bg-red-100 flex items-center justify-center transition-opacity"
                    title="删除会话"
                  >
                    <svg className="w-3 h-3 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col bg-white">
        {/* Header */}
        <div className="px-4 py-2 border-b border-slate-200 flex items-center justify-between flex-shrink-0">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowSessions(!showSessions)}
              className="w-7 h-7 rounded-md hover:bg-slate-100 flex items-center justify-center transition-colors"
            >
              <svg className="w-4 h-4 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <h2 className="text-sm font-semibold text-slate-800">智能对话</h2>
            <span className="text-[10px] text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded">{currentSessionId}</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={clearCurrentChat}
              className="text-[10px] px-2 py-1 rounded transition-colors bg-slate-100 text-slate-500 hover:bg-red-100 hover:text-red-600"
              title="清空聊天记录"
            >
              清空
            </button>
            <button
              onClick={() => setShowMetadata(!showMetadata)}
              className={`text-[10px] px-2 py-1 rounded transition-colors ${
                showMetadata 
                  ? "bg-indigo-100 text-indigo-700" 
                  : "bg-slate-100 text-slate-500"
              }`}
            >
              {showMetadata ? "隐藏元数据" : "显示元数据"}
            </button>
            <span className="w-1.5 h-1.5 bg-green-500 rounded-full"></span>
            <span className="text-[10px] text-slate-400">在线</span>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-slate-400">
              <div className="w-12 h-12 bg-slate-100 rounded-xl flex items-center justify-center mb-3">
                <svg className="w-6 h-6 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
                </svg>
              </div>
              <p className="text-xs font-medium text-slate-500">开始对话</p>
              <p className="text-[10px] text-slate-400 mt-0.5">输入需要长期记住的项目信息或规则，发送后可在左侧查看沉淀结果。</p>
            </div>
          )}
          
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[75%] px-3 py-2 rounded-xl ${
                  message.role === "user"
                    ? "bg-indigo-600 text-white rounded-br-sm"
                    : "bg-slate-100 text-slate-800 rounded-bl-sm"
                }`}
              >
                {message.role === "assistant" ? (
                  <MarkdownMessage content={message.content} />
                ) : (
                  <p className="text-[13px] leading-relaxed whitespace-pre-wrap">
                    {message.content}
                  </p>
                )}
                {streamingMessageId === message.id && isLoading && (
                  <span className="inline-block w-0.5 h-3.5 ml-0.5 bg-indigo-500 animate-pulse align-middle" />
                )}
                {renderMessageAttachments(message.attachments)}
                <p className={`text-[10px] mt-1 ${message.role === "user" ? "text-indigo-200" : "text-slate-400"}`}>
                  {message.timestamp.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" })}
                </p>
                {message.metadata && renderMetadata(message.metadata)}
              </div>
            </div>
          ))}
          
          {isLoading && streamingMessageId === null && (
            <div className="flex justify-start">
              <div className="bg-slate-100 px-3 py-2 rounded-xl rounded-bl-sm">
                <div className="flex items-center gap-1.5">
                  <div className="flex space-x-1">
                    <div className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                    <div className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                    <div className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                  </div>
                  <span className="text-[11px] text-slate-500">思考中...</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Input */}
        <div className="p-3 border-t border-slate-200 flex-shrink-0">
          {pendingAttachments.length > 0 && (
            <div className="mb-2 flex flex-wrap gap-2">
              {pendingAttachments.map((att) => (
                <div
                  key={att.id}
                  className="relative flex items-center gap-2 px-2 py-1 bg-slate-100 rounded-lg text-[11px] text-slate-600"
                >
                  {att.kind === "image" && att.previewUrl ? (
                    <img src={att.previewUrl} alt={att.file.name} className="h-10 w-10 object-cover rounded" />
                  ) : (
                    <span>📎 {att.file.name}</span>
                  )}
                  <button
                    type="button"
                    onClick={() => removePendingAttachment(att.id)}
                    className="text-slate-400 hover:text-red-500"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          )}
          <input
            ref={fileInputRef}
            type="file"
            className="hidden"
            multiple
            accept=".txt,.md,.py,.js,.json,.csv,.html,.css"
            onChange={(e) => {
              addFiles(e.target.files, "file");
              e.target.value = "";
            }}
          />
          <input
            ref={imageInputRef}
            type="file"
            className="hidden"
            multiple
            accept="image/jpeg,image/png,image/gif,image/webp"
            onChange={(e) => {
              addFiles(e.target.files, "image");
              e.target.value = "";
            }}
          />
          <div className="flex gap-2 items-end">
            <div className="flex flex-col gap-1 flex-shrink-0">
              <button
                type="button"
                onClick={() => imageInputRef.current?.click()}
                disabled={isLoading}
                className="w-8 h-8 rounded-lg border border-slate-200 hover:bg-slate-50 flex items-center justify-center text-slate-500"
                title="上传图片"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </button>
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={isLoading}
                className="w-8 h-8 rounded-lg border border-slate-200 hover:bg-slate-50 flex items-center justify-center text-slate-500"
                title="上传文件"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                </svg>
              </button>
            </div>
            <textarea
              value={input}
              onChange={(e) => {
                setInput(e.target.value);
                e.target.style.height = "auto";
                e.target.style.height = Math.min(e.target.scrollHeight, 150) + "px";
              }}
              onKeyDown={(e) => {
                // 忽略中文输入法的 Enter（确认输入）
                if (e.nativeEvent.isComposing) return;
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  if (!isLoading) {
                    sendMessage();
                  }
                }
              }}
              placeholder="输入消息... (Shift+Enter 换行)"
              rows={1}
              className="flex-1 px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all text-[13px] placeholder:text-slate-400 resize-none overflow-y-auto"
              style={{ minHeight: "40px", maxHeight: "150px" }}
              disabled={isLoading}
            />
            {isLoading ? (
              <button
                onClick={stopGeneration}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-[13px] font-medium flex items-center gap-1.5 flex-shrink-0"
              >
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
                </svg>
                终止
              </button>
            ) : (
              <button
                onClick={sendMessage}
                disabled={!input.trim() && pendingAttachments.length === 0}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-[13px] font-medium flex items-center gap-1.5 flex-shrink-0"
              >
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
                发送
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
