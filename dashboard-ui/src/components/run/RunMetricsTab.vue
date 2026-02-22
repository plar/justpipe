<script setup lang="ts">
import { computed } from 'vue'
import { useRunStore } from '@/stores/run'
import { formatDuration } from '@/lib/utils'
import type { StepTiming, BarrierMetrics } from '@/types'
import MetricTile from '@/components/ui/MetricTile.vue'
import SectionHeader from '@/components/ui/SectionHeader.vue'

const runStore = useRunStore()
const metrics = computed(() => runStore.runtimeMetrics)

const stepLatencyRows = computed(() => {
  if (!metrics.value?.step_latency) return []
  return Object.entries(metrics.value.step_latency)
    .map(([name, t]: [string, StepTiming]) => ({
      name,
      count: t.count,
      avg: t.count > 0 ? t.total_s / t.count : 0,
      min: t.min_s,
      max: t.max_s,
    }))
    .sort((a, b) => b.avg - a.avg)
})

const barrierRows = computed(() => {
  if (!metrics.value?.barriers) return []
  return Object.entries(metrics.value.barriers)
    .map(([name, b]: [string, BarrierMetrics]) => ({ name, ...b }))
})

const eventTypeRows = computed(() => {
  if (!metrics.value?.events) return []
  return Object.entries(metrics.value.events)
    .sort(([, a], [, b]) => b - a)
})
</script>

<template>
  <div v-if="!metrics" class="rounded-lg border border-border bg-card p-8 text-center text-sm text-muted-foreground">
    No runtime metrics available for this run
  </div>
  <template v-else>
    <!-- Summary tiles -->
    <div class="mb-6 grid gap-4 sm:grid-cols-5 stagger-reveal">
      <MetricTile label="Tasks Started" :value="metrics.tasks.started" />
      <MetricTile label="Peak Active" :value="metrics.tasks.peak_active" />
      <MetricTile label="Tokens" :value="metrics.tokens" />
      <MetricTile label="Peak Queue" :value="metrics.queue.max_depth" />
      <MetricTile label="Suspends" :value="metrics.suspends" />
    </div>

    <!-- Step Latency table -->
    <div v-if="stepLatencyRows.length" class="mb-6 overflow-hidden rounded-lg border border-border">
      <SectionHeader label="Step Latency" class="border-b border-border bg-card px-4 py-3" />
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="bg-muted/50 text-left text-xs uppercase tracking-wider text-muted-foreground">
            <tr>
              <th class="px-4 py-2 font-medium">Step</th>
              <th class="px-4 py-2 text-right font-medium">Count</th>
              <th class="px-4 py-2 text-right font-medium">Avg</th>
              <th class="px-4 py-2 text-right font-medium">Min</th>
              <th class="px-4 py-2 text-right font-medium">Max</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-border">
            <tr v-for="row in stepLatencyRows" :key="row.name" class="hover:bg-accent/20">
              <td class="px-4 py-2 font-mono text-xs">{{ row.name }}</td>
              <td class="px-4 py-2 text-right tabular-nums">{{ row.count }}</td>
              <td class="px-4 py-2 text-right font-mono text-xs tabular-nums">{{ formatDuration(row.avg) }}</td>
              <td class="px-4 py-2 text-right font-mono text-xs tabular-nums text-muted-foreground">{{ formatDuration(row.min) }}</td>
              <td class="px-4 py-2 text-right font-mono text-xs tabular-nums text-muted-foreground">{{ formatDuration(row.max) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Barrier Stats -->
    <div v-if="barrierRows.length" class="mb-6 overflow-hidden rounded-lg border border-border">
      <SectionHeader label="Barrier Statistics" class="border-b border-border bg-card px-4 py-3" />
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="bg-muted/50 text-left text-xs uppercase tracking-wider text-muted-foreground">
            <tr>
              <th class="px-4 py-2 font-medium">Barrier</th>
              <th class="px-4 py-2 text-right font-medium">Waits</th>
              <th class="px-4 py-2 text-right font-medium">Releases</th>
              <th class="px-4 py-2 text-right font-medium">Timeouts</th>
              <th class="px-4 py-2 text-right font-medium">Max Wait</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-border">
            <tr v-for="row in barrierRows" :key="row.name" class="hover:bg-accent/20">
              <td class="px-4 py-2 font-mono text-xs">{{ row.name }}</td>
              <td class="px-4 py-2 text-right tabular-nums">{{ row.waits }}</td>
              <td class="px-4 py-2 text-right tabular-nums">{{ row.releases }}</td>
              <td class="px-4 py-2 text-right tabular-nums" :class="row.timeouts > 0 ? 'text-warning' : ''">{{ row.timeouts }}</td>
              <td class="px-4 py-2 text-right font-mono text-xs tabular-nums">{{ formatDuration(row.max_wait_s) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Map Stats -->
    <div v-if="metrics.maps.maps_started > 0" class="mb-6 rounded-lg border border-border bg-card p-4">
      <SectionHeader label="Map Statistics" />
      <div class="grid gap-4 sm:grid-cols-4">
        <div>
          <p class="text-xs uppercase tracking-wider text-muted-foreground">Maps Started</p>
          <p class="text-lg font-semibold tabular-nums">{{ metrics.maps.maps_started }}</p>
        </div>
        <div>
          <p class="text-xs uppercase tracking-wider text-muted-foreground">Maps Completed</p>
          <p class="text-lg font-semibold tabular-nums">{{ metrics.maps.maps_completed }}</p>
        </div>
        <div>
          <p class="text-xs uppercase tracking-wider text-muted-foreground">Workers Started</p>
          <p class="text-lg font-semibold tabular-nums">{{ metrics.maps.workers_started }}</p>
        </div>
        <div>
          <p class="text-xs uppercase tracking-wider text-muted-foreground">Peak Workers</p>
          <p class="text-lg font-semibold tabular-nums">{{ metrics.maps.peak_workers }}</p>
        </div>
      </div>
    </div>

    <!-- Event Type Breakdown -->
    <div v-if="eventTypeRows.length" class="rounded-lg border border-border bg-card p-4">
      <SectionHeader label="Event Type Breakdown" />
      <div class="space-y-2">
        <div v-for="[type, count] in eventTypeRows" :key="type" class="flex items-center gap-3">
          <span class="w-32 truncate font-mono text-xs text-muted-foreground">{{ type }}</span>
          <div class="flex-1">
            <div class="h-4 overflow-hidden rounded bg-muted">
              <div
                class="h-full rounded bg-info transition-all"
                :style="{ width: eventTypeRows.length ? (count / eventTypeRows[0]![1] * 100) + '%' : '0%' }"
              />
            </div>
          </div>
          <span class="w-10 text-right text-xs font-medium tabular-nums">{{ count }}</span>
        </div>
      </div>
    </div>
  </template>
</template>
