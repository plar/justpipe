<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, nextTick, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Search, CornerDownLeft } from 'lucide-vue-next'
import type { Run } from '@/types'
import { api } from '@/api/client'
import { shortId, relativeTime } from '@/lib/utils'
import { statusBadgeVariant } from '@/lib/view-helpers'
import StatusIndicator from './StatusIndicator.vue'
import Badge from './Badge.vue'

const open = defineModel<boolean>('open', { required: true })

const router = useRouter()
const query = ref('')
const results = ref<Run[]>([])
const loading = ref(false)
const selectedIndex = ref(0)
const inputRef = ref<HTMLInputElement | null>(null)

let debounceTimer: ReturnType<typeof setTimeout> | null = null

// Global Cmd+K / Ctrl+K listener
function onGlobalKeydown(e: KeyboardEvent) {
  if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
    e.preventDefault()
    open.value = !open.value
  }
}

onMounted(() => {
  document.addEventListener('keydown', onGlobalKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', onGlobalKeydown)
})

// Auto-focus input when opened
watch(open, async (isOpen) => {
  if (isOpen) {
    query.value = ''
    results.value = []
    selectedIndex.value = 0
    await nextTick()
    inputRef.value?.focus()
  }
})

// Debounced search
watch(query, (val) => {
  if (debounceTimer) clearTimeout(debounceTimer)

  if (val.length < 2) {
    results.value = []
    loading.value = false
    return
  }

  loading.value = true
  debounceTimer = setTimeout(async () => {
    try {
      results.value = await api.searchRuns(val)
    } catch {
      results.value = []
    } finally {
      loading.value = false
    }
  }, 300)
})

const hasQuery = computed(() => query.value.length >= 2)

function close() {
  open.value = false
}

function navigate(run: Run) {
  router.push(`/run/${run.run_id}`)
  close()
}

function onKeydown(e: KeyboardEvent) {
  switch (e.key) {
    case 'Escape':
      e.preventDefault()
      close()
      break
    case 'ArrowDown':
      e.preventDefault()
      if (results.value.length > 0) {
        selectedIndex.value = (selectedIndex.value + 1) % results.value.length
      }
      break
    case 'ArrowUp':
      e.preventDefault()
      if (results.value.length > 0) {
        selectedIndex.value = (selectedIndex.value - 1 + results.value.length) % results.value.length
      }
      break
    case 'Enter': {
      e.preventDefault()
      const run = results.value[selectedIndex.value]
      if (run) navigate(run)
      break
    }
  }
}

// Reset selection when results change
watch(results, () => {
  selectedIndex.value = 0
})
</script>

<template>
  <Teleport to="body">
    <Transition name="palette">
      <div
        v-if="open"
        class="fixed inset-0 z-[200] flex justify-center"
        @keydown="onKeydown"
      >
        <!-- Backdrop -->
        <div
          class="absolute inset-0 bg-background/70 backdrop-blur-sm"
          @click="close"
        />

        <!-- Panel -->
        <div class="relative mt-[min(200px,20vh)] h-fit w-full max-w-[640px] px-4">
          <div class="overflow-hidden rounded-xl border border-border bg-card shadow-2xl">
            <!-- Search input -->
            <div class="flex items-center gap-3 border-b border-border px-4">
              <Search class="h-4 w-4 shrink-0 text-muted-foreground" />
              <input
                ref="inputRef"
                v-model="query"
                type="text"
                placeholder="Search runs by ID, pipeline name..."
                class="h-12 flex-1 bg-transparent text-sm text-foreground placeholder:text-muted-foreground focus:outline-none"
              />
              <kbd class="hidden shrink-0 rounded border border-border bg-muted px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground sm:inline">
                ESC
              </kbd>
            </div>

            <!-- Results -->
            <div class="max-h-[min(400px,50vh)] overflow-y-auto">
              <!-- Empty state: no query -->
              <div v-if="!hasQuery && !loading" class="px-4 py-8 text-center text-sm text-muted-foreground">
                Type to search runs by ID prefix or pipeline name...
              </div>

              <!-- Loading -->
              <div v-else-if="loading" class="px-4 py-8 text-center text-sm text-muted-foreground">
                Searching...
              </div>

              <!-- No results -->
              <div v-else-if="hasQuery && results.length === 0" class="px-4 py-8 text-center text-sm text-muted-foreground">
                No runs found
              </div>

              <!-- Results list -->
              <template v-else>
                <button
                  v-for="(run, i) in results"
                  :key="run.run_id"
                  class="flex w-full items-center gap-3 px-4 py-2.5 text-left text-sm transition-colors"
                  :class="i === selectedIndex ? 'bg-accent/40 text-accent-foreground' : 'text-foreground hover:bg-accent/20'"
                  @click="navigate(run)"
                  @mouseenter="selectedIndex = i"
                >
                  <StatusIndicator :status="run.status" size="sm" />
                  <span class="font-mono text-xs">{{ shortId(run.run_id) }}</span>
                  <span class="truncate text-xs text-muted-foreground">{{ run.pipeline_name }}</span>
                  <Badge :variant="statusBadgeVariant(run.status)" class="ml-auto shrink-0">
                    {{ run.status }}
                  </Badge>
                  <span class="shrink-0 text-xs text-muted-foreground">{{ relativeTime(run.start_time) }}</span>
                </button>
              </template>
            </div>

            <!-- Footer -->
            <div class="flex items-center gap-4 border-t border-border px-4 py-2 text-[11px] text-muted-foreground">
              <span class="flex items-center gap-1">
                <CornerDownLeft class="h-3 w-3" /> select
              </span>
              <span class="flex items-center gap-1">
                <span class="font-mono">&uarr;&darr;</span> navigate
              </span>
              <span class="flex items-center gap-1">
                <kbd class="rounded border border-border px-1 py-px text-[10px]">esc</kbd> close
              </span>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.palette-enter-active {
  transition: opacity 0.15s ease-out;
}
.palette-leave-active {
  transition: opacity 0.1s ease-in;
}
.palette-enter-from,
.palette-leave-to {
  opacity: 0;
}
</style>
