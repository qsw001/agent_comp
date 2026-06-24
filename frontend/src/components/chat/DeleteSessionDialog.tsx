'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Loader2, AlertTriangle } from 'lucide-react'
import Dialog from './Dialog'

interface DeleteSessionDialogProps {
  open: boolean
  onClose: () => void
  sessionTitle: string
  onConfirm: () => Promise<boolean>
}

export default function DeleteSessionDialog({ open, onClose, sessionTitle, onConfirm }: DeleteSessionDialogProps) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleDelete = async () => {
    if (loading) return
    setLoading(true)
    setError('')
    try {
      const ok = await onConfirm()
      if (ok) {
        onClose()
      } else {
        setError('删除失败，请稍后重试')
      }
    } catch {
      setError('网络异常，请稍后重试')
    } finally {
      setLoading(false)
    }
  }

  // Reset on open
  if (open && loading) {
    // keep state; reset handled by parent re-render
  }

  return (
    <Dialog
      open={open}
      onClose={() => { if (!loading) onClose() }}
      title="删除此对话？"
    >
      <div className="space-y-4">
        <div className="flex items-start gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-red-100">
            <AlertTriangle className="h-5 w-5 text-red-500" />
          </div>
          <div className="text-sm text-muted-foreground">
            <p>删除后，该对话及其聊天记录将无法恢复。</p>
            <p className="mt-1.5 truncate rounded-lg bg-muted px-3 py-2 text-xs font-medium text-foreground">
              {sessionTitle || '新对话'}
            </p>
          </div>
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
            onClick={handleDelete}
            disabled={loading}
            className="flex items-center gap-2 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition-all hover:bg-red-700 disabled:opacity-40"
          >
            {loading && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
            删除
          </motion.button>
        </div>
      </div>
    </Dialog>
  )
}
