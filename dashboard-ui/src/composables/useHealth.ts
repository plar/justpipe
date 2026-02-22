import { ref, onMounted, onBeforeUnmount } from 'vue'
import { api } from '@/api/client'

export type HealthStatus = 'online' | 'checking' | 'offline'

const status = ref<HealthStatus>('checking')
const lastSeenAt = ref<string | null>(null)
const totalPipelines = ref(0)
let failCount = 0
let pollTimer: ReturnType<typeof setInterval> | null = null
let refCount = 0

// Callbacks invoked when pipelines first appear (transition from 0 → >0)
const discoveryCallbacks: Array<() => void> = []

const POLL_INTERVAL_MS = 15_000
const FAIL_THRESHOLD = 2

async function check() {
  const result = await api.health()
  if (result.ok) {
    failCount = 0
    status.value = 'online'
    lastSeenAt.value = result.timestamp

    const prev = totalPipelines.value
    totalPipelines.value = result.totalPipelines
    if (prev === 0 && result.totalPipelines > 0) {
      discoveryCallbacks.forEach((cb) => cb())
    }
  } else {
    failCount++
    if (failCount >= FAIL_THRESHOLD) {
      status.value = 'offline'
    }
  }
}

function startPolling() {
  if (pollTimer) return
  check()
  pollTimer = setInterval(check, POLL_INTERVAL_MS)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

export function useHealth() {
  onMounted(() => {
    refCount++
    if (refCount === 1) startPolling()
  })

  onBeforeUnmount(() => {
    refCount--
    if (refCount <= 0) {
      refCount = 0
      stopPolling()
    }
  })

  return { status, lastSeenAt, totalPipelines }
}

/**
 * Register a callback that fires once when pipelines are first discovered
 * (health reports totalPipelines going from 0 to >0).
 */
export function onPipelinesDiscovered(cb: () => void) {
  discoveryCallbacks.push(cb)

  // If pipelines already exist, fire immediately
  if (totalPipelines.value > 0) {
    cb()
  }

  onBeforeUnmount(() => {
    const idx = discoveryCallbacks.indexOf(cb)
    if (idx >= 0) discoveryCallbacks.splice(idx, 1)
  })
}
