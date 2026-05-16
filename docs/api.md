# API 接口文档

## 基础信息

- **Base URL**: `/api/v1`
- **认证方式**: Bearer Token (JWT)
- **内容类型**: `application/json`
- **流式响应**: Server-Sent Events (SSE)

## 认证

### POST /auth/register

注册新用户。

**Request:**
```json
{
  "username": "string (2-64字符)",
  "email": "string (邮箱格式)",
  "password": "string (6-128字符)"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "username": "string",
    "email": "string",
    "is_active": true,
    "created_at": "datetime"
  }
}
```

### POST /auth/login

用户登录，获取 Token。

**Request:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "access_token": "jwt_token",
    "token_type": "bearer",
    "expires_in": 24
  }
}
```

### GET /auth/me

获取当前用户信息。

**Headers:** `Authorization: Bearer <token>`

## 画像

### POST /profile/create

创建学习者画像。

**Request:**
```json
{
  "name": "string",
  "dimensions": [
    {
      "name": "knowledge",
      "value": 65,
      "label": "知识水平",
      "description": "当前学科基础知识掌握程度"
    }
  ]
}
```

**维度的最小值要求:** 6 个 (知识水平、认知风格、易错点、偏好形式、学习速度、理解深度)

### GET /profile/me

获取当前用户画像。

### GET /profile/{profile_id}

获取指定画像详情。

## 对话

### POST /chat/session

创建对话会话。

**Request:**
```json
{
  "title": "新会话"
}
```

### GET /chat/sessions

获取用户的会话列表。

### GET /chat/{session_id}/messages

获取会话中的消息历史。

### POST /chat/send

发送消息（普通模式）。

**Request:**
```json
{
  "session_id": "uuid",
  "content": "用户消息"
}
```

**SSE 流式（待实现）:**
```
Event: message
data: {"type": "text", "content": "回复片段"}

Event: done
data: [DONE]
```

## 学习内容

### GET /learning/content

获取学习内容列表。

**Query Params:**
- `subject` (可选): 学科过滤
- `type` (可选): 类型过滤

### GET /learning/content/{content_id}

获取学习内容详情。

### GET /learning/path/{profile_id}

获取学习路径。

## 评估

### POST /evaluation/submit

提交学习评估。

**Request:**
```json
{
  "content_id": "uuid",
  "score": 85,
  "feedback": "optional feedback"
}
```

### GET /evaluation/progress/{profile_id}

获取学习进度报告。
