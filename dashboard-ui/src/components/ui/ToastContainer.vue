<script setup lang="ts">
import { useToast } from '@/composables/useToast'
import { Check, X, Info, AlertTriangle } from 'lucide-vue-next'

const { toasts, dismiss } = useToast()

const iconMap = { success: Check, error: AlertTriangle, info: Info }
</script>

<template>
  <Teleport to="body">
    <div class="fixed bottom-4 right-4 z-[100] flex flex-col-reverse gap-2 pointer-events-none">
      <TransitionGroup name="toast">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          class="pointer-events-auto flex w-80 items-start gap-3 rounded-lg border px-4 py-3 shadow-lg backdrop-blur-sm transition-opacity duration-300"
          :class="[
            toast.visible ? 'opacity-100' : 'opacity-0',
            {
              'border-success/30 bg-success/10 text-success': toast.type === 'success',
              'border-destructive/30 bg-destructive/10 text-destructive': toast.type === 'error',
              'border-info/30 bg-info/10 text-info': toast.type === 'info',
            },
          ]"
        >
          <component :is="iconMap[toast.type]" class="mt-0.5 h-4 w-4 shrink-0" />
          <span class="flex-1 text-sm">{{ toast.message }}</span>
          <button
            class="shrink-0 rounded p-0.5 opacity-60 transition-opacity hover:opacity-100"
            @click="dismiss(toast.id)"
          >
            <X class="h-3.5 w-3.5" />
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<style scoped>
.toast-enter-active {
  transition: all 0.3s ease-out;
}
.toast-leave-active {
  transition: all 0.3s ease-in;
}
.toast-enter-from {
  opacity: 0;
  transform: translateX(100%);
}
.toast-leave-to {
  opacity: 0;
  transform: translateX(100%);
}
</style>
