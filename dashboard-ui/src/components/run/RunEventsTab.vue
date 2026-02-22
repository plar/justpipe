<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useRunStore } from '@/stores/run'
import { useSetToggle } from '@/composables/useSetToggle'
import { formatTimestamp } from '@/lib/utils'
import EventRow from '@/components/ui/EventRow.vue'
import Badge from '@/components/ui/Badge.vue'
import { ChevronRight, Layers, Clock, ChevronsDownUp, ChevronsUpDown } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const runStore = useRunStore()

const expandedEvents = useSetToggle<number>()
const timeMode = ref<'absolute' | 'relative'>('absolute')

const firstEventTime = computed(() => {
  const first = runStore.events[0]
  return first ? new Date(first.timestamp).getTime() : 0
})

function eventOffset(timestamp: string): string {
  const ms = new Date(timestamp).getTime() - firstEventTime.value
  if (ms < 1000) return `+${ms}ms`
  if (ms < 60000) return `+${(ms / 1000).toFixed(1)}s`
  return `+${(ms / 60000).toFixed(1)}m`
}

// Event type filter chips (init from URL)
const eventTypeFilter = useSetToggle(
  route.query.events ? (route.query.events as string).split(',') : []
)
const EVENT_TYPE_ORDER: Record<string, number> = {
  start: 0,
  step_start: 1, step_end: 2, step_error: 3,
  map_start: 4, map_worker: 5, map_complete: 6,
  barrier_wait: 7, barrier_release: 8,
  token: 9, suspend: 10, timeout: 11, cancelled: 12, finish: 13,
}
const eventTypes = computed(() => {
  const types = new Set(runStore.events.map((e) => e.event_type))
  return Array.from(types).sort((a, b) => (EVENT_TYPE_ORDER[a] ?? 99) - (EVENT_TYPE_ORDER[b] ?? 99))
})
const filteredEvents = computed(() => {
  if (eventTypeFilter.items.value.size === 0) return runStore.events
  return runStore.events.filter((e) => eventTypeFilter.has(e.event_type))
})

// Sync eventTypeFilter to URL
watch(eventTypeFilter.items, (val) => {
  router.replace({ query: { ...route.query, events: val.size > 0 ? Array.from(val).join(',') : undefined } })
}, { deep: true })

// Step grouping (init from URL)
const LIFECYCLE_TYPES = new Set(['start', 'finish'])
const groupByStep = ref(route.query.group === 'step')
const expandedGroups = useSetToggle()

// Sync groupByStep to URL
watch(groupByStep, (val) => {
  router.replace({ query: { ...route.query, group: val ? 'step' : undefined } })
})

const groupedEvents = computed(() => {
  const groups = new Map<string, typeof filteredEvents.value>()
  for (const event of filteredEvents.value) {
    const key = (!event.step_name || LIFECYCLE_TYPES.has(event.event_type)) ? 'Lifecycle' : event.step_name
    if (!groups.has(key)) groups.set(key, [])
    groups.get(key)!.push(event)
  }
  return Array.from(groups.entries())
    .map(([name, events]) => ({ name, events, firstTimestamp: events[0]?.timestamp ?? '' }))
    .sort((a, b) => a.firstTimestamp.localeCompare(b.firstTimestamp))
})

function toggleEvent(seq: number) {
  expandedEvents.toggle(seq)
}

const allExpanded = computed(() => {
  if (filteredEvents.value.length === 0) return false
  const eventsExpanded = filteredEvents.value.every(e => expandedEvents.has(e.seq))
  if (groupByStep.value) {
    return groupedEvents.value.every(g => expandedGroups.has(g.name)) && eventsExpanded
  }
  return eventsExpanded
})

function expandAll() {
  expandedEvents.addAll(filteredEvents.value.map(e => e.seq))
  if (groupByStep.value) {
    expandedGroups.addAll(groupedEvents.value.map(g => g.name))
  }
}

function collapseAll() {
  expandedEvents.clear()
  expandedGroups.clear()
}

function formatEventTime(timestamp: string): string {
  return timeMode.value === 'absolute' ? formatTimestamp(timestamp) : eventOffset(timestamp)
}
</script>

<template>
  <!-- Toolbar: icon controls | filter chips | time toggle -->
  <div class="mb-4 flex items-center gap-3">
    <!-- Structural controls (icon-only) -->
    <div class="flex items-center gap-1">
      <button
        class="inline-flex items-center justify-center rounded-md border border-border p-1.5 transition-colors"
        :class="groupByStep ? 'bg-card text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'"
        :title="groupByStep ? 'Ungroup events' : 'Group by step'"
        @click="groupByStep = !groupByStep"
      >
        <Layers class="h-3.5 w-3.5" />
      </button>
      <button
        class="inline-flex items-center justify-center rounded-md border border-border p-1.5 transition-colors"
        :class="allExpanded ? 'bg-card text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'"
        :title="allExpanded ? 'Collapse all' : 'Expand all'"
        @click="allExpanded ? collapseAll() : expandAll()"
      >
        <ChevronsDownUp v-if="allExpanded" class="h-3.5 w-3.5" />
        <ChevronsUpDown v-else class="h-3.5 w-3.5" />
      </button>
    </div>
    <!-- Filter chips -->
    <div class="flex flex-wrap items-center gap-1.5 rounded-lg bg-muted/50 p-1.5">
      <button
        v-for="t in eventTypes"
        :key="t"
        class="rounded-md px-2.5 py-1 text-xs font-mono transition-colors"
        :class="eventTypeFilter.has(t) ? 'bg-card text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'"
        @click="eventTypeFilter.toggle(t)"
      >
        {{ t }}
      </button>
      <span class="text-[10px] text-muted-foreground whitespace-nowrap tabular-nums">
        {{ filteredEvents.length }}<template v-if="eventTypeFilter.items.value.size > 0"> / {{ runStore.events.length }}</template>
      </span>
      <button
        v-if="eventTypeFilter.items.value.size > 0"
        class="rounded px-1.5 py-0.5 text-[10px] text-muted-foreground hover:text-foreground transition-colors"
        @click="eventTypeFilter.clear()"
      >
        clear
      </button>
    </div>
    <!-- Time mode toggle -->
    <div class="ml-auto flex items-center gap-0.5 rounded-md border border-border p-0.5">
      <button
        class="inline-flex items-center gap-1 rounded px-2 py-0.5 text-[11px] font-medium transition-colors"
        :class="timeMode === 'absolute' ? 'bg-accent text-foreground' : 'text-muted-foreground hover:text-foreground'"
        @click="timeMode = 'absolute'"
      >
        <Clock class="h-3 w-3" />
        Abs
      </button>
      <button
        class="rounded px-2 py-0.5 text-[11px] font-medium transition-colors"
        :class="timeMode === 'relative' ? 'bg-accent text-foreground' : 'text-muted-foreground hover:text-foreground'"
        @click="timeMode = 'relative'"
      >
        Rel
      </button>
    </div>
  </div>

  <!-- Flat event list -->
  <div v-if="!groupByStep" class="divide-y divide-border overflow-hidden rounded-lg border border-border">
    <EventRow
      v-for="event in filteredEvents"
      :key="event.seq"
      :event="event"
      :expanded="expandedEvents.has(event.seq)"
      :formatted-time="formatEventTime(event.timestamp)"
      @toggle="toggleEvent"
    />
    <div v-if="filteredEvents.length === 0" class="px-4 py-8 text-center text-sm text-muted-foreground">
      No events found
    </div>
  </div>

  <!-- Grouped event list -->
  <div v-else class="space-y-2">
    <div v-for="group in groupedEvents" :key="group.name" class="overflow-hidden rounded-lg border border-border">
      <button
        class="flex w-full items-center gap-3 px-4 py-2.5 text-left text-sm font-medium transition-colors hover:bg-accent/30"
        @click="expandedGroups.toggle(group.name)"
      >
        <ChevronRight
          class="h-4 w-4 text-muted-foreground transition-transform"
          :class="{ 'rotate-90': expandedGroups.has(group.name) }"
        />
        <span class="font-mono text-xs">{{ group.name }}</span>
        <Badge variant="muted">{{ group.events.length }}</Badge>
      </button>
      <div v-if="expandedGroups.has(group.name)" class="divide-y divide-border border-t border-border">
        <EventRow
          v-for="event in group.events"
          :key="event.seq"
          :event="event"
          :expanded="expandedEvents.has(event.seq)"
          :formatted-time="formatEventTime(event.timestamp)"
          @toggle="toggleEvent"
        />
      </div>
    </div>
    <div v-if="groupedEvents.length === 0" class="rounded-lg border border-border px-4 py-8 text-center text-sm text-muted-foreground">
      No events found
    </div>
  </div>
</template>
