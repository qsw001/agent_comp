'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Trash2, Bookmark, AlertCircle, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { Navbar } from '@/components/layout/Navbar'
import { api } from '@/lib/api'
import type { Memory } from '@/types'

// ── memory_type → 中文名映射 ──
const TYPE_LABELS: Record<string, string> = {
  learning_goal: '学习目标',
  knowledge_level: '知识基础',
  weak_point: '薄弱点',
  learning_preference: '学习偏好',
  course_context: '学习进度',
  personal_fact: '学习背景',
}

const FILTER_OPTIONS = [
  { key: null, label: '全部' },
  { key: 'learning_goal', label: '学习目标' },
  { key: 'knowledge_level', label: '知识基础' },
  { key: 'weak_point', label: '薄弱点' },
  { key: 'learning_preference', label: '学习偏好' },
  { key: 'course_context', label: '学习进度' },
  { key: 'personal_fact', label: '学习背景' },
]

// ── importance → 分级 ──
function importanceLabel(val: number): { text: string; color: string } {
  if (val >= 0.7) return { text: '高', color: 'bg-orange-100 text-orange-700' }
  if (val >= 0.4) return { text: '中', color: 'bg-blue-100 text-blue-700' }
  return { text: '低', color: 'bg-gray-100 text-gray-600' }
}

// ── 进出动画配置 ──
const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.06 } },
}

const item = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0 },
}

export default function MemoriesPage() {
  const [memories, setMemories] = useState<Memory[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedType, setSelectedType] = useState<string | null>(null)
  const [deleting, setDeleting] = useState<Set<string>>(new Set())

  const fetchMemories = async (type: string | null) => {
    setLoading(true)
    setError(null)
    try {
      const url = type ? `/memories?memory_type=${encodeURIComponent(type)}` : '/memories'
      const res = await api.get<Memory[]>(url)
      if (res.success && res.data) {
        setMemories(res.data)
      } else {
        setError(res.error?.message || '加载失败')
      }
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || err?.message || '请求失败，请稍后重试')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchMemories(selectedType)
  }, [selectedType])

  const handleDelete = async (mem: Memory) => {
    if (!confirm(`确定要删除这条记忆吗？\n\n"${mem.content}"`)) return

    setDeleting((prev) => new Set(prev).add(mem.id))
    try {
      const res = await api.delete<{ message: string }>(`/memories/${mem.id}`)
      if (res.success) {
        setMemories((prev) => prev.filter((m) => m.id !== mem.id))
        toast.success('已删除')
      } else {
        toast.error(res.error?.message || '删除失败')
      }
    } catch (err: any) {
      toast.error(err?.response?.data?.error?.message || err?.message || '删除失败，请稍后重试')
    } finally {
      setDeleting((prev) => {
        const next = new Set(prev)
        next.delete(mem.id)
        return next
      })
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      <Navbar />

      <motion.main
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8"
      >
        {/* 标题 */}
        <motion.div initial={{ opacity: 0, y: -12 }} animate={{ opacity: 1, y: 0 }}>
          <h1 className="text-2xl font-bold tracking-tight">学习记忆</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            系统会根据你明确表达的学习目标、薄弱点和偏好生成记忆，用于调整后续讲解方式。
            你可以随时删除不需要的记忆。
          </p>
        </motion.div>

        {/* 筛选栏 */}
        <div className="mt-6 flex flex-wrap gap-2">
          {FILTER_OPTIONS.map((opt) => (
            <motion.button
              key={opt.label}
              whileHover={{ scale: 1.04 }}
              whileTap={{ scale: 0.96 }}
              onClick={() => setSelectedType(opt.key)}
              className={`rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
                selectedType === opt.key
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'bg-white/80 text-muted-foreground hover:bg-white hover:text-foreground border border-border/40'
              }`}
            >
              {opt.label}
            </motion.button>
          ))}
        </div>

        {/* 加载中 */}
        {loading && (
          <div className="mt-12 flex flex-col items-center justify-center py-20 text-muted-foreground">
            <Loader2 className="h-8 w-8 animate-spin" />
            <p className="mt-3 text-sm">加载中...</p>
          </div>
        )}

        {/* 错误 */}
        {!loading && error && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="mt-8 flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800"
          >
            <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-red-500" />
            <div>
              <p className="font-medium">加载失败</p>
              <p className="mt-1 text-red-600">{error}</p>
              <button
                onClick={() => fetchMemories(selectedType)}
                className="mt-2 text-sm font-medium text-red-700 underline underline-offset-2 hover:text-red-900"
              >
                重试
              </button>
            </div>
          </motion.div>
        )}

        {/* 空状态 */}
        {!loading && !error && memories.length === 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-12 flex flex-col items-center justify-center py-20 text-center"
          >
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-muted">
              <Bookmark className="h-8 w-8 text-muted-foreground" />
            </div>
            <h3 className="mt-4 text-lg font-medium">暂时没有学习记忆</h3>
            <p className="mt-2 max-w-md text-sm text-muted-foreground">
              你可以在聊天中告诉系统你的学习目标、薄弱点或讲解偏好。
            </p>
          </motion.div>
        )}

        {/* 记忆列表 */}
        {!loading && !error && memories.length > 0 && (
          <motion.div variants={container} initial="hidden" animate="show" className="mt-6 space-y-3">
            {memories.map((mem) => {
              const imp = importanceLabel(mem.importance)
              const isDeleting = deleting.has(mem.id)
              return (
                <motion.div
                  key={mem.id}
                  variants={item}
                  layout
                  className="group relative rounded-2xl border border-border/40 bg-white/80 backdrop-blur-sm shadow-sm transition-shadow hover:shadow-md"
                >
                  <div className="flex items-start gap-4 p-4 sm:p-5">
                    {/* 类型标签 */}
                    <span className={`shrink-0 rounded-full px-3 py-1 text-xs font-medium ${imp.color}`}>
                      {TYPE_LABELS[mem.memory_type] || mem.memory_type}
                    </span>

                    {/* 正文 */}
                    <div className="min-w-0 flex-1">
                      <p className="text-sm leading-relaxed text-foreground">{mem.content}</p>
                      <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
                        <span>重要性 · {imp.text}</span>
                        <span>更新于 {new Date(mem.updated_at).toLocaleString('zh-CN')}</span>
                      </div>
                    </div>

                    {/* 删除按钮 */}
                    <motion.button
                      whileHover={{ scale: 1.1 }}
                      whileTap={{ scale: 0.9 }}
                      disabled={isDeleting}
                      onClick={() => handleDelete(mem)}
                      className="shrink-0 rounded-lg p-2 text-muted-foreground opacity-0 transition-all hover:bg-red-50 hover:text-red-500 group-hover:opacity-100 disabled:opacity-50"
                      title="删除此记忆"
                    >
                      {isDeleting ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Trash2 className="h-4 w-4" />
                      )}
                    </motion.button>
                  </div>
                </motion.div>
              )
            })}
          </motion.div>
        )}

        {/* 底边距 */}
        <div className="h-12" />
      </motion.main>
    </div>
  )
}
