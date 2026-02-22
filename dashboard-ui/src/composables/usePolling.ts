import { ref, onBeforeUnmount } from 'vue'

/**
 * Auto-polling with tick counter showing seconds since last refresh.
 */
export function usePolling(onRefresh: () => Promise<void> | void, intervalMs = 3000) {
  const lastRefreshedAt = ref(Date.now())
  const secondsSinceRefresh = ref(0)
  let pollTimer: ReturnType<typeof setInterval> | null = null
  let tickTimer: ReturnType<typeof setInterval> | null = null

  function start() {
    stop()
    lastRefreshedAt.value = Date.now()
    secondsSinceRefresh.value = 0
    pollTimer = setInterval(async () => {
      await onRefresh()
      lastRefreshedAt.value = Date.now()
      secondsSinceRefresh.value = 0
    }, intervalMs)
    tickTimer = setInterval(() => {
      secondsSinceRefresh.value = Math.floor((Date.now() - lastRefreshedAt.value) / 1000)
    }, 1000)
  }

  function stop() {
    if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
    if (tickTimer) { clearInterval(tickTimer); tickTimer = null }
  }

  onBeforeUnmount(stop)

  return { secondsSinceRefresh, start, stop }
}
