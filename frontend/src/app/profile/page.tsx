'use client'
import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Navbar } from '@/components/layout/Navbar'
import { Send, Sparkles, CheckCircle2, Brain } from 'lucide-react'

// 渐进式问题
const QUESTIONS = [
  { id: 'knowledge_basis', label: '知识基础', question: '你好！让我们开始构建你的学习画像 🎓\n\n首先，你的专业是什么？之前学过哪些课程？对哪些领域比较熟悉？' },
  { id: 'learning_goals', label: '学习目标', question: '你的学习目标是什么？准备考试、找工作、做项目，还是纯粹兴趣？' },
  { id: 'cognitive_style', label: '认知风格', question: '你喜欢怎么学习？看视频讲解、读文档、动手实践，还是听音频？' },
  { id: 'weak_points', label: '薄弱环节', question: '在学习中，你觉得哪些知识点或技能最薄弱、容易出错？' },
  { id: 'engagement', label: '参与度', question: '你对当前学习内容有多大兴趣？是主动想学还是被课程要求？' },
  { id: 'time', label: '可用时间', question: '你每周大概有多少时间可以用来学习？每天能学多久？' },
  { id: 'pace', label: '学习节奏', question: '你希望学习节奏快一点还是稳扎稳打？' },
  { id: 'modalities', label: '偏好形式', question: '你偏好哪种学习资源形式？文档、视频、思维导图、练习题还是动手项目？' },
]

const DIMENSION_ICONS: Record<string, string> = {
  '知识基础': '📚', '学习目标': '🎯', '认知风格': '🧠', '薄弱环节': '⚠️',
  '参与度': '🔥', '可用时间': '⏰', '学习节奏': '🏃', '偏好形式': '🎨', '学科兴趣': '💡',
}

export default function ProfilePage() {
  const [messages, setMessages] = useState<{ role: 'assistant' | 'user'; content: string }[]>([])
  const [input, setInput] = useState('')
  const [qIndex, setQIndex] = useState(0)
  const [dimensions, setDimensions] = useState<{ name: string; label: string; value: number }[]>([])
  const [isDone, setIsDone] = useState(false)
  const chatEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // 启动第一问
    if (messages.length === 0) {
      setMessages([{ role: 'assistant', content: QUESTIONS[0].question }])
    }
  }, [])

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = () => {
    if (!input.trim() || isDone) return
    const userMsg = input.trim()
    setMessages(prev => [...prev, { role: 'user', content: userMsg }])
    setInput('')

    // 提取当前维度
    const currentQ = QUESTIONS[qIndex]
    extractDimension(userMsg, currentQ)

    // 下一个问题
    const next = qIndex + 1
    if (next < QUESTIONS.length) {
      setTimeout(() => {
        setMessages(prev => [...prev, { role: 'assistant', content: QUESTIONS[next].question }])
        setQIndex(next)
      }, 600)
    } else {
      setTimeout(() => {
        setIsDone(true)
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `🎉 太好了！你的学习画像已构建完成！\n\n我为你识别了 ${dimensions.length + 1} 个维度。点击下方卡片查看详情。`,
        }])
      }, 600)
    }
  }

  const extractDimension = (text: string, q: typeof QUESTIONS[0]) => {
    const t = text.toLowerCase()
    // 简单关键词提取
    if (q.id === 'knowledge_basis') {
      const v = t.includes('精通') || t.includes('熟练') ? 85 : t.includes('基础') ? 35 : 55
      addDim('知识基础', v)
    } else if (q.id === 'learning_goals') {
      const v = t.includes('项目') || t.includes('找工作') ? 80 : 60
      addDim('学习目标', v)
    } else if (q.id === 'cognitive_style') {
      const v = 70
      addDim('认知风格', v)
    } else if (q.id === 'weak_points') {
      addDim('薄弱环节', 40)
    } else if (q.id === 'engagement') {
      const v = t.includes('喜欢') || t.includes('感兴趣') ? 85 : 50
      addDim('参与度', v)
    } else if (q.id === 'time') {
      addDim('可用时间', 60)
    } else if (q.id === 'pace') {
      const v = t.includes('快') ? 75 : 45
      addDim('学习节奏', v)
    } else if (q.id === 'modalities') {
      addDim('偏好形式', 70)
    }
  }

  const addDim = (label: string, value: number) => {
    setDimensions(prev => {
      const exist = prev.find(d => d.label === label)
      if (exist) {
        return prev.map(d => d.label === label ? { ...d, value } : d)
      }
      return [...prev, { name: label, label, value }]
    })
  }

  const container = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.06 } },
  }

  const itemAnim = {
    hidden: { opacity: 0, x: -16 },
    show: { opacity: 1, x: 0 },
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      <Navbar />
      <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Header */}
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="text-center">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 shadow-lg shadow-blue-500/25">
            <Brain className="h-8 w-8 text-white" />
          </div>
          <h1 className="mt-4 text-2xl font-bold">对话式画像构建</h1>
          <p className="mt-1 text-muted-foreground">
            通过自然对话，AI 自动分析你的学习特征（{dimensions.length}/8 个维度）
          </p>
          {/* Progress */}
          {!isDone && (
            <div className="mt-4 mx-auto max-w-xs h-1.5 rounded-full bg-muted overflow-hidden">
              <motion.div
                className="h-full rounded-full bg-gradient-to-r from-blue-500 to-purple-600"
                initial={{ width: 0 }}
                animate={{ width: `${(dimensions.length / 8) * 100}%` }}
                transition={{ type: 'spring', stiffness: 100 }}
              />
            </div>
          )}
        </motion.div>

        {/* Chat Area */}
        <motion.div
          variants={container} initial="hidden" animate="show"
          className="mt-8 rounded-2xl border border-border/40 bg-white/80 backdrop-blur-sm shadow-xl overflow-hidden"
        >
          <div className="h-[420px] overflow-y-auto p-6 space-y-4">
            {messages.map((msg, i) => (
              <motion.div
                key={i}
                variants={itemAnim}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {msg.role === 'assistant' && (
                  <div className="mr-3 mt-1 flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-purple-500 text-white text-sm font-bold">
                    A
                  </div>
                )}
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
                    msg.role === 'user'
                      ? 'bg-gradient-to-r from-blue-600 to-blue-500 text-white rounded-br-md'
                      : 'bg-muted rounded-bl-md'
                  }`}
                >
                  {msg.content}
                </div>
                {msg.role === 'user' && (
                  <div className="ml-3 mt-1 flex h-8 w-8 items-center justify-center rounded-full bg-blue-100 text-blue-600 text-sm font-bold">
                    U
                  </div>
                )}
              </motion.div>
            ))}
            <div ref={chatEndRef} />
          </div>

          {/* Input */}
          {!isDone && (
            <div className="border-t border-border/40 p-4">
              <div className="flex items-center gap-2">
                <input
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleSend()}
                  placeholder="输入你的回答..."
                  className="flex-1 rounded-xl border border-border bg-background px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-blue-500/20 transition-shadow"
                />
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={handleSend}
                  disabled={!input.trim()}
                  className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg disabled:opacity-40"
                >
                  <Send className="h-4 w-4" />
                </motion.button>
              </div>
              <p className="mt-2 text-xs text-muted-foreground text-center">
                按 Enter 发送 · 告诉 AI 你的真实情况，画像更精准
              </p>
            </div>
          )}
        </motion.div>

        {/* Dimension Cards — shown after completion */}
        <AnimatePresence>
          {isDone && (
            <motion.div
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="mt-8"
            >
              <div className="flex items-center gap-2 mb-4">
                <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                <h2 className="text-lg font-semibold">你的学习画像</h2>
              </div>
              <motion.div variants={container} initial="hidden" animate="show" className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                {dimensions.map((dim, i) => (
                  <motion.div
                    key={i}
                    variants={itemAnim}
                    whileHover={{ y: -4 }}
                    className="rounded-xl border border-border/40 bg-white p-4 shadow-sm"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-2xl">{DIMENSION_ICONS[dim.label] || '📌'}</span>
                      <span className="text-xs font-medium text-muted-foreground">{dim.value}%</span>
                    </div>
                    <p className="mt-2 font-semibold text-sm">{dim.label}</p>
                    <div className="mt-2 h-1.5 rounded-full bg-muted overflow-hidden">
                      <motion.div
                        className="h-full rounded-full bg-gradient-to-r from-blue-500 to-purple-500"
                        initial={{ width: 0 }}
                        animate={{ width: `${dim.value}%` }}
                        transition={{ delay: 0.3 + i * 0.1, duration: 0.6 }}
                      />
                    </div>
                  </motion.div>
                ))}
              </motion.div>
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.8 }} className="mt-6 text-center">
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 px-6 py-3 text-sm font-medium text-white shadow-lg shadow-blue-500/25"
                  onClick={() => window.location.href = '/chat'}
                >
                  <Sparkles className="h-4 w-4" />
                  开始个性化学习
                </motion.button>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}
