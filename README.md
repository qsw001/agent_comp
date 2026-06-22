# 说明文档

## 前端

运行
```
npm run build
npm run dev
```

## 后端

运行
```
source .venv/bin/activate
PYTHONPATH=. alembic upgrade head
PYTHONPATH=. uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

## 数据库等
运行

```docker compose up -d postgres redis qdrant```