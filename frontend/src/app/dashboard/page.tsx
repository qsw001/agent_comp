'use client'
import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Navbar } from '@/components/layout/Navbar'
import { TrendingUp, Clock, Award, BookOpen, ChevronRight, Sparkles } from 'lucide-react'
import Link from 'next/link'

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.08, delayChildren: 0.1 },
  },
}

const item = {
  hidden: { opacity: 0, y: 24 },
  show: { opacity: 1, y: 0, transition: { type: 'spring' as const, stiffness: 300, damping: 24 } },
}

export default function DashboardPage() {
  const [greeting, setGreeting] = useState('')

  useEffect(() => {
    const h = new Date().getHours()
    if (h < 12) setGreeting('早上好')
    else if (h < 18) setGreeting('下午好')
    else setGreeting('晚上好')
  }, [])

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      <Navbar />
      <motion.main variants={container} initial="hidden" animate="show" className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">

        {/* Header */}
        <motion.div variants={item} className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">
              {greeting}，<span className="gradient-text">同学</span> 👋
            </h1>
            <p className="mt-1 text-muted-foreground">AI 多智能体系统为你打造个性化学习体验</p>
          </div>
          <Link href="/chat">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 px-5 py-2.5 text-sm font-medium text-white shadow-lg shadow-blue-500/25"
            >
              <Sparkles className="h-4 w-4" />
              开始对话
            </motion.button>
          </Link>
        </motion.div>

        {/* Stats */}
        <motion.div variants={item} className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { label: '学习时长', value: '42h', change: '+12%', icon: Clock, color: 'from-blue-500 to-blue-600' },
            { label: '已完成资源', value: '24', change: '共 52 个', icon: BookOpen, color: 'from-purple-500 to-purple-600' },
            { label: '平均得分', value: '85%', change: '+3%', icon: Award, color: 'from-amber-500 to-amber-600' },
            { label: '画像完整度', value: '100%', change: '6 个维度', icon: TrendingUp, color: 'from-emerald-500 to-emerald-600' },
          ].map((stat) => (
            <motion.div
              key={stat.label}
              whileHover={{ y: -4, boxShadow: '0 12px 40px rgba(0,0,0,0.08)' }}
              className="relative overflow-hidden rounded-2xl border border-border/40 bg-white/80 backdrop-blur-sm p-5 shadow-sm transition-shadow"
            >
              <div className={`absolute top-0 right-0 h-24 w-24 rounded-bl-full bg-gradient-to-br ${stat.color} opacity-10`} />
              <stat.icon className={`h-8 w-8 rounded-xl bg-gradient-to-br ${stat.color} p-1.5 text-white`} />
              <p className="mt-3 text-3xl font-bold">{stat.value}</p>
              <p className="text-sm text-muted-foreground">{stat.label}</p>
              <p className="mt-1 text-xs font-medium text-emerald-600">{stat.change}</p>
            </motion.div>
          ))}
        </motion.div>

        {/* Quick Actions + Activity */}
        <div className="mt-8 grid gap-6 lg:grid-cols-3">
          {/* Quick Actions */}
          <motion.div variants={item} className="lg:col-span-1 space-y-4">
            <h2 className="text-lg font-semibold">快速操作</h2>
            {[
              { icon: '🧠', title: '构建/更新学习画像', href: '/profile', desc: '对话式智能分析' },
              { icon: '💬', title: 'AI 对话学习', href: '/chat', desc: '多智能体协同辅导' },
              { icon: '📚', title: '浏览学习资源', href: '/learning', desc: '7 种类型个性化资源' },
              { icon: '🗺️', title: '查看学习路径', href: '/path', desc: '动态规划最优路线' },
            ].map((action, i) => (
              <Link key={i} href={action.href}>
                <motion.div
                  whileHover={{ x: 4 }}
                  className="flex items-center gap-4 rounded-xl border border-border/40 bg-white p-4 shadow-sm hover:border-blue-200 transition-colors cursor-pointer"
                >
                  <span className="text-2xl">{action.icon}</span>
                  <div className="flex-1">
                    <p className="font-medium text-sm">{action.title}</p>
                    <p className="text-xs text-muted-foreground">{action.desc}</p>
                  </div>
                  <ChevronRight className="h-4 w-4 text-muted-foreground" />
                </motion.div>
              </Link>
            ))}
          </motion.div>

          {/* Activity Feed */}
          <motion.div variants={item} className="lg:col-span-2">
            <h2 className="text-lg font-semibold mb-4">最近活动</h2>
            <div className="space-y-3">
              {[
                { icon: '💬', title: '完成对话式画像构建', time: '2 小时前', dur: '15 分钟', color: 'bg-blue-100 text-blue-600' },
                { icon: '📚', title: '学习了《算法基础 — 动态规划》', time: '昨天 14:30', dur: '45 分钟', color: 'bg-purple-100 text-purple-600' },
                { icon: '✏️', title: '完成线性代数练习题 (88%)', time: '昨天 10:00', dur: '30 分钟', color: 'bg-amber-100 text-amber-600' },
                { icon: '🧠', title: '思维导图已生成并保存', time: '前天', dur: '新增 2 个', color: 'bg-emerald-100 text-emerald-600' },
                { icon: '🗺️', title: '学习路径已动态更新', time: '前天', dur: '调整 3 个节点', color: 'bg-rose-100 text-rose-600' },
                { icon: '💻', title: '完成实操案例练习', time: '3 天前', dur: '60 分钟', color: 'bg-cyan-100 text-cyan-600' },
              ].map((act, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.3 + i * 0.08 }}
                  className="flex items-center gap-4 rounded-xl border border-border/40 bg-white p-4 shadow-sm"
                >
                  <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${act.color}`}>
                    {act.icon}
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium">{act.title}</p>
                    <p className="text-xs text-muted-foreground">{act.time}</p>
                  </div>
                  <span className="text-xs text-muted-foreground">{act.dur}</span>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </div>

      </motion.main>
    </div>
  )
}
