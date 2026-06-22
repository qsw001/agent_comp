'use client'
import { useState } from 'react'
import { motion } from 'framer-motion'
import { Navbar } from '@/components/layout/Navbar'
import { Map, CheckCircle2, Circle, Clock, ArrowRight, Sparkles, ChevronDown } from 'lucide-react'

interface PathNode {
  id: number
  title: string
  description: string
  hours: number
  resources: string[]
  completed: boolean
  color: string
}

export default function PathPage() {
  const [nodes, setNodes] = useState<PathNode[]>([
    { id: 1, title: '基础入门', description: '核心概念与基础知识', hours: 4, resources: ['📖 课程文档', '🧠 思维导图'], completed: true, color: 'from-blue-500 to-blue-600' },
    { id: 2, title: '技能构建', description: '关键技术深度掌握', hours: 5, resources: ['📝 练习题', '💻 实操案例'], completed: true, color: 'from-purple-500 to-purple-600' },
    { id: 3, title: '实践应用', description: '项目实战与综合运用', hours: 4, resources: ['🎬 视频教程', '💻 进阶案例', '📚 拓展阅读'], completed: false, color: 'from-amber-500 to-amber-600' },
    { id: 4, title: '能力提升', description: '进阶话题与优化技巧', hours: 3, resources: ['📊 PPT课件', '📚 论文阅读', '💻 高级案例'], completed: false, color: 'from-emerald-500 to-emerald-600' },
    { id: 5, title: '综合评估', description: '复习巩固与能力验证', hours: 2, resources: ['📝 综合测试题', '📖 总结文档'], completed: false, color: 'from-rose-500 to-rose-600' },
  ])

  const toggleNode = (id: number) => {
    setNodes(prev => prev.map(n => n.id === id ? { ...n, completed: !n.completed } : n))
  }

  const completedCount = nodes.filter(n => n.completed).length
  const totalHours = nodes.reduce((s, n) => s + n.hours, 0)
  const progress = nodes.length > 0 ? completedCount / nodes.length : 0

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      <Navbar />
      <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Header */}
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 shadow-lg shadow-blue-500/25">
            <Map className="h-7 w-7 text-white" />
          </div>
          <h1 className="mt-3 text-2xl font-bold">个性化学习路径</h1>
          <p className="mt-1 text-sm text-muted-foreground">基于你的画像动态规划的最优学习路线</p>
        </motion.div>

        {/* Progress Overview */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-6 rounded-2xl border border-border/40 bg-white/80 backdrop-blur-sm p-6 shadow-xl"
        >
          <div className="grid gap-4 sm:grid-cols-3">
            <div className="text-center">
              <p className="text-3xl font-bold text-blue-600">{completedCount}/{nodes.length}</p>
              <p className="text-xs text-muted-foreground">已完成阶段</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-purple-600">{totalHours}h</p>
              <p className="text-xs text-muted-foreground">总预计学时</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-emerald-600">{Math.round(progress * 100)}%</p>
              <p className="text-xs text-muted-foreground">总体进度</p>
            </div>
          </div>
          <div className="mt-4 h-2.5 rounded-full bg-muted overflow-hidden">
            <motion.div
              className="h-full rounded-full bg-gradient-to-r from-blue-500 to-purple-600"
              initial={{ width: 0 }}
              animate={{ width: `${progress * 100}%` }}
              transition={{ duration: 0.8, ease: 'easeOut' }}
            />
          </div>
        </motion.div>

        {/* Path Timeline */}
        <div className="mt-8 relative">
          {/* Vertical line */}
          <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-gradient-to-b from-blue-200 via-purple-200 to-emerald-200 hidden sm:block" />

          <div className="space-y-0">
            {nodes.map((node, i) => (
              <motion.div
                key={node.id}
                initial={{ opacity: 0, x: -30 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2 + i * 0.12 }}
                className="relative pl-16 sm:pl-20 pb-8 last:pb-0"
              >
                {/* Node indicator */}
                <div className="absolute left-0 sm:left-4 top-0 z-10">
                  <motion.button
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    onClick={() => toggleNode(node.id)}
                    className={`flex h-12 w-12 items-center justify-center rounded-2xl shadow-lg transition-colors ${
                      node.completed
                        ? `bg-gradient-to-br ${node.color} text-white`
                        : 'bg-white border-2 border-dashed border-muted-foreground/30 text-muted-foreground'
                    }`}
                  >
                    {node.completed ? <CheckCircle2 className="h-5 w-5" /> : <Circle className="h-5 w-5" />}
                  </motion.button>
                </div>

                {/* Node card */}
                <motion.div
                  whileHover={{ x: 4 }}
                  className={`rounded-2xl border border-border/40 p-5 shadow-sm transition-colors ${
                    node.completed ? 'bg-white' : 'bg-white/60'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono text-muted-foreground">阶段 {node.id}</span>
                        {node.completed && (
                          <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-medium text-emerald-600">
                            已完成
                          </span>
                        )}
                      </div>
                      <h3 className="mt-1 font-semibold">{node.title}</h3>
                      <p className="text-sm text-muted-foreground">{node.description}</p>
                    </div>
                    <div className="flex items-center gap-1 text-xs text-muted-foreground">
                      <Clock className="h-3 w-3" />
                      {node.hours}h
                    </div>
                  </div>
                  {!node.completed && (
                    <div className="mt-3 flex flex-wrap gap-1">
                      {node.resources.map((r, j) => (
                        <span key={j} className="rounded-lg bg-muted px-2.5 py-1 text-xs text-muted-foreground">{r}</span>
                      ))}
                    </div>
                  )}
                </motion.div>

                {/* Connector arrow */}
                {i < nodes.length - 1 && (
                  <div className="absolute left-9 sm:left-9 bottom-2">
                    <motion.div animate={{ y: [0, 4, 0] }} transition={{ repeat: Infinity, duration: 2 }}>
                      <ArrowRight className="h-4 w-4 text-muted-foreground/40 rotate-90" />
                    </motion.div>
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        </div>

        {/* CTA */}
        <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} className="mt-10 text-center">
          <div className="inline-flex items-center gap-4 rounded-2xl border border-border/40 bg-white p-4 shadow-sm">
            <p className="text-sm text-muted-foreground">
              <Sparkles className="inline h-4 w-4 text-blue-500" /> 路径会根据你的学习进度和评估结果动态调整
            </p>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="rounded-lg bg-gradient-to-r from-blue-600 to-purple-600 px-4 py-1.5 text-xs font-medium text-white"
            >
              刷新路径
            </motion.button>
          </div>
        </motion.div>
      </div>
    </div>
  )
}
