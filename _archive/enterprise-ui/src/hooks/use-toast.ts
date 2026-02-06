/**
 * Toast Hook
 *
 * Provides simple toast notifications for user feedback
 * Temporary implementation for build compatibility
 */

import { useState, useCallback } from 'react'

interface ToastMessage {
  id: string
  title: string
  description?: string
  variant?: 'default' | 'destructive' | 'success'
  duration?: number
}

interface ToastState {
  toasts: ToastMessage[]
}

let toastCounter = 0

// Simple toast implementation for build compatibility
export function useToast() {
  const [toasts, setToasts] = useState<ToastMessage[]>([])

  const toast = useCallback(
    ({ title, description, variant = 'default', duration = 5000 }: Omit<ToastMessage, 'id'>) => {
      const id = `toast-${++toastCounter}`
      const newToast: ToastMessage = {
        id,
        title,
        description,
        variant,
        duration,
      }

      setToasts((currentToasts) => [...currentToasts, newToast])

      // Auto-remove toast after duration
      setTimeout(() => {
        setToasts((currentToasts) =>
          currentToasts.filter((t) => t.id !== id)
        )
      }, duration)

      return {
        id,
        dismiss: () => {
          setToasts((currentToasts) =>
            currentToasts.filter((t) => t.id !== id)
          )
        },
        update: (updates: Partial<Omit<ToastMessage, 'id'>>) => {
          setToasts((currentToasts) =>
            currentToasts.map((t) =>
              t.id === id ? { ...t, ...updates } : t
            )
          )
        },
      }
    },
    []
  )

  const dismiss = useCallback((toastId?: string) => {
    if (toastId) {
      setToasts((currentToasts) =>
        currentToasts.filter((t) => t.id !== toastId)
      )
    } else {
      setToasts([])
    }
  }, [])

  return {
    toast,
    dismiss,
    toasts,
  }
}