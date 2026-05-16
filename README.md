# AI 个性化教育平台

> 基于大模型的个性化资源生成与学习多智能体系统  
> 第十五届中国软件杯大赛 · A组赛题 · 科大讯飞出题

---

## 📋 目录

- [项目概述](#项目概述)
- [技术栈](#技术栈)
- [快速开始](#快速开始)
- [项目结构](#项目结构)
- [开发指南](#开发指南)
- [API 文档](#api-文档)
- [部署说明](#部署说明)
- [贡献指南](#贡献指南)

---

## 🎯 项目概述

本系统旨在利用大语言模型（LLM）与多智能体（Multi-Agent）架构，为每个学习者构建个性化画像，动态生成适配的学习内容，规划最优学习路径，并提供智能答疑与评估反馈，实现"因材施教"的落地。

**核心能力：**

- 🧑‍🎓 **对话式画像** — 通过自然对话收集用户特征，构建多维度学习者画像
- 📚 **个性化内容生成** — 基于画像动态生成讲解、思维导图、题目、扩展阅读等多种形式的学习资源
- 🗺️ **学习路径规划** — 智能规划并动态调整个性化学习路径
- 💬 **智能答疑** — 结合 RAG 的多轮对话 AI 答疑
- 📊 **评估反馈** — 自动评估、跟踪学习进度，自适应调整策略

---

## 🛠️ 技术栈

### 前端

| 技术 | 用途 |
|------|------|
| Next.js 14 (App Router) | React 框架，服务端渲染 |
| React 18 | UI 库 |
| TypeScript | 类型安全 |
| Tailwind CSS | 原子化样式 |
| Zustand | 轻量状态管理 |
| React Query (TanStack Query) | 服务端数据请求/缓存 |
| Shadcn/ui | 高质量 UI 组件库 |

### 后端

| 技术 | 用途 |
|------|------|
| Python 3.12 | 运行环境 |
| FastAPI | Web 框架 |
| Pydantic v2 | 数据校验 |
| SQLAlchemy 2.0 | ORM |
| Alembic | 数据库迁移 |
| Celery | 异步任务队列 |

### Agent / AI

| 技术 | 用途 |
|------|------|
| LangGraph | 多智能体编排 / 状态图 |
| LangChain | LLM 调用 / 工具链 |
| Qdrant | 向量数据库 |
| Sentence-Transformers | Embedding 模型 |

### LLM Provider（可替换）

| Provider | 优先级 | 状态 |
|----------|--------|------|
| 讯飞星火 Spark | 🥇 首选 | ✅ |
| DeepSeek | 🥈 备选 | ✅ |
| 通义千问 Qwen | 🥈 备选 | ✅ |
| 智谱 GLM | 🥈 备选 | ✅ |

### 基础设施

| 技术 | 用途 |
|------|------|
| PostgreSQL 16 | 关系型数据库 |
| Redis 7 | 缓存 / 任务队列 / Agent 状态 |
| Docker Compose | 容器化编排 |
| Nginx | 反向代理 |

---

## 🚀 快速开始

### 前置要求

- Docker & Docker Compose v2.22+
- Node.js 20+（本地开发）
- Python 3.12+（本地开发）
- 讯飞星火 API Key（[申请地址](https://xinghuo.xfyun.cn/)）

### 1️⃣ 克隆 & 进入项目

```bash
git clone <your-repo-url>
cd ai-education-platform
```

### 2️⃣ 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入你的 API Key 和数据库配置
```

必要变量：

```env
# LLM API
XUNFEI_APP_ID=your_app_id
XUNFEI_API_KEY=your_api_key
XUNFEI_API_SECRET=your_api_secret

# 可选 Provider
DEEPSEEK_API_KEY=your_deepseek_key
QWEN_API_KEY=your_qwen_key
ZHIPU_API_KEY=your_zhipu_key

# Database
POSTGRES_USER=edulab
POSTGRES_PASSWORD=edulab_pass
POSTGRES_DB=ai_education

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Qdrant
QDRANT_HOST=qdrant
QDRANT_PORT=6333
```

### 3️⃣ Docker Compose 一键启动

```bash
docker compose up --build -d
```

等待所有服务就绪后访问：

| 服务 | 地址 |
|------|------|
| 前端 | http://localhost:3000 |
| 后端 API | http://localhost:8000 |
| API 文档 | http://localhost:8000/docs |
| Qdrant UI | http://localhost:6333/dashboard |

### 4️⃣ 初始化数据库

```bash
# 执行数据库迁移
docker exec backend alembic upgrade head

# 可选：导入种子数据
docker exec backend python scripts/seed_data.py
```

### 5️⃣ 本地开发（无 Docker）

**后端：**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**前端：**

```bash
cd frontend
npm install
npm run dev
```

---

## 📁 项目结构

```
ai-education-platform/
├── .gitignore
├── README.md
├── .env.example              # 环境变量模板
├── docker-compose.yml        # 容器编排
├── Dockerfile.frontend
├── Dockerfile.backend
│
├── frontend/                 # Next.js 前端
│   ├── src/
│   │   ├── app/              # App Router 路由 & 页面
│   │   ├── components/       # UI 组件（按模块分组）
│   │   │   ├── ui/           # 通用基础组件
│   │   │   ├── layout/       # 布局组件
│   │   │   ├── chat/         # 对话交互组件
│   │   │   ├── learning/     # 学习内容展示组件
│   │   │   ├── profile/      # 画像组件
│   │   │   └── dashboard/    # 仪表盘组件
│   │   ├── lib/              # 工具函数 / API 客户端
│   │   ├── hooks/            # 自定义 Hooks
│   │   ├── stores/           # Zustand 状态管理
│   │   └── types/            # TypeScript 类型定义
│   ├── public/               # 静态资源
│   ├── tailwind.config.ts
│   └── package.json
│
├── backend/                  # FastAPI 后端
│   ├── app/
│   │   ├── main.py           # 应用入口
│   │   ├── config.py         # 配置管理
│   │   ├── database.py       # 数据库连接
│   │   ├── api/
│   │   │   └── v1/           # API v1 路由
│   │   │       ├── router.py # 路由聚合
│   │   │       ├── auth.py   # 认证
│   │   │       ├── profile.py# 画像
│   │   │       ├── learning.py# 学习
│   │   │       ├── chat.py   # 对话
│   │   │       └── evaluation.py# 评估
│   │   ├── core/             # 核心工具
│   │   │   ├── security.py   # JWT / 加密
│   │   │   └── exceptions.py # 异常处理
│   │   ├── models/           # SQLAlchemy 模型
│   │   ├── schemas/          # Pydantic Schema
│   │   ├── services/         # 业务服务
│   │   ├── agents/           # LangGraph 智能体
│   │   ├── llm/              # LLM Provider 封装
│   │   └── rag/              # RAG 检索增强生成
│   ├── scripts/              # 数据库脚本
│   ├── alembic/              # 数据库迁移
│   └── requirements.txt
│
├── agent/                    # LangGraph Agent 核心
│   ├── graph.py              # Agent 图定义
│   ├── nodes.py              # 节点函数
│   ├── state.py              # 状态定义
│   └── tools.py              # 工具函数
│
└── docs/                     # 项目文档
    ├── requirements.md       # 需求文档
    ├── architecture.md       # 架构设计
    ├── api.md                # API 接口文档
    └── images/               # 文档配图
```

---

## 🧑‍💻 开发指南

### 后端开发

**添加新的 API 路由：**

1. 在 `app/api/v1/` 下创建路由文件
2. 在 `app/api/v1/router.py` 中注册
3. 在 `app/schemas/` 定义请求/响应模型
4. 在 `app/services/` 实现业务逻辑

**添加新的 LLM Provider：**

1. 在 `app/llm/` 下创建 Provider（继承 `BaseLLM`）
2. 在 `app/llm/__init__.py` 注册
3. 在 `.env` 中添加对应的 API Key

### 前端开发

**页面路由：**

- `/` — 首页 / 仪表盘
- `/chat` — 对话式画像
- `/profile` — 学习者画像
- `/learning` — 学习内容
- `/path` — 学习路径

### Agent 开发

Agent 基于 LangGraph 的状态图编排，核心在 `agent/` 目录。参考 `agent/graph.py` 添加新的 Agent 节点。

---

## 📚 API 文档

启动后端后自动生成：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

主要接口：

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/auth/login` | 用户登录 |
| POST | `/api/v1/profile/create` | 创建画像 |
| GET  | `/api/v1/profile/{id}` | 获取画像 |
| POST | `/api/v1/chat/session` | 创建对话会话 |
| POST | `/api/v1/chat/send` | 发送消息（SSE 流式） |
| GET  | `/api/v1/learning/content` | 获取学习内容 |
| POST | `/api/v1/learning/path` | 规划/调整学习路径 |
| POST | `/api/v1/evaluation/submit` | 提交评估 |
| GET  | `/api/v1/evaluation/progress` | 获取学习进度 |

---

## 🐳 部署说明

### 生产部署

```bash
# 使用生产配置
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

### 环境变量

所有敏感配置通过 `.env` 注入，切勿提交到 Git。

### 数据持久化

Docker Compose 已配置命名卷，数据库和向量数据不会因容器重启丢失。

```bash
# 查看数据卷
docker volume ls | grep ai-education

# 备份数据库
docker exec postgres pg_dump -U edulab ai_education > backup.sql
```

---

## 🤝 贡献指南

1. Fork 项目
2. 创建 feature branch: `git checkout -b feat/your-feature`
3. 提交修改: `git commit -m "feat: add something"`
4. 推送到分支: `git push origin feat/your-feature`
5. 发起 Pull Request

**提交信息规范：** 遵循 [Conventional Commits](https://www.conventionalcommits.org/)

---

## 📄 许可

本作品著作权归参赛团队所有，大赛规则另有约定的从其约定。

---

> 答疑 QQ 群：1072584310  
> 出题企业：科大讯飞股份有限公司
