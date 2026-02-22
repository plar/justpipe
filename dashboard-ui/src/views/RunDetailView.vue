<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useRunStore } from '@/stores/run'
import { useReplayStore } from '@/stores/replay'
import { formatDuration, formatTimestamp, shortId } from '@/lib/utils'
import { statusBadgeVariant } from '@/lib/view-helpers'
import { useKeyboard } from '@/composables/useKeyboard'
import { usePolling } from '@/composables/usePolling'
import { processInvocationEvents } from '@/lib/event-processor'
import { api } from '@/api/client'
import type { PipelineSummary } from '@/types'
import TabBar from '@/components/ui/TabBar.vue'
import StatusIndicator from '@/components/ui/StatusIndicator.vue'
import Badge from '@/components/ui/Badge.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorBanner from '@/components/ui/ErrorBanner.vue'
import WaterfallTimeline from '@/components/timeline/WaterfallTimeline.vue'
import ConcurrencyChart from '@/components/timeline/ConcurrencyChart.vue'
import FailureAutopsy from '@/components/inspector/FailureAutopsy.vue'
import StepInspector from '@/components/inspector/StepInspector.vue'
import DagErrorBoundary from '@/components/dag/DagErrorBoundary.vue'
import DagCanvasPixi from '@/components/dag/DagCanvasPixi.vue'
import DagLegend from '@/components/dag/DagLegend.vue'
import ReplayControls from '@/components/replay/ReplayControls.vue'
import ArtifactBrowser from '@/components/artifacts/ArtifactBrowser.vue'
import RunEventsTab from '@/components/run/RunEventsTab.vue'
import RunMetricsTab from '@/components/run/RunMetricsTab.vue'
import { useToast } from '@/composables/useToast'
import Breadcrumb from '@/components/ui/Breadcrumb.vue'
import MetaViewer from '@/components/ui/MetaViewer.vue'
import { ChevronRight, GitCompareArrows, Download } from 'lucide-vue-next'

const { toast } = useToast()
const route = useRoute()
const router = useRouter()
const runStore = useRunStore()
const replay = useReplayStore()

const runId = computed(() => route.params.id as string)
const activeTab = ref((route.query.tab as string) || 'timeline')
const selectedStepIndex = ref<number | null>(null)
const showArtifacts = ref(false)

// Auto-refresh for in-progress runs
const TERMINAL_STATUSES = new Set(['success', 'failed', 'timeout', 'cancelled', 'client_closed'])
const isTerminal = computed(() => {
  const status = runStore.run?.status
  return !status || TERMINAL_STATUSES.has(status)
})
const polling = usePolling(() => runStore.refreshRun(runId.value), 3000)

function startPolling() {
  if (!isTerminal.value) polling.start()
}

watch(isTerminal, (terminal) => {
  if (terminal) polling.stop()
})

// Replay state
const replayPipeline = ref<PipelineSummary | null>(null)
const replayLoading = ref(false)

const tabs = computed(() => [
  { key: 'timeline', label: 'Timeline' },
  { key: 'events', label: 'Events', count: runStore.events.length || null },
  { key: 'metrics', label: 'Metrics' },
  { key: 'replay', label: 'Replay' },
])

// Keyboard shortcuts
useKeyboard({
  tabKeys: ['timeline', 'events', 'metrics', 'replay'],
  onTab: (key) => { switchTab(key) },
  onEscape: () => { selectedStepIndex.value = null },
})

// Inspector data — index-based to handle duplicate step names
const inspectorOpen = computed(() => selectedStepIndex.value !== null)

const inspectorEvents = computed(() => {
  if (selectedStepIndex.value === null) return []
  const entry = runStore.timeline[selectedStepIndex.value]
  if (!entry) return []
  const invocationIdx = runStore.timeline
    .slice(0, selectedStepIndex.value)
    .filter((e) => e.step_name === entry.step_name).length
  return runStore.eventsForInvocation(entry.step_name, invocationIdx)
})

const inspectorStep = computed(() => processInvocationEvents(inspectorEvents.value))

function selectStep(index: number) {
  selectedStepIndex.value = selectedStepIndex.value === index ? null : index
}

function switchTab(tab: string) {
  activeTab.value = tab
  router.replace({ query: { ...route.query, tab } })
}

function goToCompare() {
  router.push({ path: '/compare', query: { run1: runId.value } })
}

async function exportRun() {
  try {
    const data = await api.exportRun(runId.value)
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `run-${runId.value.slice(0, 12)}.json`
    a.click()
    URL.revokeObjectURL(url)
    toast('Run exported', 'success')
  } catch (e) {
    toast(e instanceof Error ? e.message : 'Export failed', 'error')
  }
}

// Load replay data when switching to replay tab
async function loadReplayData() {
  if (!runStore.run || replayPipeline.value) return
  replayLoading.value = true
  try {
    replayPipeline.value = await api.getPipeline(runStore.run.pipeline_hash)
    replay.setEvents(runStore.events)
  } finally {
    replayLoading.value = false
  }
}

watch(activeTab, (tab) => {
  if (tab === 'replay') loadReplayData()
})

onMounted(async () => {
  await runStore.fetchRun(runId.value)
  startPolling()
})

watch(runId, async (newId) => {
  polling.stop()
  await runStore.fetchRun(newId)
  replayPipeline.value = null
  replay.reset()
  startPolling()
})

onBeforeUnmount(() => {
  replay.reset()
})
</script>

<template>
  <div>
    <LoadingState v-if="runStore.loading" />
    <ErrorBanner v-else-if="runStore.error" :message="runStore.error" />
    <template v-else-if="runStore.run">
      <!-- Header -->
      <div class="mb-6">
        <div class="flex items-center justify-between">
          <Breadcrumb :items="[
            { label: 'Pipelines', to: '/' },
            { label: runStore.run.pipeline_name, to: `/pipeline/${runStore.run.pipeline_hash}` },
            { label: shortId(runStore.run.run_id) },
          ]" />
          <div class="flex items-center gap-2">
            <button
              class="inline-flex items-center gap-1.5 rounded-md border border-border bg-card px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
              @click="exportRun"
            >
              <Download class="h-3.5 w-3.5" />
              Export JSON
            </button>
            <button
              class="inline-flex items-center gap-1.5 rounded-md border border-border bg-card px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
              @click="goToCompare"
            >
              <GitCompareArrows class="h-3.5 w-3.5" />
              Compare with...
            </button>
          </div>
        </div>

        <div class="mt-2 flex items-center gap-3">
          <StatusIndicator :status="runStore.run.status" size="lg" :pulse="runStore.run.status === 'success'" />
          <h1 class="font-mono text-xl font-semibold text-foreground">
            {{ shortId(runStore.run.run_id) }}
          </h1>
          <Badge :variant="statusBadgeVariant(runStore.run.status)">{{ runStore.run.status }}</Badge>
          <span v-if="!isTerminal" class="inline-flex items-center gap-1.5 text-xs text-emerald-500">
            <span class="relative flex h-2 w-2">
              <span class="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75"></span>
              <span class="relative inline-flex h-2 w-2 rounded-full bg-emerald-500"></span>
            </span>
            Live
          </span>
        </div>

        <div class="mt-2 flex items-center gap-6 text-sm text-muted-foreground">
          <span>Started: {{ formatTimestamp(runStore.run.start_time) }}</span>
          <span v-if="runStore.run.end_time">Ended: {{ formatTimestamp(runStore.run.end_time) }}</span>
          <span>Duration: <strong class="text-foreground">{{ formatDuration(runStore.run.duration_seconds) }}</strong></span>
          <span v-if="!isTerminal" class="text-xs text-muted-foreground/60">
            Updated {{ polling.secondsSinceRefresh.value }}s ago
          </span>
        </div>

        <!-- Collapsible Meta -->
        <MetaViewer
          v-if="runStore.run.run_meta && Object.keys(runStore.run.run_meta).length > 0"
          :meta="runStore.run.run_meta"
          collapsible
          class="mt-3"
        />
      </div>

      <!-- Failure Autopsy -->
      <FailureAutopsy
        v-if="runStore.run.status === 'failed'"
        :run="runStore.run"
        :steps="runStore.steps"
        :events="runStore.events"
      />

      <!-- Tabs -->
      <div class="mb-6">
        <TabBar :tabs="tabs" :active="activeTab" @select="switchTab" />
      </div>

      <!-- Timeline Tab -->
      <div v-if="activeTab === 'timeline'">
        <WaterfallTimeline
          :entries="runStore.timeline"
          :critical-path="runStore.criticalPath"
          :selected-index="selectedStepIndex"
          @select-step="selectStep"
        />
        <ConcurrencyChart
          :entries="runStore.timeline"
          :min-ms="runStore.timelineRange.min"
          :span-ms="runStore.timelineRange.span"
        />

        <!-- Collapsible Artifacts -->
        <div v-if="runStore.steps.some((s) => 'artifacts' in s)" class="mt-6">
          <button
            class="inline-flex items-center gap-1.5 rounded-md border border-border bg-card px-2.5 py-1 text-xs text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
            @click="showArtifacts = !showArtifacts"
          >
            <ChevronRight class="h-3.5 w-3.5 transition-transform" :class="{ 'rotate-90': showArtifacts }" />
            Artifacts
          </button>
          <div v-if="showArtifacts" class="mt-2">
            <ArtifactBrowser :steps="runStore.steps" />
          </div>
        </div>
      </div>

      <!-- Events Tab -->
      <RunEventsTab v-if="activeTab === 'events'" />

      <!-- Metrics Tab -->
      <div v-show="activeTab === 'metrics'">
        <RunMetricsTab />
      </div>

      <!-- Replay Tab -->
      <div v-if="activeTab === 'replay'">
        <LoadingState v-if="replayLoading" text="Loading pipeline topology..." />
        <div v-else-if="replayPipeline?.topology">
          <DagErrorBoundary>
            <DagCanvasPixi
              :topology="replayPipeline.topology"
              :visual-ast="replayPipeline.visual_ast"
              :replay-statuses="replay.activeSteps"
              :replay-time-ms="replay.currentTimeMs"
              :replay-step-timings="replay.stepTimings"
            >
              <template #legend>
                <DagLegend />
              </template>
            </DagCanvasPixi>
          </DagErrorBoundary>
          <ReplayControls />
        </div>
        <div v-else class="rounded-lg border border-border bg-card p-8 text-center text-sm text-muted-foreground">
          No topology data available for replay
        </div>
      </div>

      <!-- Step Inspector Sidebar -->
      <StepInspector
        :open="inspectorOpen"
        :step="inspectorStep"
        :events="inspectorEvents"
        @close="selectedStepIndex = null"
      />
    </template>
  </div>
</template>
