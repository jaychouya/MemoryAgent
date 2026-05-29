import ChatPanel from "@/components/ChatPanel";

export default function Home() {
  return (
    <main className="min-h-screen bg-slate-50">
      {/* 顶部导航 */}
      <nav className="bg-white border-b border-slate-200 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900">MemoMind</h1>
              <p className="text-xs text-slate-500">智能AI助手</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <span className="px-3 py-1.5 bg-indigo-50 text-indigo-600 text-sm font-medium rounded-full">
              认知记忆架构
            </span>
          </div>
        </div>
      </nav>

      {/* 主内容区 */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          
          {/* 左侧：记忆层说明 */}
          <aside className="lg:col-span-1 space-y-6">
            <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
                <svg className="w-5 h-5 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                </svg>
                四层记忆架构
              </h2>
              
              <div className="space-y-4">
                <div className="p-4 bg-indigo-50 rounded-xl border border-indigo-100">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-3 h-3 bg-indigo-500 rounded-full"></div>
                    <h3 className="font-medium text-indigo-900">工作记忆</h3>
                  </div>
                  <p className="text-sm text-indigo-700">当前对话上下文，高速读写，会话结束即清空</p>
                </div>
                
                <div className="p-4 bg-purple-50 rounded-xl border border-purple-100">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
                    <h3 className="font-medium text-purple-900">短期记忆</h3>
                  </div>
                  <p className="text-sm text-purple-700">近期对话摘要，临时偏好，7-30天自动衰减</p>
                </div>
                
                <div className="p-4 bg-pink-50 rounded-xl border border-pink-100">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-3 h-3 bg-pink-500 rounded-full"></div>
                    <h3 className="font-medium text-pink-900">长期记忆</h3>
                  </div>
                  <p className="text-sm text-pink-700">稳定偏好和知识，持久化存储，定期整理</p>
                </div>
                
                <div className="p-4 bg-amber-50 rounded-xl border border-amber-100">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-3 h-3 bg-amber-500 rounded-full"></div>
                    <h3 className="font-medium text-amber-900">情景记忆</h3>
                  </div>
                  <p className="text-sm text-amber-700">重要事件和经历，情感标记，永久保存</p>
                </div>
              </div>
            </div>
            
            {/* 核心特性 */}
            <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
                <svg className="w-5 h-5 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                核心特性
              </h2>
              
              <ul className="space-y-3">
                <li className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span className="text-sm text-slate-700">自主性决策引擎</span>
                </li>
                <li className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span className="text-sm text-slate-700">记忆可解释性</span>
                </li>
                <li className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span className="text-sm text-slate-700">跨会话记忆共享</span>
                </li>
                <li className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span className="text-sm text-slate-700">智能记忆遗忘</span>
                </li>
              </ul>
            </div>
          </aside>
          
          {/* 右侧：聊天界面 */}
          <div className="lg:col-span-3">
            <ChatPanel />
          </div>
        </div>
      </div>
      
      {/* 底部 */}
      <footer className="bg-white border-t border-slate-200 px-6 py-4 mt-8">
        <div className="max-w-7xl mx-auto flex items-center justify-between text-sm text-slate-500">
          <p>MemoMind · 基于认知记忆架构的个人AI助手</p>
          <p>展示项目 · 面试作品</p>
        </div>
      </footer>
    </main>
  );
}
