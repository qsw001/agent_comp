import Link from "next/link";
import { Navbar } from "@/components/layout/Navbar";

export default function HomePage() {
  return (
    <>
      <Navbar />
      <main className="flex-1">
        {/* Hero */}
        <section className="relative overflow-hidden py-20 lg:py-32">
          <div className="absolute inset-0 bg-gradient-to-br from-primary-50 via-white to-accent-50 dark:from-primary-950 dark:via-background dark:to-accent-950" />
          <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="mx-auto max-w-3xl text-center">
              <h1 className="text-4xl font-bold tracking-tight sm:text-5xl lg:text-6xl">
                <span className="bg-gradient-to-r from-primary-600 to-accent-600 bg-clip-text text-transparent">
                  AI 个性化教育平台
                </span>
              </h1>
              <p className="mt-6 text-lg leading-8 text-muted-foreground">
                基于大模型与多智能体架构，为每个学习者构建个性化画像，
                动态生成适配内容，规划最优路径，实现真正的"因材施教"。
              </p>
              <div className="mt-10 flex items-center justify-center gap-4">
                <Link
                  href="/chat"
                  className="rounded-lg bg-primary-600 px-8 py-3 text-sm font-semibold text-white shadow-sm hover:bg-primary-700 transition-colors"
                >
                  开始对话画像
                </Link>
                <Link
                  href="/dashboard"
                  className="rounded-lg border border-border bg-white px-8 py-3 text-sm font-semibold text-foreground shadow-sm hover:bg-muted transition-colors dark:bg-gray-900"
                >
                  查看仪表盘
                </Link>
              </div>
            </div>
          </div>
        </section>

        {/* 核心能力 */}
        <section className="border-t border-border py-20">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <h2 className="text-center text-3xl font-bold">核心能力</h2>
            <p className="mt-4 text-center text-muted-foreground">
              五大模块覆盖个性化学习的全流程
            </p>
            <div className="mt-12 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
              {features.map((feature) => (
                <div
                  key={feature.title}
                  className="group rounded-xl border border-border bg-card p-6 shadow-sm transition-shadow hover:shadow-md"
                >
                  <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-lg bg-primary-100 text-primary-600 dark:bg-primary-900 dark:text-primary-300">
                    {feature.icon}
                  </div>
                  <h3 className="text-lg font-semibold">{feature.title}</h3>
                  <p className="mt-2 text-sm text-muted-foreground">
                    {feature.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* 技术栈 */}
        <section className="border-t border-border bg-muted/50 py-20">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <h2 className="text-center text-3xl font-bold">技术栈</h2>
            <div className="mt-12 grid gap-6 text-center sm:grid-cols-3 lg:grid-cols-6">
              {[
                "Next.js",
                "FastAPI",
                "LangGraph",
                "Qdrant",
                "PostgreSQL",
                "讯飞星火",
              ].map((tech) => (
                <div
                  key={tech}
                  className="rounded-lg border border-border bg-card px-4 py-3 text-sm font-medium shadow-sm"
                >
                  {tech}
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="border-t border-border py-8 text-center text-sm text-muted-foreground">
          <p>第十五届中国软件杯大赛 · A组赛题 · 科大讯飞出题</p>
          <p className="mt-1">答疑 QQ 群：1072584310</p>
        </footer>
      </main>
    </>
  );
}

const features = [
  {
    title: "对话式画像",
    description: "通过自然对话交互，摒弃繁琐表单，智能构建多维度学习者画像。",
    icon: "🧑‍🎓",
  },
  {
    title: "个性化内容生成",
    description: "基于画像动态生成讲解、思维导图、题目、扩展阅读等多样内容。",
    icon: "📚",
  },
  {
    title: "学习路径规划",
    description: "结合知识图谱与 AI 规划最优学习路径，动态调整学习策略。",
    icon: "🗺️",
  },
  {
    title: "智能答疑",
    description: "结合 RAG 技术的多轮对话 AI 答疑，提供详细逐步讲解。",
    icon: "💬",
  },
  {
    title: "评估反馈",
    description: "自动评估学习效果，跟踪进度，自适应调整学习策略。",
    icon: "📊",
  },
  {
    title: "多模态学习",
    description: "支持文字、代码、思维导图、视频等多种学习资源形式。",
    icon: "🎯",
  },
];
