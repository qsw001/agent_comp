import { Navbar } from "@/components/layout/Navbar";

export default function DashboardPage() {
  return (
    <>
      <Navbar />
      <main className="flex-1">
        <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
          <h1 className="text-2xl font-bold">学习仪表盘</h1>
          <p className="mt-1 text-muted-foreground">你的学习数据分析与概览</p>

          {/* 统计卡片 */}
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {stats.map((stat) => (
              <div
                key={stat.label}
                className="rounded-xl border border-border bg-card p-5 shadow-sm"
              >
                <p className="text-sm text-muted-foreground">{stat.label}</p>
                <p className="mt-2 text-3xl font-bold">{stat.value}</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  {stat.change}
                </p>
              </div>
            ))}
          </div>

          {/* 最近活动 */}
          <div className="mt-8">
            <h2 className="text-lg font-semibold">最近活动</h2>
            <div className="mt-4 space-y-3">
              {activities.map((act, idx) => (
                <div
                  key={idx}
                  className="flex items-center gap-4 rounded-lg border border-border bg-card p-4 shadow-sm"
                >
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary-100 text-lg dark:bg-primary-900">
                    {act.icon}
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium">{act.title}</p>
                    <p className="text-xs text-muted-foreground">{act.time}</p>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    {act.duration}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>
    </>
  );
}

const stats = [
  { label: "学习时长", value: "42h", change: "较上周 +12%" },
  { label: "已完成内容", value: "18", change: "共 52 个" },
  { label: "平均得分", value: "85%", change: "较上周 +3%" },
  { label: "画像维度", value: "6", change: "完整度 100%" },
];

const activities = [
  { icon: "💬", title: "完成对话式画像构建", time: "2 小时前", duration: "15 分钟" },
  { icon: "📚", title: "学习了《算法基础 — 动态规划入门》", time: "昨天 14:30", duration: "45 分钟" },
  { icon: "✏️", title: "完成线性代数练习题 (得分 88%)", time: "昨天 10:00", duration: "30 分钟" },
  { icon: "🗺️", title: "学习路径已更新", time: "前天", duration: "新增 2 个节点" },
];
