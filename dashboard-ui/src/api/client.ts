import type {
  PipelineSummary,
  Run,
  PipelineEvent,
  TimelineEntry,
  Comparison,
  Stats,
} from '@/types'

const BASE = '/api'

async function request<T>(path: string, method: 'GET' | 'POST' = 'GET'): Promise<T> {
  const res = await fetch(`${BASE}${path}`, method === 'POST' ? { method } : undefined)
  if (!res.ok) {
    throw new Error(`API ${res.status}: ${res.statusText}`)
  }
  return res.json()
}

/** Build a query string from a record, omitting null/undefined values. */
function buildQuery(params: Record<string, string | number | boolean | undefined | null>): string {
  const qs = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value != null && value !== '') qs.set(key, String(value))
  }
  const s = qs.toString()
  return s ? `?${s}` : ''
}

export const api = {
  listPipelines(): Promise<PipelineSummary[]> {
    return request('/pipelines')
  },

  getPipeline(hash: string): Promise<PipelineSummary> {
    return request(`/pipelines/${hash}`)
  },

  listRuns(
    hash: string,
    params?: { status?: string; limit?: number; offset?: number }
  ): Promise<Run[]> {
    const q = buildQuery({
      status: params?.status,
      limit: params?.limit,
      offset: params?.offset,
    })
    return request(`/pipelines/${hash}/runs${q}`)
  },

  getRun(id: string): Promise<Run> {
    return request(`/runs/${id}`)
  },

  getEvents(runId: string, type?: string): Promise<PipelineEvent[]> {
    const q = type ? `?type=${type}` : ''
    return request(`/runs/${runId}/events${q}`)
  },

  getTimeline(runId: string): Promise<TimelineEntry[]> {
    return request(`/runs/${runId}/timeline`)
  },

  compare(run1: string, run2: string): Promise<Comparison> {
    return request(`/compare?run1=${run1}&run2=${run2}`)
  },

  getStats(hash: string, days = 7): Promise<Stats> {
    return request(`/stats/${hash}?days=${days}`)
  },

  async exportRun(runId: string): Promise<{ run: Run; events: PipelineEvent[] }> {
    const [run, events] = await Promise.all([this.getRun(runId), this.getEvents(runId)])
    return { run, events }
  },

  searchRuns(prefix: string, limit = 10): Promise<Run[]> {
    return request(`/runs/search?q=${encodeURIComponent(prefix)}&limit=${limit}`)
  },

  async health(): Promise<{ ok: boolean; timestamp: string | null; totalPipelines: number }> {
    try {
      const res = await fetch(`${BASE}/health`)
      if (!res.ok) return { ok: false, timestamp: null, totalPipelines: 0 }
      const data = await res.json()
      return { ok: true, timestamp: data.timestamp ?? null, totalPipelines: data.total_pipelines ?? 0 }
    } catch {
      return { ok: false, timestamp: null, totalPipelines: 0 }
    }
  },

  cleanupRuns(
    hash: string,
    params: { older_than_days?: number; status?: string; keep?: number; dry_run?: boolean }
  ): Promise<{ count: number; runs: Run[] }> {
    const q = buildQuery({
      older_than_days: params.older_than_days,
      status: params.status,
      keep: params.keep,
      dry_run: params.dry_run,
    })
    return request(`/pipelines/${hash}/cleanup${q}`, 'POST')
  },
}
