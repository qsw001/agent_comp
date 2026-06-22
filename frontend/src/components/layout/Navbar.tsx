'use client'
import { useState } from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import { Menu, X, BookOpen, User, MessageCircle, Map, BarChart3, Home, LogOut } from 'lucide-react'
import { clsx } from 'clsx'
import { useAuthStore } from '@/stores'
import { clearAuthToken } from '@/lib/auth'

const navItems = [
  { href: '/dashboard', label: '仪表盘', icon: Home },
  { href: '/profile', label: '学习画像', icon: User },
  { href: '/chat', label: 'AI 对话', icon: MessageCircle },
  { href: '/learning', label: '资源中心', icon: BookOpen },
  { href: '/path', label: '学习路径', icon: Map },
  { href: '/evaluation', label: '效果评估', icon: BarChart3 },
]

export function Navbar() {
  const pathname = usePathname()
  const router = useRouter()
  const { logout } = useAuthStore()
  const [mobileOpen, setMobileOpen] = useState(false)

  const handleLogout = () => {
    clearAuthToken()
    logout()
    setMobileOpen(false)
    router.push('/login')
  }

  return (
    <motion.header
      initial={{ y: -80 }}
      animate={{ y: 0 }}
      className="sticky top-0 z-50 border-b border-border/40 bg-white/80 backdrop-blur-xl"
    >
      <nav className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <Link href="/dashboard" className="flex items-center gap-2">
            <motion.div
              whileHover={{ rotate: 10, scale: 1.1 }}
              className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 text-white font-bold text-lg"
            >
              A
            </motion.div>
            <span className="text-lg font-bold tracking-tight">
              <span className="gradient-text">AI 教育平台</span>
            </span>
          </Link>

          {/* Desktop Nav */}
          <div className="hidden md:flex items-center gap-1">
            {navItems.map((item) => (
              <Link key={item.href} href={item.href}>
                <motion.div
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className={clsx(
                    'relative flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                    pathname === item.href
                      ? 'text-blue-600'
                      : 'text-muted-foreground hover:text-foreground'
                  )}
                >
                  <item.icon className="h-4 w-4" />
                  {item.label}
                  {pathname === item.href && (
                    <motion.div
                      layoutId="nav-indicator"
                      className="absolute bottom-0 left-2 right-2 h-0.5 rounded-full bg-blue-500"
                      transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                    />
                  )}
                </motion.div>
              </Link>
            ))}
            {/* Divider + Logout */}
            <div className="mx-1 h-5 w-px bg-border" />
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleLogout}
              className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground hover:text-red-500 transition-colors"
            >
              <LogOut className="h-4 w-4" />
              退出
            </motion.button>
          </div>

          {/* Mobile Toggle */}
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="md:hidden p-2 rounded-lg hover:bg-muted transition-colors"
          >
            {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>

        {/* Mobile Menu */}
        <AnimatePresence>
          {mobileOpen && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="md:hidden overflow-hidden border-t border-border/40"
            >
              <div className="space-y-1 px-2 py-3">
                {navItems.map((item) => (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setMobileOpen(false)}
                    className={clsx(
                      'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                      pathname === item.href
                        ? 'bg-blue-50 text-blue-600'
                        : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                    )}
                  >
                    <item.icon className="h-5 w-5" />
                    {item.label}
                  </Link>
                ))}
                {/* Mobile Logout */}
                <div className="pt-2 border-t border-border/40 mt-2">
                  <button
                    onClick={handleLogout}
                    className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-muted-foreground hover:bg-red-50 hover:text-red-500 transition-colors"
                  >
                    <LogOut className="h-5 w-5" />
                    退出登录
                  </button>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </nav>
    </motion.header>
  )
}
