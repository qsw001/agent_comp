import { Navbar } from "@/components/layout/Navbar";
import Link from "next/link";

export default function LearningPage() {
  return (
    <>
      <Navbar />
      <main className="flex-1">
        <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
          <h1 className="text-2xl font-bold">学习内容</h1>
          <p className="mt-1 text-muted-foreground">为你个性化推荐的学习资源</p>

          {/* 类型过滤 */}
          <div className="mt-6 flex flex-wrap gap-2">
            {types.map((t) => (
              <button
                key={t}
                className="rounded-full border border-border px-4 py-1.5 text-sm font-medium hover:bg-muted transition-colors"
              >
                {t}
              </button>
            ))}
          </div>

          {/* 内容卡片列表 */}
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {contents.map((item) => (
              <Link
                key={item.id}
                href={`/learning/${item.id}`}
                className="group rounded-xl border border-border bg-card p-5 shadow-sm transition-shadow hover:shadow-md"
              >
                <div className="mb-3 flex items-center gap-2">
                  <span className="rounded-md bg-primary-100 px-2 py-0.5 text-xs font-medium text-primary-700 dark:bg-primary-900 dark:text-primary-300">
                    {item.type}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {item.difficulty}
                  </span>
                </div>
                <h3 className="font-semibold group-hover:text-primary-600 transition-colors">
                  {item.title}
                </h3>
                <p className="mt-2 text-sm text-muted-foreground line-clamp-2">
                  {item.desc}
                </p>
              </Link>
            ))}
          </div>
        </div>
      </main>
    </>
  );
}

const types = ["全部", "讲解", "思维导图", "题目", "扩展阅读", "视频", "代码"];

const contents = [
  { id: "1", title: "算法基础 — 动态规划入门", type: "讲解", difficulty: "中等", desc: "从斐波那契数列到背包问题，系统讲解 DP 核心思想" },
  { id: "2", title: "Python 函数式编程思维导图", type: "思维导图", difficulty: "入门", desc: "直观理解 map/reduce/filter 和 lambda 表达式" },
  { id: "3", title: "线性代数练习题集", type: "题目", difficulty: "困难", desc: "矩阵运算、特征值分解等 20 道精选练习题" },
  { id: "4", title: "深度学习发展综述 (2025)", type: "扩展阅读", difficulty: "进阶", desc: "涵盖 Transformer、Diffusion、多模态等前沿方向" },
  { id: "5", title: "FastAPI 实战教程视频", type: "视频", difficulty: "中等", desc: "从零搭建 RESTful API，包含数据库集成和部署" },
  { id: "6", title: "React Hooks 代码示例", type: "代码", difficulty: "简单", desc: "useState/useEffect/useContext 使用场景与最佳实践" },
];
