'use client'
import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Navbar } from '@/components/layout/Navbar'
import { BookOpen, Brain, PenLine, Library, Video, Code2, Presentation, Search, Sparkles, X, ChevronDown, Check } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { RESOURCE_TYPE_META, type ResourceType, type LearningResource } from '@/types'

const CATEGORIES = [
  { key: 'all' as const, label: '全部', icon: '📦' },
  ...(Object.entries(RESOURCE_TYPE_META) as [ResourceType, typeof RESOURCE_TYPE_META[keyof typeof RESOURCE_TYPE_META]][]).map(([key, meta]) => ({
    key, label: meta.name, icon: meta.icon,
  })),
]

// Mock resources
const mockResources: LearningResource[] = [
  { id: '1', type: 'document', title: '机器学习基础 — 核心概念与原理', content: { sections: [{ heading: '概述', body: '机器学习是人工智能的核心分支...' }, { heading: '监督学习', body: '从标注数据中学习映射关系...' }, { heading: '无监督学习', body: '从未标注数据中发现隐藏结构...' }] }, difficulty: 'beginner', tags: ['机器学习', '入门'] },
  { id: '2', type: 'mindmap', title: '算法设计与分析 — 思维导图', content: { root: { label: '算法设计', children: [{ label: '分治法' }, { label: '动态规划' }, { label: '贪心算法' }] }, mermaid: 'graph TD\n  A[算法] --> B[分治]\n  A --> C[DP]\n  A --> D[贪心]' }, difficulty: 'intermediate', tags: ['算法', '思维导图'] },
  { id: '3', type: 'quiz', title: '数据结构 — 练习题集', content: { total: 8, questions: [{ type: 'choice', question: '栈的特点是？', options: ['FIFO', 'LIFO', '随机', '优先'], answer: 'LIFO' }, { type: 'fill', question: '二叉树的遍历方式有___种', answer: '4' }] }, difficulty: 'intermediate', tags: ['数据结构', '练习'] },
  { id: '4', type: 'reading', title: '深度学习前沿 — 拓展阅读', content: { sections: [{ section_title: '必读基础', items: [{ title: 'Deep Learning Book', description: '经典教材' }] }, { section_title: '前沿研究', items: [{ title: 'Attention Is All You Need', description: 'Transformer论文' }] }] }, difficulty: 'advanced', tags: ['深度学习', '阅读'] },
  { id: '5', type: 'video', title: 'Python 编程入门 — 教学视频', content: { duration: '45分钟', scenes: [{ title: '环境搭建', duration: '5分钟' }, { title: '基础语法', duration: '15分钟' }, { title: '实战项目', duration: '25分钟' }] }, difficulty: 'beginner', tags: ['Python', '视频'] },
  { id: '6', type: 'code', title: '设计模式实战 — 代码案例', content: { cases: [{ title: '单例模式', code: 'class Singleton:\\n  _instance = None\\n  def __new__(cls):\\n    if not cls._instance:\\n      cls._instance = super().__new__(cls)\\n    return cls._instance' }, { title: '工厂模式', code: 'class Factory:\\n  def create(self, type):\\n    if type == "A": return ProductA()\\n    return ProductB()' }] }, difficulty: 'intermediate', tags: ['设计模式', '代码'] },
  { id: '7', type: 'slides', title: '软件工程概论 — 教学PPT', content: { total: 10, slides: [{ slide: 1, title: '软件工程概述' }, { slide: 2, title: '开发模型' }, { slide: 3, title: '需求分析' }] }, difficulty: 'beginner', tags: ['软件工程', 'PPT'] },
]

export default function LearningPage() {
  const [activeCat, setActiveCat] = useState<string>('all')
  const [search, setSearch] = useState('')
  const [selected, setSelected] = useState<LearningResource | null>(null)
  const [generating, setGenerating] = useState(false)
  const [topic, setTopic] = useState('')

  const filtered = mockResources.filter(r => {
    if (activeCat !== 'all' && r.type !== activeCat) return false
    if (search && !r.title.includes(search) && !r.tags.some(t => t.includes(search))) return false
    return true
  })

  const handleGenerate = () => {
    if (!topic.trim()) return
    setGenerating(true)
    setTimeout(() => {
      setGenerating(false)
      setTopic('')
    }, 2500)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      <Navbar />
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Header */}
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-2xl font-bold">📚 资源中心</h1>
            <p className="mt-1 text-sm text-muted-foreground">多智能体协同生成的个性化学习资源</p>
          </div>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => document.getElementById('generate-section')?.scrollIntoView({ behavior: 'smooth' })}
            className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 px-5 py-2.5 text-sm font-medium text-white shadow-lg shadow-blue-500/25"
          >
            <Sparkles className="h-4 w-4" />
            生成新资源
          </motion.button>
        </motion.div>

        {/* Search + Filter */}
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="mt-6 flex items-center gap-4 flex-wrap">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="搜索资源..."
              className="w-full rounded-xl border border-border bg-white pl-10 pr-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500/20"
            />
          </div>
          <div className="flex items-center gap-1 flex-wrap">
            {CATEGORIES.map((cat) => (
              <motion.button
                key={cat.key}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setActiveCat(cat.key)}
                className={`flex items-center gap-1.5 rounded-lg px-3 py-2 text-xs font-medium transition-colors ${
                  activeCat === cat.key ? 'bg-blue-600 text-white shadow-md' : 'bg-white text-muted-foreground hover:text-foreground border border-border/40'
                }`}
              >
                {cat.icon} {cat.label}
              </motion.button>
            ))}
          </div>
        </motion.div>

        {/* Resource Grid */}
        <motion.div layout className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <AnimatePresence mode="popLayout">
            {filtered.map((resource) => {
              const meta = RESOURCE_TYPE_META[resource.type]
              return (
                <motion.div
                  key={resource.id}
                  layout
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  whileHover={{ y: -4, boxShadow: '0 12px 40px rgba(0,0,0,0.1)' }}
                  onClick={() => setSelected(resource)}
                  className="group cursor-pointer rounded-2xl border border-border/40 bg-white p-5 shadow-sm transition-shadow"
                >
                  <div className="flex items-start justify-between">
                    <div
                      className="flex h-10 w-10 items-center justify-center rounded-xl text-lg"
                      style={{ backgroundColor: meta.color + '20' }}
                    >
                      {meta.icon}
                    </div>
                    <span
                      className="rounded-full px-2 py-0.5 text-[10px] font-medium"
                      style={{ color: meta.color, backgroundColor: meta.color + '15' }}
                    >
                      {resource.difficulty}
                    </span>
                  </div>
                  <h3 className="mt-3 font-semibold text-sm group-hover:text-blue-600 transition-colors leading-snug">
                    {resource.title}
                  </h3>
                  <p className="mt-1 text-xs text-muted-foreground">{meta.name}</p>
                  <div className="mt-3 flex items-center gap-1">
                    {resource.tags.map(tag => (
                      <span key={tag} className="rounded-md bg-muted px-2 py-0.5 text-[10px] text-muted-foreground">{tag}</span>
                    ))}
                  </div>
                </motion.div>
              )
            })}
          </AnimatePresence>
        </motion.div>

        {filtered.length === 0 && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-12 text-center">
            <p className="text-muted-foreground">没有找到匹配的资源</p>
          </motion.div>
        )}

        {/* Generate Section */}
        <motion.div id="generate-section" initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} className="mt-12 rounded-2xl border border-border/40 bg-gradient-to-br from-blue-50 to-purple-50 p-8 text-center">
          <Sparkles className="mx-auto h-10 w-10 text-blue-500" />
          <h2 className="mt-3 text-xl font-bold">AI 多智能体资源生成</h2>
          <p className="mt-1 text-sm text-muted-foreground">输入学习主题，多智能体自动协同生成 7 种个性化学习资源</p>
          <div className="mt-6 flex items-center justify-center gap-2 max-w-md mx-auto">
            <input
              value={topic}
              onChange={e => setTopic(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleGenerate()}
              placeholder="例如：动态规划、神经网络、操作系统..."
              disabled={generating}
              className="flex-1 rounded-xl border border-border bg-white px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-blue-500/20 disabled:opacity-50"
            />
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleGenerate}
              disabled={!topic.trim() || generating}
              className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 px-5 py-3 text-sm font-medium text-white shadow-lg disabled:opacity-40"
            >
              {generating ? (
                <>
                  <motion.span animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1.5, ease: 'linear' }}>
                    <Sparkles className="h-4 w-4" />
                  </motion.span>
                  生成中...
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  生成资源
                </>
              )}
            </motion.button>
          </div>
          <p className="mt-3 text-xs text-muted-foreground">
            支持生成：文档、思维导图、练习题、拓展阅读、视频脚本、实操案例、PPT
          </p>
        </motion.div>

        {/* Resource Detail Modal */}
        <AnimatePresence>
          {selected && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
              onClick={() => setSelected(null)}
            >
              <motion.div
                initial={{ scale: 0.9, opacity: 0, y: 20 }}
                animate={{ scale: 1, opacity: 1, y: 0 }}
                exit={{ scale: 0.9, opacity: 0, y: 20 }}
                onClick={e => e.stopPropagation()}
                className="relative w-full max-w-2xl max-h-[80vh] overflow-y-auto rounded-2xl bg-white shadow-2xl"
              >
                {/* Close */}
                <button
                  onClick={() => setSelected(null)}
                  className="absolute top-4 right-4 z-10 p-1.5 rounded-lg hover:bg-muted transition-colors"
                >
                  <X className="h-5 w-5" />
                </button>

                {/* Header */}
                <div className="p-6 border-b border-border">
                  <div className="flex items-center gap-3">
                    <div
                      className="flex h-10 w-10 items-center justify-center rounded-xl text-lg"
                      style={{ backgroundColor: RESOURCE_TYPE_META[selected.type].color + '20' }}
                    >
                      {RESOURCE_TYPE_META[selected.type].icon}
                    </div>
                    <div>
                      <h2 className="font-semibold">{selected.title}</h2>
                      <p className="text-xs text-muted-foreground">
                        {RESOURCE_TYPE_META[selected.type].name} · {selected.difficulty}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Content */}
                <div className="p-6">
                  <ResourceContent resource={selected} />
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}

// Resource content renderer by type
function ResourceContent({ resource }: { resource: LearningResource }) {
  const c = resource.content

  switch (resource.type) {
    case 'document':
      return (
        <div className="space-y-4">
          {c.sections?.map((s: any, i: number) => (
            <motion.div key={i} initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.08 }}>
              <h3 className="font-semibold text-sm mb-2">{s.heading}</h3>
              <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-wrap">{s.body || s.content}</p>
              {s.key_points && (
                <ul className="mt-2 space-y-1">
                  {s.key_points.map((kp: string, j: number) => (
                    <li key={j} className="flex items-start gap-2 text-sm text-muted-foreground">
                      <Check className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" /> {kp}
                    </li>
                  ))}
                </ul>
              )}
            </motion.div>
          ))}
        </div>
      )

    case 'mindmap':
      return (
        <div>
          {c.mermaid ? (
            <pre className="rounded-xl bg-slate-900 p-4 text-xs text-emerald-400 overflow-x-auto whitespace-pre">{c.mermaid}</pre>
          ) : (
            <MindmapRenderer node={c.root} depth={0} />
          )}
        </div>
      )

    case 'quiz':
      return (
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span>共 {c.total} 题</span>
            <span>·</span>
            <span>时间限制: {c.time_limit || '20分钟'}</span>
          </div>
          {c.questions?.map((q: any, i: number) => (
            <motion.div key={i} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.06 }}
              className="rounded-xl border border-border/40 p-4"
            >
              <p className="text-sm font-medium">{i + 1}. {q.question}</p>
              {q.options && (
                <div className="mt-2 grid gap-1">
                  {q.options.map((opt: string, j: number) => (
                    <label key={j} className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground cursor-pointer py-1">
                      <input type="radio" name={`q-${i}`} className="text-blue-600" />
                      {opt}
                    </label>
                  ))}
                </div>
              )}
              {q.type === 'fill' && (
                <input className="mt-2 w-full rounded-lg border border-border px-3 py-2 text-sm" placeholder="输入你的答案..." />
              )}
              <details className="mt-2">
                <summary className="text-xs text-blue-600 cursor-pointer hover:underline">查看答案</summary>
                <p className="mt-1 text-xs text-emerald-600">{q.answer}</p>
                {q.explanation && <p className="mt-1 text-xs text-muted-foreground">{q.explanation}</p>}
              </details>
            </motion.div>
          ))}
        </div>
      )

    case 'reading':
      return (
        <div className="space-y-4">
          {c.sections?.map((s: any, i: number) => (
            <motion.div key={i} initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.08 }}>
              <h3 className="font-semibold text-sm flex items-center gap-2">
                {s.section_title}
                <span className={`text-xs px-2 py-0.5 rounded-full ${
                  s.priority === 'high' ? 'bg-red-100 text-red-600' : s.priority === 'medium' ? 'bg-amber-100 text-amber-600' : 'bg-slate-100 text-slate-500'
                }`}>
                  {s.priority === 'high' ? '必读' : s.priority === 'medium' ? '推荐' : '选读'}
                </span>
              </h3>
              {s.items?.map((item: any, j: number) => (
                <div key={j} className="mt-2 rounded-lg border border-border/40 p-3 bg-muted/30">
                  <p className="font-medium text-sm">{item.title}</p>
                  <p className="text-xs text-muted-foreground">{item.type} · {item.description}</p>
                </div>
              ))}
            </motion.div>
          ))}
        </div>
      )

    case 'video':
      return (
        <div>
          <p className="text-sm text-muted-foreground mb-4">⏱️ 总时长: {c.duration}</p>
          {c.scenes?.map((s: any, i: number) => (
            <motion.div key={i} initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.08 }}
              className="flex items-center gap-4 py-3 border-b border-border/40 last:border-0"
            >
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100 text-blue-600 text-xs font-bold">
                {s.id || i + 1}
              </div>
              <div>
                <p className="font-medium text-sm">{s.title}</p>
                <p className="text-xs text-muted-foreground">{s.duration} · {s.narration?.slice(0, 60)}...</p>
              </div>
            </motion.div>
          ))}
        </div>
      )

    case 'code':
      return (
        <div className="space-y-6">
          {c.cases?.map((cs: any, i: number) => (
            <motion.div key={i} initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.1 }}>
              <h3 className="font-semibold text-sm mb-2">{cs.title}</h3>
              <p className="text-xs text-muted-foreground mb-3">{cs.description}</p>
              {cs.objectives && (
                <ul className="mb-3 space-y-1">
                  {cs.objectives.map((o: string, j: number) => (
                    <li key={j} className="flex items-start gap-2 text-xs text-muted-foreground">
                      <Check className="h-3 w-3 text-emerald-500 shrink-0 mt-0.5" /> {o}
                    </li>
                  ))}
                </ul>
              )}
              <pre className="rounded-xl bg-slate-900 p-4 text-xs text-emerald-400 overflow-x-auto whitespace-pre">{cs.code}</pre>
              {cs.exercises && (
                <div className="mt-3">
                  <p className="text-xs font-medium mb-1">练习任务：</p>
                  {cs.exercises.map((e: string, j: number) => (
                    <p key={j} className="text-xs text-muted-foreground">· {e}</p>
                  ))}
                </div>
              )}
            </motion.div>
          ))}
        </div>
      )

    case 'slides':
      return (
        <div>
          <p className="text-sm text-muted-foreground mb-4">📊 共 {c.total} 页</p>
          <div className="grid gap-2 sm:grid-cols-2">
            {c.slides?.map((s: any, i: number) => (
              <motion.div key={i} initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: i * 0.04 }}
                className="rounded-lg border border-border/40 p-3 hover:border-blue-300 transition-colors cursor-pointer"
              >
                <p className="text-xs text-muted-foreground">第 {s.slide} 页</p>
                <p className="font-medium text-sm">{s.title}</p>
                {s.subtitle && <p className="text-xs text-muted-foreground">{s.subtitle}</p>}
              </motion.div>
            ))}
          </div>
        </div>
      )

    default:
      return <pre className="text-xs overflow-auto">{JSON.stringify(c, null, 2)}</pre>
  }
}

// Mindmap recursive renderer
function MindmapRenderer({ node, depth }: { node: any; depth: number }) {
  const colors = ['border-l-blue-400 bg-blue-50', 'border-l-purple-400 bg-purple-50', 'border-l-emerald-400 bg-emerald-50', 'border-l-amber-400 bg-amber-50']
  const color = colors[depth % colors.length]
  return (
    <div className={`ml-${depth * 4} rounded-lg border-l-4 ${color} p-3 mb-2`}>
      <p className="font-medium text-sm">{node.icon} {node.label}</p>
      {node.children && (
        <div className="mt-2 ml-4">
          {node.children.map((child: any, i: number) => (
            <MindmapRenderer key={i} node={child} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  )
}
