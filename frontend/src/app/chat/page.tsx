'use client'
import { useState, useRef, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Navbar } from '@/components/layout/Navbar'
import { Send, Sparkles, BookOpen, HelpCircle, Map, BarChart3, Loader2, ChevronDown, ChevronUp } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import type { Citation, ChatMessageMetadata } from '@/types'

type Msg = { role: 'user' | 'assistant'; content: string; metadata?: ChatMessageMetadata }

export default function ChatPage() {
  const [messages, setMessages] = useState<Msg[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [error, setError] = useState('')
  const chatEndRef = useRef<HTMLDivElement>(null)
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // 记录每条消息的 citations 展开/收起状态（key = 消息索引）
  const [expandedCitations, setExpandedCitations] = useState<Set<number>>(new Set())

  // ── 构建 citations 折叠标签文字 ──
  function citationsLabel(citations: Citation[]): string {
    const pages = [...new Set(citations.map((c) => c.page_number).filter(Boolean))]
      .sort((a, b) => a - b)
      .slice(0, 3)
    return pages.length > 0 ? `📖 参考教材 · ${pages.map((p) => `第 ${p} 页`).join(' · ')}` : '📖 参考教材'
  }

  function toggleCitations(idx: number) {
    setExpandedCitations((prev) => {
      const next = new Set(prev)
      if (next.has(idx)) next.delete(idx); else next.add(idx)
      return next
    })
  }

  // 快捷操作按钮
  const quickActions = [
    { icon: <BookOpen className="h-4 w-4" />, label: '生成学习资源', prompt: '请为机器学习生成全方位学习资源：课程讲解、思维导图、练习题、拓展阅读和实操案例' },
    { icon: <Map className="h-4 w-4" />, label: '规划学习路径', prompt: '帮我规划一条从头学习Python的学习路径' },
    { icon: <BarChart3 className="h-4 w-4" />, label: '评估学习效果', prompt: '帮我评估一下当前的学习效果' },
    { icon: <HelpCircle className="h-4 w-4" />, label: '智能答疑', prompt: '我有一个知识点不太理解，能帮我讲解一下吗？' },
  ]

  // ── 确保存在有效的聊天会话 ──
  async function ensureSession(): Promise<string | null> {
    if (sessionId) return sessionId
    setError('')
    try {
      const token = localStorage.getItem('auth_token')
      const res = await fetch(`${API_BASE}/chat/session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...(token && { Authorization: `Bearer ${token}` }) },
        body: JSON.stringify({ title: '新对话' }),
      })
      const data = await res.json()
      if (data.success && data.data?.id) {
        setSessionId(data.data.id)
        return data.data.id
      }
      setError('创建会话失败，请刷新页面后重试。')
      return null
    } catch {
      setError('网络异常，无法创建会话。请检查网络后重试。')
      return null
    }
  }

  const sendMessage = async (content: string) => {
    if (!content.trim() || loading) return

    // 首次发送前先创建会话
    const sid = await ensureSession()
    if (!sid) return

    const userMsg: Msg = { role: 'user', content }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const token = localStorage.getItem('auth_token')
      const res = await fetch(`${API_BASE}/chat/send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...(token && { Authorization: `Bearer ${token}` }) },
        body: JSON.stringify({ session_id: sid, content }),
      })
      const data = await res.json()
      if (data.success && data.data) {
        const aiMsg: Msg = { role: 'assistant', content: data.data.content, metadata: data.data.metadata }
        setMessages(prev => [...prev, aiMsg])
      } else {
        setMessages(prev => [...prev, { role: 'assistant', content: '抱歉，处理请求时出现错误，请重试。' }])
      }
    } catch {
      // 本地模拟回复
      setTimeout(() => {
        const mockResponse = generateMockResponse(content)
        setMessages(prev => [...prev, { role: 'assistant', content: mockResponse }])
        setLoading(false)
      }, 1500)
      return
    }
    setLoading(false)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      <Navbar />
      <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Header */}
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 shadow-lg shadow-blue-500/25">
            <Sparkles className="h-7 w-7 text-white" />
          </div>
          <h1 className="mt-3 text-2xl font-bold">AI 智能对话</h1>
          <p className="mt-1 text-sm text-muted-foreground">多智能体系统根据你的画像提供个性化学习服务</p>
        </motion.div>

        {/* Chat Area */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-6 rounded-2xl border border-border/40 bg-white/80 backdrop-blur-sm shadow-xl overflow-hidden"
        >
          <div className="h-[500px] overflow-y-auto p-6 space-y-4">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center">
                <motion.div
                  animate={{ y: [0, -8, 0] }}
                  transition={{ repeat: Infinity, duration: 3 }}
                  className="text-6xl mb-4"
                >
                  🤖
                </motion.div>
                <h3 className="text-lg font-medium">你好！我是 AI 学习助手</h3>
                <p className="mt-1 text-sm text-muted-foreground max-w-sm">
                  我可以帮你生成个性化学习资源、规划学习路径、答疑解惑，还可以评估你的学习效果。
                </p>
                {/* Quick Actions */}
                <div className="mt-6 grid grid-cols-2 gap-2 max-w-sm">
                  {quickActions.map((action, i) => (
                    <motion.button
                      key={i}
                      whileHover={{ scale: 1.03 }}
                      whileTap={{ scale: 0.97 }}
                      initial={{ opacity: 0, y: 12 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.3 + i * 0.1 }}
                      onClick={() => sendMessage(action.prompt)}
                      disabled={loading}
                      className="flex items-center gap-2 rounded-xl border border-border/40 bg-white px-3 py-2.5 text-xs font-medium text-muted-foreground hover:border-blue-300 hover:text-blue-600 transition-colors shadow-sm"
                    >
                      {action.icon}
                      {action.label}
                    </motion.button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((msg, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  {msg.role === 'assistant' && (
                    <div className="mr-3 mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-purple-500 text-white text-xs font-bold">
                      AI
                    </div>
                  )}
                  <div
                    className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                      msg.role === 'user'
                        ? 'bg-gradient-to-r from-blue-600 to-blue-500 text-white rounded-br-md'
                        : 'bg-muted rounded-bl-md prose prose-sm max-w-none'
                    }`}
                  >
                    {msg.role === 'assistant' ? (
                      <ReactMarkdown
                        components={{
                          code: ({ children, ...props }: any) => (
                            <code className="bg-slate-800 text-emerald-400 rounded px-1.5 py-0.5 text-xs" {...props}>
                              {children}
                            </code>
                          ),
                        }}
                      >
                        {msg.content}
                      </ReactMarkdown>
                    ) : (
                      msg.content
                    )}
                    {/* ── RAG Citations ── */}
                    {msg.role === 'assistant' &&
                     msg.metadata?.retrieval_used === true &&
                     Array.isArray(msg.metadata?.citations) &&
                     msg.metadata.citations.length > 0 && (
                      <div className="mt-2 border-t border-border/30 pt-2">
                        <button
                          onClick={() => toggleCitations(i)}
                          className="flex w-full items-center gap-1.5 text-xs text-muted-foreground hover:text-blue-600 transition-colors"
                        >
                          <span>{citationsLabel(msg.metadata.citations)}</span>
                          {expandedCitations.has(i)
                            ? <ChevronUp className="h-3 w-3" />
                            : <ChevronDown className="h-3 w-3" />
                          }
                        </button>
                        {expandedCitations.has(i) && (
                          <div className="mt-1.5 space-y-1.5">
                            {msg.metadata.citations.slice(0, 5).map((c, ci) => (
                              <div key={ci} className="rounded-lg bg-slate-50 px-2.5 py-1.5 text-xs text-muted-foreground leading-relaxed">
                                <span className="font-medium text-slate-700">
                                  第 {c.page_number} 页
                                </span>
                                {c.chapter ? (
                                  <span className="text-slate-500">
                                    {' · '}{(c.chapter.length > 30 ? c.chapter.slice(0, 30) + '…' : c.chapter)}
                                  </span>
                                ) : null}
                                {c.content_snippet ? (
                                  <p className="mt-0.5 text-slate-400 line-clamp-2">
                                    {(c.content_snippet.length > 120 ? c.content_snippet.slice(0, 120) + '…' : c.content_snippet)}
                                  </p>
                                ) : null}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                  {msg.role === 'user' && (
                    <div className="ml-3 mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-100 text-blue-600 text-xs font-bold">
                      U
                    </div>
                  )}
                </motion.div>
              ))
            )}
            {loading && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex items-center gap-3 pl-11">
                <div className="flex items-center gap-1">
                  <motion.span animate={{ opacity: [0.4, 1, 0.4] }} transition={{ repeat: Infinity, duration: 1.4 }} className="h-2 w-2 rounded-full bg-blue-400" />
                  <motion.span animate={{ opacity: [0.4, 1, 0.4] }} transition={{ repeat: Infinity, duration: 1.4, delay: 0.2 }} className="h-2 w-2 rounded-full bg-blue-400" />
                  <motion.span animate={{ opacity: [0.4, 1, 0.4] }} transition={{ repeat: Infinity, duration: 1.4, delay: 0.4 }} className="h-2 w-2 rounded-full bg-blue-400" />
                </div>
                <span className="text-xs text-muted-foreground">AI 思考中...</span>
              </motion.div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Input */}
          <div className="border-t border-border/40 p-4">
            {error && (
              <p className="mb-3 rounded-xl border border-red-200 bg-red-50 px-4 py-2.5 text-sm text-red-600">
                {error}
              </p>
            )}
            <div className="flex items-center gap-2">
              <input
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(input) }}}
                placeholder="输入你的问题或学习需求..."
                disabled={loading}
                className="flex-1 rounded-xl border border-border bg-background px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-blue-500/20 transition-shadow disabled:opacity-50"
              />
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => sendMessage(input)}
                disabled={!input.trim() || loading}
                className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg shadow-blue-500/25 disabled:opacity-40"
              >
                {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
              </motion.button>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  )
}

// 本地 mock 回复（后端不可用时的降级方案）
function generateMockResponse(input: string): string {
  const t = input.toLowerCase()
  if (t.includes('资源') || t.includes('生成')) {
    return `## 🎓 为你生成的学习资源\n\n多智能体系统已协同生成了以下资源：\n\n- 📖 **课程讲解文档**：核心概念与原理详解\n- 🧠 **思维导图**：知识结构全景图\n- 📝 **练习题**：8 道多类型题目\n- 📚 **拓展阅读**：3 个难度层级的推荐材料\n- 💻 **实操案例**：从入门到进阶的代码实践\n\n点击「资源中心」查看完整内容！`
  }
  if (t.includes('路径') || t.includes('规划')) {
    return `## 📍 学习路径\n\n根据你的画像，规划如下路径：\n\n**阶段 1**: 基础入门（4h）\n**阶段 2**: 技能构建（5h）\n**阶段 3**: 实践应用（4h）\n**阶段 4**: 能力提升（3h）\n**阶段 5**: 综合评估（2h）\n\n> 📊 总预计 18 小时，系统会根据进度动态调整`
  }
  if (t.includes('评估')) {
    return `## 📊 学习评估\n\n- 📚 知识掌握度: ████████░░ 80%\n- 🔧 技能熟练度: ███████░░░ 68%\n- 📈 学习进度: ██████░░░░ 62%\n- 🔥 参与度: ████████░░ 82%\n\n### 建议\n1. 加强综合应用题练习\n2. 增加项目实战投入\n3. 每周进行一次自测`
  }
  return `## 💡 智能辅导\n\n关于你的问题：「${input}」\n\n这是一个很好的问题！让我从以下角度为你解答：\n\n### 核心概念\n首先明确概念的定义和边界\n\n### 原理分析\n从底层理解运作机制\n\n### 实践建议\n理论结合实践是最佳路径\n\n需要我深入展开某个方面吗？`
}
