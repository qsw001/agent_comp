'use client'
import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Navbar } from '@/components/layout/Navbar'
import { BarChart3, TrendingUp, Target, Zap, ChevronRight, RefreshCw } from 'lucide-react'

const assessmentData = {
  knowledge_mastery: 78,
  skill_proficiency: 65,
  learning_progress: 62,
  engagement: 82,
  strengths: ['基础知识扎实', '理解速度较快', '图文结合学习效果好'],
  weaknesses: ['综合应用能力待提升', '代码实操经验不足', '复杂问题拆解需加强'],
  recommendations: [
    '增加项目实战任务，每周至少完成 1 个综合案例',
    '针对性练习薄弱环节的专项题目',
    '参加学习讨论，通过分享加深理解',
    '定期进行自测，追踪知识掌握变化',
  ],
}

export default function EvaluationPage() {
  const [animated, setAnimated] = useState(false)
  useEffect(() => { setAnimated(true) }, [])

  const metrics = [
    { name: '知识掌握度', value: assessmentData.knowledge_mastery, icon: Target, color: 'from-blue-500 to-blue-600', textColor: 'text-blue-600' },
    { name: '技能熟练度', value: assessmentData.skill_proficiency, icon: Zap, color: 'from-purple-500 to-purple-600', textColor: 'text-purple-600' },
    { name: '学习进度', value: assessmentData.learning_progress, icon: TrendingUp, color: 'from-emerald-500 to-emerald-600', textColor: 'text-emerald-600' },
    { name: '参与度', value: assessmentData.engagement, icon: BarChart3, color: 'from-amber-500 to-amber-600', textColor: 'text-amber-600' },
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      <Navbar />
      <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Header */}
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 shadow-lg shadow-blue-500/25">
            <BarChart3 className="h-7 w-7 text-white" />
          </div>
          <h1 className="mt-3 text-2xl font-bold">学习效果评估</h1>
          <p className="mt-1 text-sm text-muted-foreground">多维度精准评估，动态调整学习策略</p>
        </motion.div>

        {/* Metric Cards */}
        <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {metrics.map((metric, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 + i * 0.1 }}
              whileHover={{ y: -4 }}
              className="rounded-2xl border border-border/40 bg-white p-5 shadow-sm text-center"
            >
              <div className={`mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br ${metric.color} bg-opacity-10`}>
                <metric.icon className={`h-6 w-6 ${metric.textColor}`} />
              </div>
              <p className="mt-3 text-3xl font-bold">{animated ? metric.value : 0}%</p>
              <p className="text-sm text-muted-foreground">{metric.name}</p>
              <div className="mt-2 h-1.5 rounded-full bg-muted overflow-hidden">
                <motion.div
                  className={`h-full rounded-full bg-gradient-to-r ${metric.color}`}
                  initial={{ width: 0 }}
                  animate={{ width: animated ? `${metric.value}%` : '0%' }}
                  transition={{ duration: 1, delay: 0.5 + i * 0.15, ease: 'easeOut' }}
                />
              </div>
            </motion.div>
          ))}
        </div>

        {/* Strengths & Weaknesses */}
        <div className="mt-8 grid gap-6 lg:grid-cols-2">
          {/* Strengths */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.5 }}
            className="rounded-2xl border border-border/40 bg-white p-6 shadow-sm"
          >
            <h3 className="font-semibold flex items-center gap-2">
              <span className="text-emerald-500">✅</span> 优势方面
            </h3>
            <ul className="mt-3 space-y-2">
              {assessmentData.strengths.map((s, i) => (
                <motion.li key={i} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.6 + i * 0.08 }}
                  className="flex items-center gap-3 rounded-lg bg-emerald-50 px-3 py-2 text-sm"
                >
                  <div className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                  {s}
                </motion.li>
              ))}
            </ul>
          </motion.div>

          {/* Weaknesses */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.5 }}
            className="rounded-2xl border border-border/40 bg-white p-6 shadow-sm"
          >
            <h3 className="font-semibold flex items-center gap-2">
              <span className="text-amber-500">⚠️</span> 需要加强
            </h3>
            <ul className="mt-3 space-y-2">
              {assessmentData.weaknesses.map((w, i) => (
                <motion.li key={i} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.6 + i * 0.08 }}
                  className="flex items-center gap-3 rounded-lg bg-amber-50 px-3 py-2 text-sm"
                >
                  <div className="h-1.5 w-1.5 rounded-full bg-amber-500" />
                  {w}
                </motion.li>
              ))}
            </ul>
          </motion.div>
        </div>

        {/* Recommendations */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
          className="mt-6 rounded-2xl border border-border/40 bg-white p-6 shadow-sm"
        >
          <div className="flex items-center justify-between">
            <h3 className="font-semibold flex items-center gap-2">
              <span className="text-blue-500">💡</span> AI 学习建议
            </h3>
            <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
              className="flex items-center gap-1.5 text-xs text-blue-600 hover:underline"
            >
              <RefreshCw className="h-3 w-3" /> 刷新评估
            </motion.button>
          </div>
          <div className="mt-3 space-y-2">
            {assessmentData.recommendations.map((r, i) => (
              <motion.div key={i} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.75 + i * 0.08 }}
                className="flex items-start gap-3 rounded-lg bg-blue-50 px-4 py-3"
              >
                <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-blue-500 text-white text-[10px] font-bold mt-0.5">
                  {i + 1}
                </div>
                <p className="text-sm">{r}</p>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Historical progress */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.9 }}
          className="mt-6 rounded-2xl border border-border/40 bg-white p-6 shadow-sm"
        >
          <h3 className="font-semibold">📈 学习趋势</h3>
          <div className="mt-4 h-40 flex items-end justify-between gap-2 px-4">
            {[45, 50, 55, 60, 58, 65, 62].map((val, i) => (
              <div key={i} className="flex-1 flex flex-col items-center gap-1">
                <span className="text-xs font-medium text-muted-foreground">{val}%</span>
                <motion.div
                  initial={{ height: 0 }}
                  animate={{ height: `${val * 1.2}px` }}
                  transition={{ delay: 1 + i * 0.08, duration: 0.5 }}
                  className="w-full rounded-t-lg bg-gradient-to-t from-blue-500 to-purple-500 max-w-[30px]"
                />
                <span className="text-[10px] text-muted-foreground">W{i + 1}</span>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  )
}
