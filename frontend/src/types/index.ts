/**
 * 前端类型定义 — AI 教育平台
 */

// ─── 学习者画像 ──────────────────────────────────

export interface LearnerProfile {
  id: string;
  userId: string;
  name: string;
  dimensions: ProfileDimension[];
  summary: string;
  createdAt: string;
  updatedAt: string;
}

export interface ProfileDimension {
  name: string;
  value: number; // 0-100
  label: string;
  description?: string;
}

// ─── 对话 ────────────────────────────────────────

export interface ChatSession {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
}

export interface ChatMessage {
  id: string;
  sessionId: string;
  role: "user" | "assistant" | "system";
  content: string;
  contentType: MessageContentType;
  metadata?: Record<string, unknown>;
  createdAt: string;
}

export type MessageContentType =
  | "text"
  | "markdown"
  | "mindmap"
  | "quiz"
  | "code"
  | "image";

// ─── 学习内容 ────────────────────────────────────

export interface LearningContent {
  id: string;
  title: string;
  type: LearningContentType;
  subject: string;
  difficulty: 1 | 2 | 3 | 4 | 5;
  content: string;
  description?: string;
  tags: string[];
  createdAt: string;
}

export type LearningContentType =
  | "explanation"
  | "mindmap"
  | "quiz"
  | "reading"
  | "video"
  | "code";

// ─── 学习路径 ────────────────────────────────────

export interface LearningPath {
  id: string;
  profileId: string;
  goal: string;
  nodes: LearningPathNode[];
  progress: number;
  createdAt: string;
  updatedAt: string;
}

export interface LearningPathNode {
  id: string;
  title: string;
  description: string;
  status: "pending" | "in_progress" | "completed" | "skipped";
  order: number;
  estimatedMinutes: number;
  contentType: LearningContentType;
  prerequisites: string[];
}

// ─── 评估 ────────────────────────────────────────

export interface Evaluation {
  id: string;
  contentId: string;
  score: number;
  feedback: string;
  submittedAt: string;
}

export interface LearningProgress {
  profileId: string;
  totalContents: number;
  completedContents: number;
  averageScore: number;
  timeSpentMinutes: number;
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
}

// ─── API 响应 ────────────────────────────────────

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: ApiError;
  meta?: PaginationMeta;
}

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, string[]>;
}

export interface PaginationMeta {
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
}

// ─── SSE 流式响应 ────────────────────────────────

export interface StreamChunk {
  type: "text" | "done" | "error";
  content?: string;
  metadata?: Record<string, unknown>;
}
