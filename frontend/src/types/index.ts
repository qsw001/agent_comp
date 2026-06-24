// ── API 类型定义 ──

export interface ApiResponse<T = any> {
  success: boolean
  message?: string
  data?: T
  error?: { code: string; message: string }
}

// ── 用户 ──
export interface User {
  id: string
  username: string
  email?: string
  major?: string
}

// ── 画像维度 ──
export interface ProfileDimension {
  name: string
  value: number
  label: string
  description: string
}

// ── 学习画像 ──
export interface LearnerProfile {
  id: string
  user_id: string
  name: string
  summary?: string
  dimensions: Record<string, { value: number; label: string; description: string }>
  status: string
  created_at: string
  updated_at: string
}

// ── 学习资源 ──
export type ResourceType = 'document' | 'mindmap' | 'quiz' | 'reading' | 'video' | 'code' | 'slides'

export interface LearningResource {
  id: string
  type: ResourceType
  title: string
  content: any
  difficulty: string
  tags: string[]
  created_at?: string
}

// ── 学习路径节点 ──
export interface PathNode {
  order: number
  title: string
  description: string
  resource_types: ResourceType[]
  estimated_hours: number
  completed: boolean
}

// ── 学习路径 ──
export interface LearningPath {
  id: string
  profile_id: string
  goal: string
  nodes: PathNode[]
  progress: number
  created_at: string
  updated_at: string
}

// ── RAG 引用来源 ──
export interface Citation {
  source_file: string
  page_number: number
  chapter: string
  chunk_id: string
  score: number
  content_snippet: string
}

// ── 聊天消息元数据 ──
export interface ChatMessageMetadata {
  agent_used?: string
  profile_dimensions_count?: number
  profile_complete?: boolean
  citations?: Citation[]
  retrieval_used?: boolean
  confidence?: number | null
  resources?: any[]
  assessment?: any
  error?: string
  [key: string]: any
}

// ── 聊天消息 ──
export interface ChatMessage {
  id: string
  session_id: string
  role: 'user' | 'assistant'
  content: string
  content_type: string
  metadata?: ChatMessageMetadata
  created_at: string
}

// ── 聊天会话 ──
export interface ChatSession {
  id: string
  title: string
  created_at: string
  updated_at: string
}

// ── 评估 ──
export interface Assessment {
  id: string
  profile_id: string
  content_id: string
  score: number
  feedback: string
  submitted_at: string
}

// ── 学习进度 ──
export interface LearningProgress {
  profile_id: string
  total_contents: number
  completed_contents: number
  average_score: number
  time_spent_minutes: number
  strengths: string[]
  weaknesses: string[]
  recommendations: string[]
}

// ── 资源生成请求 ──
export interface ResourceGenerateRequest {
  topic: string
  types: ResourceType[]
  profile_dims?: ProfileDimension[]
}

// ── 长期学习记忆 ──
export interface Memory {
  id: string
  memory_type: string
  content: string
  importance: number
  source_message_id: string | null
  created_at: string
  updated_at: string
}

// ── 资源类型元数据 ──
export const RESOURCE_TYPE_META: Record<ResourceType, { name: string; icon: string; color: string }> = {
  document: { name: '课程讲解', icon: '📖', color: '#3B82F6' },
  mindmap:   { name: '思维导图', icon: '🧠', color: '#8B5CF6' },
  quiz:      { name: '练习题',   icon: '📝', color: '#F59E0B' },
  reading:   { name: '拓展阅读', icon: '📚', color: '#10B981' },
  video:     { name: '教学视频', icon: '🎬', color: '#EF4444' },
  code:      { name: '实操案例', icon: '💻', color: '#06B6D4' },
  slides:    { name: '教学PPT',  icon: '📊', color: '#EC4899' },
}
