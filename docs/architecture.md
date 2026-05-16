# 架构设计文档

## 系统架构图

```mermaid
graph TB
    subgraph 前端层
        A[Next.js SSR]
        B[Tailwind CSS UI]
        C[Zustand 状态管理]
    end

    subgraph API 网关
        D[Nginx 反向代理]
    end

    subgraph 后端服务层
        E[FastAPI]
        F[Pydantic 校验]
        G[SQLAlchemy ORM]
    end

    subgraph AI 能力层
        H[LangGraph 多智能体]
        I[RAG 检索增强]
        J[LLM Provider 工厂]
    end

    subgraph 数据层
        K[(PostgreSQL)]
        L[(Redis 缓存)]
        M[(Qdrant 向量库)]
    end

    A --> D
    D --> E
    E --> F
    E --> G
    E --> H
    H --> I
    H --> J
    G --> K
    E --> L
    I --> M
```

## 多智能体架构

```mermaid
graph LR
    R[Router Agent] --> P[Profiling Agent]
    R --> C[Content Gen Agent]
    R --> Q[QA Agent]
    R --> PL[Path Planning Agent]
    R --> E[Evaluation Agent]
    P --> R
    C --> R
    Q --> R
    PL --> R
    E --> R
```

## 数据流

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant Agent
    participant LLM
    participant RAG
    participant DB

    User->>Frontend: 输入消息
    Frontend->>API: POST /chat/send
    API->>Agent: process_chat_message()
    Agent->>Agent: Router → QA Agent
    Agent->>RAG: retrieve_context(query)
    RAG-->>Agent: 相关文档
    Agent->>LLM: chat(messages + context)
    LLM-->>Agent: 回复内容
    Agent-->>API: agent_output
    API->>DB: 保存消息
    API-->>Frontend: SSE 流式回复
    Frontend-->>User: 显示回复
```

## 技术栈总览

| 层级 | 技术 | 用途 |
|------|------|------|
| 前端 | Next.js 14 + React 18 + TypeScript | Web UI |
| 样式 | Tailwind CSS | 原子化 CSS |
| 状态 | Zustand + TanStack Query | 客户端/服务端状态 |
| 后端 | Python 3.12 + FastAPI | API 服务 |
| ORM | SQLAlchemy 2.0 + Alembic | 数据库 |
| Agent | LangGraph + LangChain | 多智能体编排 |
| LLM | 讯飞星火 / DeepSeek / 通义千问 / 智谱 | 大模型 |
| RAG | Qdrant + Sentence-Transformers | 向量检索 |
| 数据库 | PostgreSQL 16 | 关系数据 |
| 缓存 | Redis 7 | 缓存/队列 |
| 部署 | Docker Compose | 容器化 |
