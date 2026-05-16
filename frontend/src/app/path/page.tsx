import { Navbar } from "@/components/layout/Navbar";

export default function PathPage() {
  return (
    <>
      <Navbar />
      <main className="flex-1">
        <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
          <h1 className="text-2xl font-bold">学习路径</h1>
          <p className="mt-1 text-muted-foreground">为你规划的最优学习路线</p>

          {/* 路径概览 */}
          <div className="mt-6 rounded-xl border border-border bg-card p-5 shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="font-semibold">Python 全栈开发入门</h2>
                <p className="mt-1 text-sm text-muted-foreground">
                  目标：掌握 Python 全栈开发核心技能
                </p>
              </div>
              <div className="text-right">
                <span className="text-2xl font-bold text-primary-600">35%</span>
                <p className="text-xs text-muted-foreground">完成进度</p>
              </div>
            </div>
            <div className="mt-4 h-2 w-full rounded-full bg-muted">
              <div className="h-2 w-[35%] rounded-full bg-primary-500" />
            </div>
          </div>

          {/* 路径节点 */}
          <div className="mt-8 space-y-4">
            {nodes.map((node, idx) => (
              <div key={node.id} className="relative flex gap-4">
                {/* 时间线 */}
                <div className="flex flex-col items-center">
                  <div
                    className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-bold ${
                      node.status === "completed"
                        ? "bg-green-100 text-green-700"
                        : node.status === "in_progress"
                        ? "bg-primary-100 text-primary-700"
                        : "bg-muted text-muted-foreground"
                    }`}
                  >
                    {idx + 1}
                  </div>
                  {idx < nodes.length - 1 && (
                    <div className="mt-1 h-full w-0.5 bg-border" />
                  )}
                </div>
                {/* 内容 */}
                <div className="mb-6 flex-1 rounded-xl border border-border bg-card p-4 shadow-sm">
                  <div className="flex items-center justify-between">
                    <h3 className="font-medium">{node.title}</h3>
                    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                      node.status === "completed"
                        ? "bg-green-100 text-green-700"
                        : node.status === "in_progress"
                        ? "bg-blue-100 text-blue-700"
                        : "bg-gray-100 text-gray-600"
                    }`}>
                      {statusMap[node.status]}
                    </span>
                  </div>
                  <p className="mt-1 text-sm text-muted-foreground">
                    {node.desc}
                  </p>
                  <div className="mt-2 flex items-center gap-3 text-xs text-muted-foreground">
                    <span>⏱ {node.time}</span>
                    <span>📖 {node.type}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </main>
    </>
  );
}

const statusMap: Record<string, string> = {
  completed: "已完成",
  in_progress: "进行中",
  pending: "待开始",
};

const nodes = [
  { id: "1", title: "Python 基础语法", desc: "变量、数据类型、控制流、函数定义", time: "2 小时", type: "讲解+代码", status: "completed" as const },
  { id: "2", title: "面向对象编程", desc: "类、继承、多态、魔术方法", time: "3 小时", type: "讲解+题目", status: "completed" as const },
  { id: "3", title: "FastAPI 入门", desc: "路由、依赖注入、Pydantic 模型", time: "4 小时", type: "视频+实践", status: "in_progress" as const },
  { id: "4", title: "数据库与 SQLAlchemy", desc: "ORM 模型、迁移、关联查询", time: "5 小时", type: "讲解+代码", status: "pending" as const },
  { id: "5", title: "前端基础 (HTML/CSS/JS)", desc: "响应式布局、DOM 操作、Fetch API", time: "4 小时", type: "视频+实践", status: "pending" as const },
  { id: "6", title: "综合项目实战", desc: "搭建一个完整的全栈 Web 应用", time: "8 小时", type: "项目实战", status: "pending" as const },
];
