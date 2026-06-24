'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Loader2 } from 'lucide-react'
import Dialog from './Dialog'

interface RenameDialogProps {
  open: boolean
  onClose: () => void
  currentTitle: string
  onRename: (newTitle: string) => Promise<boolean>
}

export default function RenameDialog({ open, onClose, currentTitle, onRename }: RenameDialogProps) {
  const [value, setValue] = useState(currentTitle)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleOpen = (isOpen: boolean) => {
    if (isOpen) {
      setValue(currentTitle)
      setError('')
      setLoading(false)
    }
  }

  const handleSubmit = async () => {
    const trimmed = value.trim()
    if (!trimmed || trimmed.length > 60 || loading) return
    setLoading(true)
    setError('')
    try {
      const ok = await onRename(trimmed)
      if (ok) {
        onClose()
      } else {
        setError('重命名失败，请稍后重试')
      }
    } catch {
      setError('网络异常，请稍后重试')
    } finally {
      setLoading(false)
    }
  }

  // Reset state when dialog opens
  if (open && value !== currentTitle && !loading) {
    // Use effect-like pattern
  }

  return (
    <div onAnimationStart={() => handleOpen(true)}>
      <Dialog
        open={open}
        onClose={() => { if (!loading) onClose() }}
        title="重命名对话"
      >
        <div className="space-y-3">
          <div>
            <input
              value={value}
              onChange={(e) => {
                if (e.target.value.length <= 60) setValue(e.target.value)
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleSubmit()
                if (e.key === 'Escape' && !loading) onClose()
              }}
              placeholder="输入对话名称"
              maxLength={60}
              disabled={loading}
              autoFocus
              className="w-full rounded-xl border border-border bg-background px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500/20 transition-shadow disabled:opacity-50"
            />
            <p className="mt-1.5 text-right text-xs text-muted-foreground">
              {value.trim().length} / 60
            </p>
          </div>

          {error && (
            <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-600">{error}</p>
          )}

          <div className="flex items-center justify-end gap-2 pt-1">
            <button
              onClick={onClose}
              disabled={loading}
              className="rounded-lg px-4 py-2 text-sm text-muted-foreground hover:bg-muted transition-colors disabled:opacity-50"
            >
              取消
            </button>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={handleSubmit}
              disabled={!value.trim() || loading}
              className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition-all hover:bg-blue-700 disabled:opacity-40"
            >
              {loading && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
              保存
            </motion.button>
          </div>
        </div>
      </Dialog>
    </div>
  )
}
