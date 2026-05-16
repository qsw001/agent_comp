import { Navbar } from "@/components/layout/Navbar";

export default function ChatPage() {
  return (
    <>
      <Navbar />
      <main className="flex-1">
        <div className="mx-auto flex h-[calc(100vh-4rem)] max-w-7xl">
          {/* 侧栏：会话列表 — 占位 */}
          <aside className="hidden w-72 border-r border-border p-4 lg:block">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-sm font-semibold">会话列表</h2>
              <button className="rounded-lg bg-primary-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-primary-700">
                + 新会话
              </button>
            </div>
            <div className="space-y-2">
              <div className="rounded-lg border border-border bg-muted/30 p-3">
                <p className="text-sm font-medium">对话式画像</p>
                <p className="mt-1 text-xs text-muted-foreground">点击开始创建你的个性化画像</p>
              </div>
            </div>
          </aside>

          {/* 主体：对话区域 */}
          <div className="flex flex-1 flex-col">
            {/* 消息区 */}
            <div className="flex-1 overflow-y-auto p-4">
              <div className="mx-auto max-w-3xl space-y-4 pt-8">
                <div className="rounded-2xl bg-muted/50 p-6 text-center">
                  <h1 className="text-2xl font-bold">开始你的学习之旅</h1>
                  <p className="mt-2 text-muted-foreground">
                    告诉我一些关于你的信息，让我更好地了解你的学习需求
                  </p>
                </div>
              </div>
            </div>

            {/* 输入区 */}
            <div className="border-t border-border p-4">
              <div className="mx-auto flex max-w-3xl gap-3">
                <input
                  type="text"
                  placeholder="输入消息..."
                  className="flex-1 rounded-xl border border-input bg-background px-4 py-3 text-sm outline-none ring-offset-background placeholder:text-muted-foreground focus:ring-2 focus:ring-primary"
                />
                <button className="rounded-xl bg-primary-600 px-6 py-3 text-sm font-semibold text-white hover:bg-primary-700 transition-colors">
                  发送
                </button>
              </div>
            </div>
          </div>
        </div>
      </main>
    </>
  );
}
