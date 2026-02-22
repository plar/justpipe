import { ref } from 'vue'

export type ToastType = 'success' | 'error' | 'info'

export interface Toast {
  id: number
  message: string
  type: ToastType
  visible: boolean
}

const toasts = ref<Toast[]>([])
let nextId = 0

const AUTO_DISMISS_MS: Record<ToastType, number> = {
  success: 3000,
  info: 3000,
  error: 5000,
}

function addToast(message: string, type: ToastType = 'info') {
  const id = nextId++
  const toast: Toast = { id, message, type, visible: true }
  toasts.value.push(toast)

  setTimeout(() => {
    dismiss(id)
  }, AUTO_DISMISS_MS[type])
}

function dismiss(id: number) {
  const toast = toasts.value.find((t) => t.id === id)
  if (toast) {
    toast.visible = false
    // Remove from array after fade-out transition
    setTimeout(() => {
      toasts.value = toasts.value.filter((t) => t.id !== id)
    }, 300)
  }
}

export function useToast() {
  return {
    toasts,
    toast: addToast,
    dismiss,
  }
}
