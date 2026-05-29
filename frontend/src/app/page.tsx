import ChatPanel from "@/components/ChatPanel";

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-center mb-8 text-gray-800">
          MemoMind
        </h1>
        <p className="text-center text-gray-600 mb-8">
          Personal AI Assistant with Cognitive Memory Architecture
        </p>
        <div className="flex justify-center">
          <ChatPanel />
        </div>
      </div>
    </main>
  );
}
