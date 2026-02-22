<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { modKeyName } from '@/lib/platform'

const open = defineModel<boolean>('open', { required: true })

const shortcutGroups = [
  {
    label: 'Global',
    shortcuts: [
      { keys: [modKeyName, 'K'], description: 'Search runs' },
      { keys: ['?'], description: 'Show keyboard shortcuts' },
    ],
  },
  {
    label: 'Navigation',
    shortcuts: [
      { keys: ['1'], description: 'First tab' },
      { keys: ['2'], description: 'Second tab' },
      { keys: ['3'], description: 'Third tab' },
      { keys: ['4'], description: 'Fourth tab' },
    ],
  },
  {
    label: 'Actions',
    shortcuts: [
      { keys: ['Esc'], description: 'Close panel' },
      { keys: ['/'], description: 'Focus search' },
    ],
  },
]

function close() {
  open.value = false
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    e.preventDefault()
    close()
    return
  }

  // Open on `?` when not in an input
  if (!open.value && e.key === '?' && !isInputFocused()) {
    e.preventDefault()
    open.value = true
  }
}

function isInputFocused(): boolean {
  const el = document.activeElement
  if (!el) return false
  const tag = el.tagName
  return tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || (el as HTMLElement).isContentEditable
}

onMounted(() => {
  document.addEventListener('keydown', onKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', onKeydown)
})
</script>

<template>
  <Teleport to="body">
    <Transition name="overlay">
      <div
        v-if="open"
        class="fixed inset-0 z-[200] flex items-center justify-center"
      >
        <!-- Backdrop -->
        <div
          class="absolute inset-0 bg-background/70 backdrop-blur-sm"
          @click="close"
        />

        <!-- Panel -->
        <div class="relative w-full max-w-md px-4">
          <div class="overflow-hidden rounded-xl border border-border bg-card shadow-2xl">
            <!-- Header -->
            <div class="flex items-center justify-between border-b border-border px-5 py-4">
              <h2 class="text-sm font-semibold text-foreground">Keyboard Shortcuts</h2>
              <kbd
                class="inline-flex items-center rounded border border-border bg-muted px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground cursor-pointer hover:bg-accent"
                @click="close"
              >
                ESC
              </kbd>
            </div>

            <!-- Groups -->
            <div class="divide-y divide-border">
              <div v-for="group in shortcutGroups" :key="group.label" class="px-5 py-4">
                <h3 class="mb-3 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                  {{ group.label }}
                </h3>
                <div class="space-y-2.5">
                  <div
                    v-for="shortcut in group.shortcuts"
                    :key="shortcut.description"
                    class="flex items-center justify-between"
                  >
                    <span class="text-sm text-foreground">{{ shortcut.description }}</span>
                    <div class="flex items-center gap-1">
                      <template v-for="(key, i) in shortcut.keys" :key="key">
                        <span v-if="i > 0" class="text-xs text-muted-foreground">+</span>
                        <kbd class="inline-flex h-6 min-w-[24px] items-center justify-center rounded border border-border bg-muted px-1.5 font-mono text-[11px] font-medium text-muted-foreground shadow-sm">
                          {{ key }}
                        </kbd>
                      </template>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.overlay-enter-active {
  transition: opacity 0.15s ease-out;
}
.overlay-leave-active {
  transition: opacity 0.1s ease-in;
}
.overlay-enter-from,
.overlay-leave-to {
  opacity: 0;
}
</style>
