"""
种子数据脚本 — 插入初始学习内容
"""
import asyncio
import uuid

from sqlalchemy import select

from app.database import async_session_factory
from app.models import LearningContent, User


async def seed_data():
    """插入示例数据"""
    async with async_session_factory() as session:
        # 检查是否已有数据
        result = await session.execute(select(LearningContent).limit(1))
        if result.scalar_one_or_none():
            print("ℹ️ 数据已存在，跳过")
            return

        print("🌱 插入种子数据...")

        contents = [
            LearningContent(
                id=str(uuid.uuid4()),
                title="算法基础 — 动态规划入门",
                type="explanation",
                subject="计算机科学",
                difficulty=3,
                content="# 动态规划入门\n\n动态规划（Dynamic Programming）是一种通过把原问题分解为相对简单的子问题的方式求解复杂问题的方法。\n\n## 核心思想\n\n1. **最优子结构**：问题的最优解包含子问题的最优解\n2. **重叠子问题**：子问题会被重复计算，需要缓存\n3. **状态转移方程**：定义状态之间的关系",
                description="从斐波那契数列到背包问题，系统讲解 DP 核心思想",
                tags=["算法", "动态规划", "入门"],
            ),
            LearningContent(
                id=str(uuid.uuid4()),
                title="Python 函数式编程",
                type="mindmap",
                subject="编程",
                difficulty=2,
                content="# 函数式编程概念图\n\n- 纯函数\n  - 无副作用\n  - 引用透明\n- 高阶函数\n  - map\n  - filter\n  - reduce\n- 不可变数据\n- 惰性求值",
                description="直观理解 map/reduce/filter 和 lambda 表达式",
                tags=["Python", "函数式编程"],
            ),
            LearningContent(
                id=str(uuid.uuid4()),
                title="线性代数核心习题",
                type="quiz",
                subject="数学",
                difficulty=4,
                content="## 线性代数练习题\n\n### 1. 矩阵运算\n计算矩阵乘积 [[1,2],[3,4]] × [[5,6],[7,8]]\n\n### 2. 特征值\n求矩阵 [[4,1],[2,3]] 的特征值和特征向量\n\n### 3. 线性方程组\n求解方程组：\nx + 2y = 5\n3x + 4y = 11",
                description="矩阵运算、特征值分解等练习题",
                tags=["数学", "线性代数", "练习"],
            ),
            LearningContent(
                id=str(uuid.uuid4()),
                title="深度学习发展综述 (2025)",
                type="reading",
                subject="人工智能",
                difficulty=5,
                content="# 深度学习前沿综述\n\n## Transformer 架构演进\n\n从原始 Transformer 到 GPT、BERT、LLaMA 系列...\n\n## 扩散模型\n\n在图像生成领域的突破性进展...\n\n## 多模态大模型\n\n融合文本、图像、语音的统一模型...",
                description="涵盖 Transformer、Diffusion、多模态等前沿方向",
                tags=["AI", "深度学习", "前沿"],
            ),
            LearningContent(
                id=str(uuid.uuid4()),
                title="FastAPI 实战教程",
                type="video",
                subject="Web开发",
                difficulty=3,
                content="## FastAPI 实战教程\n\n### 第一章：环境搭建\n- 安装 Python 3.12\n- 创建虚拟环境\n- 安装 FastAPI 和 Uvicorn\n\n### 第二章：第一个 API\n- 定义路由\n- 请求与响应模型\n- 依赖注入",
                description="从零搭建 RESTful API，包含数据库集成和部署",
                tags=["FastAPI", "Python", "Web"],
            ),
            LearningContent(
                id=str(uuid.uuid4()),
                title="React Hooks 最佳实践",
                type="code",
                subject="前端开发",
                difficulty=2,
                content="```tsx\n// useState\nconst [count, setCount] = useState(0);\n\n// useEffect\nuseEffect(() => {\n  fetchData().then(setData);\n}, []);\n\n// useContext\nconst theme = useContext(ThemeContext);\n\n// 自定义 Hook\nfunction useWindowSize() {\n  const [size, setSize] = useState({ width: 0, height: 0 });\n  useEffect(() => {\n    const handler = () => setSize({ width: window.innerWidth, height: window.innerHeight });\n    window.addEventListener('resize', handler);\n    return () => window.removeEventListener('resize', handler);\n  }, []);\n  return size;\n}\n```",
                description="useState/useEffect/useContext 使用场景与最佳实践",
                tags=["React", "Hooks", "前端"],
            ),
        ]

        for content in contents:
            session.add(content)

        await session.commit()
        print(f"✅ 已插入 {len(contents)} 条学习内容")


if __name__ == "__main__":
    asyncio.run(seed_data())
