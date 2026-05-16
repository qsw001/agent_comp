import { Navbar } from "@/components/layout/Navbar";

export default function ProfilePage() {
  return (
    <>
      <Navbar />
      <main className="flex-1">
        <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
          <h1 className="text-2xl font-bold">我的学习画像</h1>
          <p className="mt-1 text-muted-foreground">你的个性化学习特征概览</p>

          {/* 画像维度雷达图占位 */}
          <div className="mt-8 grid gap-6 sm:grid-cols-2">
            {dimensions.map((dim) => (
              <div
                key={dim.name}
                className="rounded-xl border border-border bg-card p-5 shadow-sm"
              >
                <div className="flex items-center justify-between">
                  <h3 className="font-medium">{dim.label}</h3>
                  <span className="text-sm font-bold text-primary-600">
                    {dim.value}%
                  </span>
                </div>
                <div className="mt-3 h-2 w-full rounded-full bg-muted">
                  <div
                    className="h-2 rounded-full bg-primary-500 transition-all"
                    style={{ width: `${dim.value}%` }}
                  />
                </div>
                <p className="mt-2 text-xs text-muted-foreground">
                  {dim.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </main>
    </>
  );
}

const dimensions = [
  { name: "knowledge", label: "知识水平", value: 65, description: "当前学科基础知识掌握程度" },
  { name: "cognitive", label: "认知风格", value: 78, description: "偏向视觉型 + 实践型学习" },
  { name: "weakness", label: "易错点", value: 45, description: "需要重点加强的薄弱环节" },
  { name: "preference", label: "偏好形式", value: 82, description: "喜欢互动式、项目式学习" },
  { name: "speed", label: "学习速度", value: 70, description: "中等偏快，需适当挑战" },
  { name: "depth", label: "理解深度", value: 60, description: "概念理解良好，需加强应用" },
];
