import ChatPanel from "@/components/ChatPanel";

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-indigo-50 p-8">
      <div className="max-w-4xl mx-auto">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-50 rounded-full text-indigo-600 text-sm font-medium mb-6">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            认知记忆架构
          </div>
          
          <h1 className="text-5xl font-bold text-slate-900 mb-4 tracking-tight">
            <span className="bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-500 bg-clip-text text-transparent">
              MemoMind
            </span>
          </h1>
          
          <p className="text-lg text-slate-600 max-w-2xl mx-auto leading-relaxed">
            您的个人AI助手，具备四层认知记忆架构
            <br />
            <span className="text-slate-400">越用越懂您，真正理解您的偏好和习惯</span>
          </p>
        </div>

        {/* Features */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 hover:border-indigo-200 transition-colors">
            <div className="w-12 h-12 bg-indigo-50 rounded-xl flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <h3 className="font-semibold text-slate-900 mb-2">工作记忆</h3>
            <p className="text-sm text-slate-500">当前对话上下文，高速读写</p>
          </div>
          
          <div className="bg-white p-6 rounded-2xl border border-slate-200 hover:border-purple-200 transition-colors">
            <div className="w-12 h-12 bg-purple-50 rounded-xl flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="font-semibold text-slate-900 mb-2">短期记忆</h3>
            <p className="text-sm text-slate-500">近期对话摘要，临时偏好</p>
          </div>
          
          <div className="bg-white p-6 rounded-2xl border border-slate-200 hover:border-pink-200 transition-colors">
            <div className="w-12 h-12 bg-pink-50 rounded-xl flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-pink-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
              </svg>
            </div>
            <h3 className="font-semibold text-slate-900 mb-2">长期记忆</h3>
            <p className="text-sm text-slate-500">稳定偏好和知识，持久化存储</p>
          </div>
        </div>

        {/* Chat Panel */}
        <div className="flex justify-center">
          <ChatPanel />
        </div>

        {/* Footer */}
        <div className="text-center mt-12 text-sm text-slate-400">
          <p>MemoMind · 基于认知记忆架构的个人AI助手</p>
          <p className="mt-1">展示项目 · 面试作品</p>
        </div>
      </div>
    </main>
  );
}
