'use client'

import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Plus, MessageSquare, X, Loader2, MoreHorizontal, Pencil, Trash2 } from 'lucide-react'
import type { ChatSession } from '@/types'

interface SidebarProps {
  sessions: ChatSession[]
  currentSessionId: string | null
  onSelect: (id: string) => void
  onDelete: (id: string) => void
  onRename: (id: string) => void
  onNewChat: () => void
  open: boolean
  onClose: () => void
  deleting: string | null
}

export default function ChatSidebar({
  sessions,
  currentSessionId,
  onSelect,
  onDelete,
  onRename,
  onNewChat,
  open,
  onClose,
  deleting,
}: SidebarProps) {
  const [menuOpen, setMenuOpen] = useState<string | null>(null)
  const menuRef = useRef<HTMLDivElement>(null)

  // 点击外部关闭菜单
  useEffect(() => {
    if (!menuOpen) return
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(null)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [menuOpen])

  const content = (
    <div className="flex h-full flex-col">
      {/* 新建对话按钮 */}
      <div className="p-3">
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => { onNewChat(); onClose() }}
          className="flex w-full items-center gap-2 rounded-xl border border-border/40 bg-white/80 px-4 py-2.5 text-sm font-medium shadow-sm transition-all hover:bg-white hover:shadow-md"
        >
          <Plus className="h-4 w-4" />
          新建对话
        </motion.button>
      </div>

      {/* 会话列表 */}
      <div className="flex-1 overflow-y-auto px-2">
        {sessions.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <MessageSquare className="mb-2 h-8 w-8 text-muted-foreground/40" />
            <p className="text-xs text-muted-foreground">暂无聊天记录</p>
          </div>
        ) : (
          <div className="space-y-0.5">
            {sessions.map((s) => {
              const isActive = s.id === currentSessionId
              const isDeleting = deleting === s.id
              return (
                <motion.div
                  key={s.id}
                  layout
                  className={`group relative flex items-center rounded-lg px-3 py-2.5 text-sm transition-colors cursor-pointer ${
                    isActive
                      ? 'bg-blue-50 text-blue-700 font-medium'
                      : 'text-foreground/80 hover:bg-muted/60'
                  }`}
                  onClick={() => { onSelect(s.id); onClose() }}
                >
                  <MessageSquare className={`mr-2 h-4 w-4 shrink-0 ${isActive ? 'text-blue-500' : 'text-muted-foreground/60'}`} />
                  <span className="truncate flex-1">{s.title || '新对话'}</span>

                  {/* More 按钮 */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      setMenuOpen(menuOpen === s.id ? null : s.id)
                    }}
                    className="shrink-0 rounded p-1 text-muted-foreground/40 opacity-0 transition-all hover:bg-muted hover:text-foreground group-hover:opacity-100"
                    title="更多操作"
                  >
                    <MoreHorizontal className="h-3.5 w-3.5" />
                  </button>

                  {/* 下拉菜单 */}
                  <AnimatePresence>
                    {menuOpen === s.id && (
                      <motion.div
                        ref={menuRef}
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.95 }}
                        className="absolute right-2 top-full z-50 mt-1 w-32 rounded-xl border border-border/40 bg-white shadow-xl"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <button
                          onClick={() => { setMenuOpen(null); onRename(s.id) }}
                          className="flex w-full items-center gap-2 rounded-t-xl px-3 py-2 text-xs hover:bg-muted transition-colors"
                        >
                          <Pencil className="h-3.5 w-3.5" />
                          重命名
                        </button>
                        <button
                          onClick={() => { setMenuOpen(null); onDelete(s.id) }}
                          disabled={isDeleting}
                          className="flex w-full items-center gap-2 rounded-b-xl px-3 py-2 text-xs text-red-600 hover:bg-red-50 transition-colors disabled:opacity-50"
                        >
                          {isDeleting ? (
                            <Loader2 className="h-3.5 w-3.5 animate-spin" />
                          ) : (
                            <Trash2 className="h-3.5 w-3.5" />
                          )}
                          删除
                        </button>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )

  return (
    <>
      {/* 桌面端：固定侧栏 */}
      <aside className="hidden md:flex md:w-72 md:shrink-0 md:flex-col md:border-r md:border-border/40 md:bg-white/60 md:backdrop-blur-sm">
        {content}
      </aside>

      {/* 移动端：抽屉覆盖 */}
      <AnimatePresence>
        {open && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-40 bg-black/40 md:hidden"
              onClick={onClose}
            />
            <motion.aside
              initial={{ x: -300 }}
              animate={{ x: 0 }}
              exit={{ x: -300 }}
              transition={{ type: 'spring', damping: 30, stiffness: 300 }}
              className="fixed left-0 top-0 z-50 h-full w-72 bg-white/95 backdrop-blur-xl shadow-2xl md:hidden"
            >
              <div className="flex items-center justify-between border-b border-border/40 px-3 py-3">
                <span className="text-sm font-medium">会话列表</span>
                <button onClick={onClose} className="rounded-lg p-1.5 hover:bg-muted">
                  <X className="h-4 w-4" />
                </button>
              </div>
              {content}
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </>
  )
}
