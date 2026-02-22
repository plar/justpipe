import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/api/client'
import type { Run, PipelineEvent, TimelineEntry } from '@/types'
import { computeCriticalPath } from '@/lib/critical-path'
import { processEvents, extractFinishPayload } from '@/lib/event-processor'

export const useRunStore = defineStore('run', () => {
  /* ── State ───────────────────────────────────────────────── */
  const run = ref<Run | null>(null)
  const events = ref<PipelineEvent[]>([])
  const timeline = ref<TimelineEntry[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  /* ── Computed ────────────────────────────────────────────── */

  const criticalPath = computed(() =>
    timeline.value.length === 0 ? new Set<string>() : computeCriticalPath(timeline.value)
  )

  const steps = computed(() => processEvents(events.value))

  const finishPayload = computed(() => extractFinishPayload(events.value))

  const runtimeMetrics = computed(() => finishPayload.value?.metrics ?? null)

  /** Events filtered by step name */
  function eventsForStep(stepName: string): PipelineEvent[] {
    return events.value.filter((e) => e.step_name === stepName)
  }

  /** Events for a specific invocation of a step (0-based invocation index).
   *  Groups by STEP_START boundaries to isolate each invocation. */
  function eventsForInvocation(stepName: string, invocationIndex: number): PipelineEvent[] {
    const stepEvents = events.value.filter((e) => e.step_name === stepName)
    const invocations: PipelineEvent[][] = []
    let current: PipelineEvent[] = []
    for (const e of stepEvents) {
      if (e.event_type.toLowerCase() === 'step_start') {
        if (current.length > 0) invocations.push(current)
        current = [e]
      } else {
        current.push(e)
      }
    }
    if (current.length > 0) invocations.push(current)
    return invocations[invocationIndex] ?? stepEvents
  }

  /** Timeline range for waterfall rendering */
  const timelineRange = computed(() => {
    if (timeline.value.length === 0) return { min: 0, max: 1, span: 1 }
    const starts = timeline.value.map((e) => new Date(e.start_time).getTime())
    const ends = timeline.value.map((e) => new Date(e.end_time).getTime())
    const min = Math.min(...starts)
    const max = Math.max(...ends)
    return { min, max, span: max - min || 1 }
  })

  /* ── Actions ─────────────────────────────────────────────── */

  /** Fetch all run data in parallel and apply to state. */
  async function loadRunData(runId: string): Promise<void> {
    const [r, ev, tl] = await Promise.all([
      api.getRun(runId),
      api.getEvents(runId),
      api.getTimeline(runId),
    ])
    run.value = r
    events.value = ev
    timeline.value = tl
  }

  async function fetchRun(runId: string) {
    loading.value = true
    error.value = null
    run.value = null
    events.value = []
    timeline.value = []
    try {
      await loadRunData(runId)
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e)
    } finally {
      loading.value = false
    }
  }

  /** Silent refresh — updates data without setting loading flag (no flicker) */
  async function refreshRun(runId: string) {
    try {
      await loadRunData(runId)
    } catch {
      // Silent refresh — don't overwrite existing error state
    }
  }

  return {
    run,
    events,
    timeline,
    loading,
    error,
    criticalPath,
    steps,
    finishPayload,
    runtimeMetrics,
    timelineRange,
    eventsForStep,
    eventsForInvocation,
    fetchRun,
    refreshRun,
  }
})
