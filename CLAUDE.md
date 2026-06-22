# AI 教育平台 — 开发指南

> 项目：基于大模型的个性化资源生成与学习多智能体系统（第十五届中国软件杯 · 科大讯飞赛题）

---

## 0. 项目目录结构

```
ai-education-platform/
├── data/                            # 📄 原始课程资料（RAG 知识库源文件）
│   └── 随机过程及应用.pdf           #   当前课程教材
├── backend/                         # FastAPI 后端
│   ├── alembic/                     #   数据库迁移
│   ├── app/
│   │   ├── agents/                  #   🤖 LangGraph 多智能体系统（核心）
│   │   │   ├── graph.py             #     图编排 + run_agent() 入口
│   │   │   ├── nodes.py             #     5 个 Agent 节点实现
│   │   │   └── state.py             #     状态定义
│   │   ├── api/v1/                  #   API 路由
│   │   ├── core/                    #   安全、异常、Redis
│   │   ├── llm/                     #   LLM Provider 工厂模式（4 个 Provider）
│   │   ├── rag/                     #   RAG 检索增强（Qdrant + Embedding）
│   │   │   ├── embeddings.py       #     Sentence-Transformer 嵌入
│   │   │   ├── pdf_processor.py    #     PDF 解析 + OCR（扫描件降级）
│   │   │   ├── vector_store.py     #     Qdrant 操作
│   │   │   └── retriever.py        #     检索 + 构建 prompt
│   │   ├── models/                  #   SQLAlchemy 模型（7 张表）
│   │   ├── schemas/                 #   Pydantic 请求/响应
│   │   ├── services/                #   业务服务层
│   │   ├── config.py                #   配置管理
│   │   ├── database.py              #   数据库连接
│   │   └── main.py                  #   🚀 FastAPI 入口
│   ├── scripts/                     #   初始化脚本
│   ├── pyproject.toml
│   └── requirements.txt
├── frontend/                        # Next.js 前端
│   ├── src/
│   │   ├── app/                     #   App Router（7 个页面路由）
│   │   │   ├── chat/                #     AI 对话
│   │   │   ├── dashboard/           #     仪表盘
│   │   │   ├── evaluation/          #     评估
│   │   │   ├── learning/            #     资源中心
│   │   │   ├── login/               #     登录/注册
│   │   │   ├── path/                #     学习路径
│   │   │   ├── profile/             #     画像构建
│   │   │   ├── page.tsx             #     根 → /dashboard
│   │   │   ├── globals.css
│   │   │   └── layout.tsx           #     根布局
│   │   ├── components/layout/       #   导航栏、Provider
│   │   ├── hooks/                   #   自定义 hooks
│   │   ├── lib/                     #   Axios 封装 + 认证工具
│   │   ├── stores/                  #   Zustand（4 个 Store）
│   │   ├── types/                   #   TypeScript 类型
│   │   └── middleware.ts            #   路由鉴权
│   ├── tailwind.config.ts
│   ├── next.config.js
│   └── package.json
├── docs/                            # 文档
│   ├── PROJECT_CONTEXT.md           #   项目上下文（开发前必读）
│   ├── api.md                       #   API 接口文档
│   ├── architecture.md              #   架构设计
│   ├── requirements.md              #   软件杯赛题需求
│   └── images/
├── agent/                           # 遗留旧版 Agent 原型（待清理）
├── docker-compose.yml               # PostgreSQL + Redis + Qdrant
├── nginx.conf                       # 生产反向代理
├── requirements.docx                # 赛题原始需求（不可修改）
└── README.md
```

---

## 1. 前置阅读

**开发前必须先完整阅读以下文档：**

1. `docs/PROJECT_CONTEXT.md` — 项目现状、功能完成度、Mock 清单、已知问题
2. `docs/requirements.md` — 软件杯赛题需求（5 大基本功能）
3. `docs/api.md` — 全部 API 接口定义
4. `docs/architecture.md` — 系统架构图、多智能体数据流

---

## 2. 当前课程教材

当前课程统一为 **《随机过程及应用》**。

PDF 源文件位于 `data/随机过程及应用.pdf`，是 RAG 知识库的唯一来源文档。所有知识性回答优先从此文档检索。

---

## 3. P0 唯一目标

当前最高优先级（P0）的目标是打通以下链路，且**每次只实现一个明确功能**：

| 步骤 | 说明 |
|---|---|
| ① PDF 入库 Qdrant | 解析 PDF → 分块 → 嵌入 → 存入 `learning_resources` 集合，chunk metadata 保留 `source_file`、`page_number`、`chapter`、`chunk_id` |
| ② 检索验证 | 手动测试 Qdrant 语义查询，确认返回相关段落及页码 |
| ③ QA Agent 接入 RAG + LLM | 修改 `qa_agent_node` 调用 `LLMFactory.chat()` + `retrieve_context()`，生成带引用回答 |
| ④ 聊天页展示真实回答 | 前端渲染带页码来源的回答，去除 mock fallback |

**P0 完成前不得开始 P1/P2 工作。**

---

## 4. 开发纪律

### 4.1 每次只改一个功能

一次修改只聚焦一个 P0 模块，不得同时修改多个 P0 模块。

### 4.2 修改前输出计划

修改任何代码前，先输出以下内容：

```
## 修改计划
- 目标：
- 修改/新增的文件：
- 风险：
- 测试方法：
```

### 4.3 未经明确要求不得做以下操作

```
- 重构整个项目
- 删除已有功能
- 修改 docker-compose.yml
- 修改 nginx.conf
- 修改 backend/app/main.py
- 修改 backend/app/database.py
- 修改 backend/app/config.py
- 修改 backend/app/core/security.py
- 修改 frontend/next.config.js
- 修改 frontend/src/middleware.ts
- 修改已有 Alembic migration
- 删除根目录 agent/
```

### 4.4 安全红线

**不得读取、输出、提交或硬编码 `.env` 中的任何密码、SMTP 凭据、API Key。**

### 4.5 LLM 调用规范

所有 LLM 调用必须通过 `LLMFactory` 进行，不能绕过 Provider 工厂直接调用第三方 SDK。

---

## 5. RAG 准则

### 5.1 知识优先检索

所有知识性回答**优先走 RAG**。没有检索依据时必须明确说明"当前知识库中没有找到相关依据"。

### 5.2 Chunk Metadata 规范

RAG chunk metadata 至少包含以下字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `source_file` | str | 来源 PDF 文件名 |
| `page_number` | int | 所在页码 |
| `chapter` | str | 所属章节标题 |
| `chunk_id` | str | 分块唯一标识 |

---

## 6. 修改完成后的交付规范

每次修改完成后必须提供：

1. **运行命令**
   ```bash
   # 启动数据库
   docker compose up -d postgres redis qdrant
   # 启动后端
   cd backend && source .venv/bin/activate && PYTHONPATH=. uvicorn app.main:app --reload
   # 启动前端
   cd frontend && npm run dev
   ```

2. **测试命令** — 验证本次修改的测试方法或脚本

3. **实际修改的文件清单** — 列出所有新增或修改的文件

4. **已知限制** — 当前实现的局限性、待解决的边界情况

---

## 7. 语言规范

- 默认用中文解释（包含需求讨论、计划说明、总结报告）
- 代码注释和变量/函数命名遵循现有项目风格（后端：Python snake_case，前端：TypeScript camelCase）
- 代码注释与代码逻辑本身用英文（见现有代码习惯），与项目上下文相关的说明用中文

---

## 8. 启动备忘

```bash
# 数据库
docker compose up -d postgres redis qdrant

# 后端（需在 backend/ 目录下）
source .venv/bin/activate
PYTHONPATH=. alembic upgrade head     # 首次需要迁移
PYTHONPATH=. uvicorn app.main:app --reload

# 前端（需在 frontend/ 目录下）
npm run dev
```

---

## 9. 数据库表

| 表 | 说明 |
|---|---|
| `users` | 用户（密码哈希 + 邮箱） |
| `learner_profiles` | 学习者画像（JSONB dimensions） |
| `chat_sessions` | 对话会话 |
| `chat_messages` | 消息（text / markdown / mindmap） |
| `learning_contents` | 学习内容 |
| `learning_paths` | 学习路径（JSONB nodes） |
| `evaluations` | 评估记录 |
