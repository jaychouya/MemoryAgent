"use client";

import { useState, useEffect, useRef } from "react";
import { getUserId } from "@/lib/api";

interface MemoryCitation {
  memory_id: string;
  memory_type: string;
  description: string;
  content_snippet: string;
  score: number;
  age_days: number;
  is_stale: boolean;
  selection_reason: string;
}

interface Message {
  id: string;
  content: string;
  role: "user" | "assistant";
  timestamp: Date;
  metadata?: {
    turns?: number;
    tools_called?: string[];
    memories_used?: string[];
    memory_citations?: MemoryCitation[];
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
}

export default function ChatPanel({ modelConfig }: ChatPanelProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState("default");
  const [sessions, setSessions] = useState<Session[]>([]);
  const [showSessions, setShowSessions] = useState(false);
  const [showMetadata, setShowMetadata] = useState(true);
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    try {
      const response = await fetch(`/api/sessions?user_id=${encodeURIComponent(getUserId())}`);
      const data = await response.json();
      setSessions(data.sessions || []);
    } catch (error) {
      console.error("Failed to load sessions:", error);
    }
  };

  const deleteSession = async (sessionId: string) => {
    if (!confirm("确定要删除这个会话吗？")) return;
    
    try {
      await fetch(`/api/sessions/${sessionId}?user_id=${encodeURIComponent(getUserId())}`, {
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
        `/api/sessions/${sessionId}/messages?user_id=${encodeURIComponent(getUserId())}`
      );
      const data = await response.json();
      
      if (data.messages && data.messages.length > 0) {
        const loadedMessages: Message[] = data.messages.map((m: any, index: number) => ({
          id: `loaded-${index}`,
          content: m.content,
          role: m.role as "user" | "assistant",
          timestamp: new Date(m.timestamp || Date.now()),
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

  const sendMessage = async () => {
    if (!input.trim()) return;

    const messageText = input.trim();
    const userMessage: Message = {
      id: Date.now().toString(),
      content: messageText,
      role: "user",
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    const requestBody = {
      message: messageText,
      session_id: currentSessionId,
      user_id: getUserId(),
      llm_config: modelConfig ? {
        api_key: modelConfig.apiKey,
        base_url: modelConfig.baseUrl,
        model: modelConfig.model
      } : null,
    };

    const assistantId = (Date.now() + 1).toString();
    let streamedContent = "";
    let toolsCalled: string[] = [];
    let memoriesUsed: string[] = [];
    let memoryCitations: MemoryCitation[] = [];

    try {
      const streamResponse = await fetch("/api/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody),
        signal: abortController.signal,
      });

      if (streamResponse.ok && streamResponse.body) {
        setMessages((prev) => [
          ...prev,
          {
            id: assistantId,
            content: "",
            role: "assistant",
            timestamp: new Date(),
          },
        ]);

        const reader = streamResponse.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const parts = buffer.split("\n\n");
          buffer = parts.pop() || "";

          for (const part of parts) {
            const line = part.trim();
            if (!line.startsWith("data:")) continue;
            try {
              const payload = JSON.parse(line.replace(/^data:\s*/, ""));
              if (payload.type === "token") {
                streamedContent += payload.content;
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantId
                      ? { ...m, content: streamedContent }
                      : m
                  )
                );
              } else if (payload.type === "tool_result" && payload.metadata?.citation) {
                memoryCitations.push(payload.metadata.citation as MemoryCitation);
                memoriesUsed.push(payload.metadata.citation.content_snippet);
              } else if (payload.type === "tool_result" && payload.metadata?.source === "memory") {
                memoriesUsed.push(payload.content);
              } else if (payload.type === "tool_result" && payload.metadata?.tool_name) {
                toolsCalled.push(payload.metadata.tool_name);
              }
            } catch {
              /* ignore malformed SSE chunks */
            }
          }
        }

        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? {
                  ...m,
                  content: streamedContent || "（无内容）",
                  metadata: {
                    tools_called: toolsCalled,
                    memories_used: memoriesUsed,
                    memory_citations: memoryCitations,
                    stop_reason: "end_turn",
                  },
                }
              : m
          )
        );
        loadSessions();
        return;
      }

      const response = await fetch("/api/chat", {
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
          stop_reason: data.decision_explanation?.action || "end_turn",
        }
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error: any) {
      if (error.name === "AbortError") {
        // 用户终止了请求
        const abortMessage: Message = {
          id: (Date.now() + 1).toString(),
          content: "（已终止回复）",
          role: "assistant",
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, abortMessage]);
      } else {
        console.error("Failed to send message:", error);
      }
    } finally {
      setIsLoading(false);
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
        </div>
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
              <p className="text-[10px] text-slate-400 mt-0.5">输入消息开始体验智能记忆</p>
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
                <p className="text-[13px] leading-relaxed whitespace-pre-wrap">{message.content}</p>
                <p className={`text-[10px] mt-1 ${message.role === "user" ? "text-indigo-200" : "text-slate-400"}`}>
                  {message.timestamp.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" })}
                </p>
                {message.metadata && renderMetadata(message.metadata)}
              </div>
            </div>
          ))}
          
          {isLoading && (
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
          <div className="flex gap-2 items-end">
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
                disabled={!input.trim()}
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
