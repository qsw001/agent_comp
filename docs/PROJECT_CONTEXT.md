# AI 教育平台 — 项目上下文

> 生成时间：2026-06-22
> 用途：开发者接手项目时的完整现状参考

---

## 一、项目目录结构

```
ai-education-platform/
├── agent/                          # (根级) 遗留的旧版 Agent 原型
│   ├── graph.py                    #   LangGraph 图编排（简版）
│   └── state.py                    #   状态定义（简版）
├── backend/                        # FastAPI 后端
│   ├── alembic/                    #   数据库迁移
│   ├── app/
│   │   ├── agents/                 #   🤖 LangGraph 多智能体系统（核心）
│   │   │   ├── graph.py            #     图编排 + run_agent() 入口
│   │   │   ├── nodes.py            #     5 个 Agent 节点实现（全部业务逻辑内联）
│   │   │   └── state.py            #     状态定义
│   │   ├── api/v1/                 #   API 路由
│   │   │   ├── router.py           #     路由聚合
│   │   │   ├── auth.py             #     认证（登录/注册/验证码）
│   │   │   ├── chat.py             #     对话
│   │   │   ├── learning.py         #     学习内容/路径
│   │   │   ├── profile.py          #     画像
│   │   │   ├── resources.py        #     资源生成
│   │   │   └── evaluation.py       #     评估
│   │   ├── core/
│   │   │   ├── security.py         #     JWT + bcrypt
│   │   │   ├── exceptions.py       #     统一异常
│   │   │   └── redis.py            #     Redis 客户端
│   │   ├── llm/                    #   LLM Provider 工厂模式
│   │   │   ├── base.py             #     抽象基类
│   │   │   ├── __init__.py         #     LLMFactory (注册/fallback)
│   │   │   ├── deepseek.py         #     DeepSeek
│   │   │   ├── qwen.py             #     通义千问
│   │   │   ├── xunfei.py           #     讯飞星火
│   │   │   └── zhipu.py            #     智谱GLM
│   │   ├── rag/                    #   RAG 检索增强
│   │   │   ├── embeddings.py       #     Sentence-Transformer 嵌入
│   │   │   ├── vector_store.py     #     Qdrant 操作
│   │   │   └── retriever.py        #     检索 + 构建 prompt
│   │   ├── models/                 #   SQLAlchemy 模型
│   │   ├── schemas/                #   Pydantic 请求/响应
│   │   ├── services/               #   业务服务层
│   │   ├── config.py               #   配置管理
│   │   ├── database.py             #   数据库连接
│   │   └── main.py                 #   🚀 入口
│   ├── scripts/                    #   初始化脚本
│   ├── pyproject.toml
│   └── requirements.txt
├── frontend/                       # Next.js 前端
│   ├── src/
│   │   ├── app/                    #   App Router 页面
│   │   │   ├── chat/page.tsx       #     对话
│   │   │   ├── dashboard/page.tsx  #     仪表盘
│   │   │   ├── evaluation/page.tsx #     评估
│   │   │   ├── learning/page.tsx   #     资源中心
│   │   │   ├── login/page.tsx      #     登录/注册
│   │   │   ├── path/page.tsx       #     学习路径
│   │   │   ├── profile/page.tsx    #     画像构建
│   │   │   ├── page.tsx            #     根 → 重定向 /dashboard
│   │   │   ├── globals.css         #     全局样式
│   │   │   └── layout.tsx          #     根布局（Provider 包裹）
│   │   ├── components/             #   组件
│   │   │   └── layout/
│   │   │       ├── Navbar.tsx      #     导航栏
│   │   │       └── Providers.tsx   #     Context Provider 聚合
│   │   ├── hooks/                  #   自定义 hooks（空）
│   │   ├── lib/                    #   工具库
│   │   │   ├── api.ts              #     Axios 实例 + 接口封装
│   │   │   └── auth.ts             #     认证工具
│   │   ├── stores/                 #   Zustand 状态
│   │   │   └── index.ts            #     4 个 Store（auth/profile/resources/path）
│   │   ├── types/                  #   TypeScript 类型
│   │   │   └── index.ts            #     全局类型定义
│   │   └── middleware.ts           #   路由鉴权中间件
│   ├── tailwind.config.ts
│   ├── next.config.js
│   └── package.json
├── docs/                           # 文档
│   ├── api.md                      #   API 接口文档
│   ├── architecture.md             #   架构设计文档
│   ├── requirements.md             #   软件杯赛题需求
│   ├── PROJECT_CONTEXT.md          #   项目上下文（本文档）
│   └── images/
├── docker-compose.yml              # PostgreSQL + Redis + Qdrant
├── nginx.conf                      # 生产环境反向代理
├── requirements.docx               # 赛题原始需求 Word
└── README.md
```

---

## 二、前端技术栈

| 类别 | 技术 |
|---|---|
| 框架 | Next.js 14 (App Router) + TypeScript |
| 渲染 | 全部页面为 Client Component (`'use client'`) |
| 样式 | Tailwind CSS 3.4 + 自定义 primary/accent 色彩体系 |
| 动画 | Framer Motion (页面入场、列表 stagger、悬停效果) |
| 状态管理 | Zustand (4 个 Store: auth / profile / resources / path) |
| HTTP 请求 | Axios (封装 ApiClient，含拦截器、401 自动跳转) |
| 服务端状态 | TanStack React Query (已声明依赖，但未使用) |
| 工具库 | react-hot-toast, react-markdown, date-fns, clsx+tailwind-merge |

**入口文件**: `frontend/src/app/layout.tsx` — 设置字体、Provider 包裹、全局元信息。

### 路由结构

| 路径 | 文件 | 描述 |
|---|---|---|
| `/` | `page.tsx` | 根路由 → 自动重定向到 `/dashboard` |
| `/login` | `login/page.tsx` | 登录/注册（含邮箱验证码） |
| `/dashboard` | `dashboard/page.tsx` | 仪表盘（统计卡片 + 快速操作） |
| `/chat` | `chat/page.tsx` | AI 智能对话（含快捷操作 / mock fallback） |
| `/profile` | `profile/page.tsx` | 对话式画像构建（8 个维度，前端自包含） |
| `/learning` | `learning/page.tsx` | 资源中心（7 类 mock 资源 + 分类筛选 + 详情弹窗） |
| `/path` | `path/page.tsx` | 学习路径（5 阶段时间线，前端自包含） |
| `/evaluation` | `evaluation/page.tsx` | 评估仪表盘（硬编码数据） |

**中间件**: `middleware.ts` — 基于 Cookie `auth_token` 的路由保护，`/login` 为公开路由。

---

## 三、后端技术栈

| 类别 | 技术 |
|---|---|
| 框架 | Python 3.9+ + FastAPI |
| ORM | SQLAlchemy 2.0 (async) + Alembic 迁移 |
| 数据库驱动 | asyncpg (异步) / psycopg2 (同步, alembic) |
| 认证 | JWT (python-jose) + bcrypt 密码哈希 |
| 多智能体 | LangGraph (StateGraph + MemorySaver) |
| LLM 接入 | 工厂模式 (4 个 Provider: 讯飞星火 / DeepSeek / 通义千问 / 智谱 GLM) |
| 向量检索 | Qdrant + Sentence-Transformers (BAAI/bge-large-zh-v1.5) |
| 缓存 | Redis (asyncio) |
| 配置 | Pydantic Settings (.env 加载) |
| 日志 | Loguru |
| 邮件 | smtplib (QQ 邮箱 SMTP, .env 已配置) |

**入口文件**: `backend/app/main.py` — FastAPI 应用实例，含 lifespan 生命周期、CORS、路由挂载、全局异常处理、健康检查。

### API 接口

| 模块 | 路由 | 方法 | 描述 |
|---|---|---|---|
| 认证 | `/api/v1/auth/register` | POST | 注册 |
| | `/api/v1/auth/login` | POST | 登录 → JWT |
| | `/api/v1/auth/me` | GET | 获取当前用户 |
| | `/api/v1/auth/send-email-code` | POST | 发送邮箱验证码 |
| | `/api/v1/auth/verify-email-code` | POST | 校验邮箱验证码 |
| 画像 | `/api/v1/profile/create` | POST | 创建画像 |
| | `/api/v1/profile/me` | GET | 当前用户画像 |
| | `/api/v1/profile/{id}` | GET | 获取指定画像 |
| 对话 | `/api/v1/chat/session` | POST | 创建会话 |
| | `/api/v1/chat/sessions` | GET | 会话列表 |
| | `/api/v1/chat/{id}/messages` | GET | 消息历史 |
| | `/api/v1/chat/send` | POST | 发送消息 → 多智能体 |
| 学习 | `/api/v1/learning/content` | GET | 内容列表 |
| | `/api/v1/learning/content/{id}` | GET | 内容详情 |
| | `/api/v1/learning/path/{profile_id}` | GET | 学习路径 |
| 资源 | `/api/v1/resources/generate` | POST | 多智能体生成资源 |
| | `/api/v1/resources/profile-resources` | GET | 按画像推荐资源 |
| 评估 | `/api/v1/evaluation/submit` | POST | 提交评估 |
| | `/api/v1/evaluation/progress/{profile_id}` | GET | 获取进度 |
| 健康 | `/api/v1/health` | GET | 健康检查 |

---

## 四、数据库、环境变量、配置文件

### 数据库（3 个 Docker 服务）

| 服务 | 用途 | 镜像 |
|---|---|---|
| PostgreSQL 16 | 业务数据（用户、画像、对话、学习内容） | `postgres:16-alpine` |
| Redis 7 | 缓存、邮箱验证码存储 | `redis:7-alpine` |
| Qdrant | 向量数据库（学习资源语义检索） | `qdrant/qdrant:latest` |

### 数据库表（7 张）

| 表 | 描述 |
|---|---|
| `users` | 用户（含密码哈希、邮箱） |
| `learner_profiles` | 学习者画像（dimensions 为 JSONB） |
| `chat_sessions` | 对话会话 |
| `chat_messages` | 消息（text / markdown / mindmap 等类型） |
| `learning_contents` | 学习内容 |
| `learning_paths` | 学习路径（nodes 为 JSONB） |
| `evaluations` | 评估记录 |

### 环境变量类别（.env）

- **LLM Provider**: 讯飞星火（首选，但 key 为占位符）、DeepSeek、通义千问、智谱
- **数据库**: PostgreSQL 连接参数（默认 `localhost:5432`, 用户 `edulab`）
- **Redis**: `localhost:6379`
- **Qdrant**: `localhost:6333`, collection: `learning_resources`
- **JWT**: SECRET (占位符), HS256, 24h 过期
- **SMTP**: QQ 邮箱（已实际配置完整账号密码）
- **前端**: `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`

### 主要配置文件

| 文件 | 作用 |
|---|---|
| `.env` / `.env.example` | 环境变量 |
| `docker-compose.yml` | Docker 编排（数据库层） |
| `nginx.conf` | 生产环境反向代理（HTTPS + 路由） |
| `backend/pyproject.toml` | Poetry 依赖声明 |
| `backend/requirements.txt` | pip 依赖 |
| `frontend/package.json` | npm 依赖 |
| `frontend/next.config.js` | Next.js 配置（rewrites 代理 API） |
| `frontend/tailwind.config.ts` | Tailwind 主题色 + 动画 |
| `frontend/tsconfig.json` | TypeScript 配置 |
| `backend/app/config.py` | 后端 Pydantic 配置(读取 .env) |

---

## 五、当前已实现功能

### 前端（UI 完整，但数据多为 Mock）

- [x] **登录/注册** — 完整流程，含邮箱验证码（注册必须验证邮箱）
- [x] **仪表盘** — 问候语、4 个统计卡片、4 个快速操作入口、活动时间线
- [x] **对话式画像构建** — 8 个渐进式问题 → 前端关键词分析 → 评分 → 维度卡片展示
- [x] **AI 智能对话** — 消息界面 + 快捷操作按钮 + Markdown 渲染 + 模拟回复
- [x] **资源中心** — 7 类 mock 数据 → 分类筛选 + 搜索 + 详情弹窗（含按类型渲染器）
- [x] **学习路径** — 5 阶段时间线、进度条、完成状态切换
- [x] **学习评估** — 4 指标展示（带动画柱状图）+ 优势/不足/建议 + 趋势图

### 后端（API 路由完整，但多无真实 LLM 调用）

- [x] **认证系统** — JWT 登录/注册/邮箱验证码/Token 校验
- [x] **对话管理** — 会话 CRUD、消息存储
- [x] **画像 CRUD** — 创建/查询
- [x] **学习内容 CRUD** — 列表/详情
- [x] **评估提交 + 进度** — 入库 + 统计
- [x] **多智能体编排** — LangGraph 图已构建（Router → Profiling / ContentGen / QA / PathPlanning / Evaluation）
- [x] **Agent Nodes** — 5 个节点完整实现（模板 / 规则引擎）
- [x] **LLM Provider 工厂** — 4 个 Provider 注册、自动 fallback
- [x] **RAG 检索架构** — Qdrant 集合管理、文档插入、语义检索、Prompt 构建
- [x] **Embedding** — BAAI/bge-large-zh-v1.5

---

## 六、Mock 功能（待替换）

| 页面 / 模块 | Mock 情况 |
|---|---|
| `evaluation/page.tsx` | 全部数据是硬编码 `assessmentData`，无 API 调用 |
| `learning/page.tsx` | 7 条 mock 资源数据，生成按钮是 `setTimeout` 假动画 |
| `path/page.tsx` | 5 阶段时间线前端硬编码，`toggleNode` 只在本地切换 |
| `dashboard/page.tsx` | 统计卡片是假数据 |
| `chat/page.tsx` | API 调用失败后使用 `generateMockResponse()` 降级 |
| `profile/page.tsx` | 8 个问题 + 前端关键词评分，全在前端完成，后端 API 未实际调用 |

---

## 七、关键未实现功能

- [ ] **任何 Agent 节点未实际调用 LLM** — nodes.py 中 5 个 Agent 全是纯 Python 规则引擎/模板输出
- [ ] **RAG 与 Agent 未打通** — `rag_service.py` 和 `retriever.py` 已实现，但没有任何 Agent 调用它
- [ ] **前端流式 SSE 响应** — `api.ts` 已实现 `stream()` 方法，但前端使用普通 POST，后端无 stream endpoint
- [ ] **TanStack React Query** — 已声明依赖但未使用
- [ ] **后端 .venv 是 Python 3.9** — pyproject.toml 声明 `^3.12`，实际运行 Python 3.9
- [ ] **根目录 agent/** — 遗留旧版 Agent 原型，与 `backend/app/agents/` 功能重复

---

## 八、潜在问题

1. **`nodes.py` 调用了 `random.choice`** — LangGraph 确定性重放依赖纯函数，随机数破坏一致性
2. **`nodes.py` 行数达 1129 行** — 所有 Agent 逻辑在一个文件中
3. **`_generate_code_case` 的 `topic.replace(" ", "")`** — 中文主题替换空格行为正常，英文主题如 "machine learning" 会变成 "machinelearning"
4. **Alembic migration 路径** — `env.py` 中 `from app.models import *` 要求 PYTHONPATH 正确设置
5. **`POSTGRES_HOST=localhost`** — Docker Compose 启动时服务名为 `postgres`，实际 host 应为 `postgres`
6. **`NEXT_PUBLIC_API_BASE_URL`** — 前端可能走 Next.js rewrites 也可能直连，chat/page.tsx 硬编码了 `http://localhost:8000` 而非使用环境变量

---

## 九、启动命令

### 启动数据库
```bash
docker compose up -d postgres redis qdrant
```

### 启动后端
```bash
cd backend
source .venv/bin/activate
PYTHONPATH=. alembic upgrade head
PYTHONPATH=. uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 启动前端
```bash
cd frontend
npm run dev
```

---

## 十、不可随意修改的文件

| 文件 | 原因 |
|---|---|
| `docker-compose.yml` | 基础设施编排，改错会导致数据库/缓存不可用 |
| `nginx.conf` | 生产环境反向代理，影响线上部署 |
| `backend/alembic/` | 数据库迁移历史，包含已应用的 revision。追加新的，不要手动修改已有 |
| `backend/app/database.py` | SQLAlchemy 引擎和 Session 工厂的全局配置 |
| `backend/app/config.py` | 配置加载的基类，影响所有模块的环境变量读取 |
| `backend/app/main.py` | FastAPI 应用入口，CORS / 路由 / 异常处理 |
| `backend/app/core/security.py` | JWT / bcrypt 底层实现，影响整个认证体系 |
| `backend/app/schemas/__init__.py` | 所有 API 请求/响应结构，前端类型适配于此 |
| `frontend/src/middleware.ts` | 路由鉴权中间件，修改可能破坏整个权限体系 |
| `frontend/next.config.js` | Next.js 配置，rewrites proxy 关系到后端通信 |
| `.env` | 敏感信息（SMTP 密码、API Key），不要提交到 git |
| `requirements.docx` | 赛题原始需求文档，不可修改 |

---

## 十一、第一开发目标

> **将《随机过程与排队论》PDF 建立为 Qdrant RAG 知识库，并让 QA Agent 实现真实的检索增强问答与页码引用。**

具体含义：
1. 将 PDF 文档解析为文本块（带页码元数据）
2. 通过 Sentence-Transformers (BAAI/bge-large-zh-v1.5) 生成向量嵌入
3. 存入 Qdrant `learning_resources` 集合
4. 在 QA Agent 节点中调用 `retriever.py` 进行语义检索
5. 将检索到的上下文（含页码）注入 LLM Prompt
6. 前端聊天页展示带有来源（页码）引用的真实回答

---

## 十二、当前开发优先级

### P0 — 核心链路打通

- [ ] **PDF 入库 Qdrant** — 解析《随机过程与排队论》PDF，分块 + 嵌入 + 存入向量库
- [ ] **检索验证** — 手动测试 Qdrant 查询，确认语义检索返回相关段落及页码
- [ ] **QA Agent 接入 RAG + LLM** — `qa_agent_node` 改为调用 `LLMFactory.chat()` 和 `retrieve_context()`，生成带引用回答
- [ ] **聊天页展示真实回答与来源** — `chat/page.tsx` 渲染带页码引用的回答，去除 mock fallback

### P1 — 增强真实感

- [ ] **ProfileAgent 接入真实 LLM** — `profiling_agent_node` 改用 LLM 分析用户输入，提取画像维度
- [ ] **学习路径接入真实数据** — `path/page.tsx` 调用后端 API，移除前端硬编码
- [ ] **资源生成接入真实 LLM** — ContentGen Agent 调用 LLM 按画像动态生成资源

### P2 — 工程优化

- [ ] **SSE 流式输出** — 后端加 `/chat/send/stream` endpoint，前端切换到 `api.stream()` 流式接收
- [ ] **去除全部前端 Mock** — 逐一替换 `dashboard`、`learning`、`path`、`evaluation` 中的假数据
- [ ] **拆分过大的 nodes.py** — 按 Agent 类型拆分为独立文件
- [ ] **清理根目录遗留 agent/** — 删除与 `backend/app/agents/` 重复的旧版原型
