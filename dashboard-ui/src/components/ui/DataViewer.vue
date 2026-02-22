<script setup lang="ts">
import { ref, computed } from 'vue'
import JsonViewer from '@/components/ui/JsonViewer.vue'
import MetaViewer from '@/components/ui/MetaViewer.vue'
import ViewModeToggle from '@/components/ui/ViewModeToggle.vue'
import { ChevronRight } from 'lucide-vue-next'
import { useCopyJson } from '@/composables/useCopyJson'
import { useSetToggle } from '@/composables/useSetToggle'
import { formatEntry, type DisplayEntry } from '@/lib/utils'

const props = withDefaults(defineProps<{
  data: Record<string, unknown>
  maxHeight?: string
  depth?: number
}>(), {
  maxHeight: '400px',
  depth: 0,
})

const { copyLabel, copy } = useCopyJson()
const viewMode = ref<'smart' | 'raw'>('smart')
const expandedSections = useSetToggle()
const expandedTexts = useSetToggle()
const TEXT_THRESHOLD = 120

function isLongText(value: string): boolean {
  return value.length > TEXT_THRESHOLD || value.includes('\n')
}

function truncateText(value: string): string {
  const firstLine = value.split('\n')[0]!
  if (firstLine.length > TEXT_THRESHOLD) return firstLine.slice(0, TEXT_THRESHOLD) + '...'
  return firstLine + '...'
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes}b`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}kb`
  return `${(bytes / (1024 * 1024)).toFixed(1)}mb`
}

// Classify entries — skip 'meta' only at root level (depth 0)
const scalarEntries = computed<DisplayEntry[]>(() => {
  if (!props.data || typeof props.data !== 'object') return []
  const entries: DisplayEntry[] = []
  for (const [k, v] of Object.entries(props.data)) {
    if (props.depth === 0 && k === 'meta') continue
    if (v === null) {
      entries.push({ key: k, value: 'null' })
    } else if (Array.isArray(v) && v.length === 0) {
      entries.push({ key: k, value: '[]' })
    } else if (typeof v !== 'object') {
      entries.push(formatEntry(k, v))
    }
  }
  return entries
})

const hasMeta = computed(() => {
  if (props.depth > 0) return false
  const meta = props.data?.meta
  return meta !== null && meta !== undefined && typeof meta === 'object' && !Array.isArray(meta)
})

const metaData = computed(() => props.data?.meta as Record<string, unknown>)

const objectEntries = computed<Array<{ key: string; value: unknown }>>(() => {
  if (!props.data || typeof props.data !== 'object') return []
  const entries: Array<{ key: string; value: unknown }> = []
  for (const [k, v] of Object.entries(props.data)) {
    if (props.depth === 0 && k === 'meta') continue
    if (v !== null && typeof v === 'object') {
      if (Array.isArray(v) && v.length === 0) continue // handled in scalarEntries
      entries.push({ key: k, value: v })
    }
  }
  return entries
})

/** Convert array to indexed record for smart rendering. */
function toIndexedRecord(arr: unknown[]): Record<string, unknown> {
  const record: Record<string, unknown> = {}
  for (let i = 0; i < arr.length; i++) record[String(i)] = arr[i]
  return record
}

const isEmpty = computed(() =>
  scalarEntries.value.length === 0 &&
  !hasMeta.value &&
  objectEntries.value.length === 0
)

function objectSummary(value: unknown): string {
  if (Array.isArray(value)) return `[${value.length}]`
  if (value && typeof value === 'object') return `{${Object.keys(value).length}}`
  return ''
}

function copyData() {
  copy(props.data, 'Data')
}
</script>

<template>
  <div>
    <!-- Header: Smart/Raw toggle + Copy (root only) -->
    <ViewModeToggle
      v-if="depth === 0"
      v-model="viewMode"
      :copy-label="copyLabel"
      class="mb-2"
      @copy="copyData"
    />

    <!-- Smart view -->
    <div v-if="viewMode === 'smart'"
      :class="depth === 0 ? 'rounded-lg border border-border bg-card' : ''"
      :style="depth === 0 ? { maxHeight, minHeight: '100px', overflow: 'auto', resize: 'vertical' } : {}"
    >
      <!-- Scalar key-value rows -->
      <div
        v-for="entry in scalarEntries"
        :key="'s-' + entry.key"
        class="flex items-start gap-4 border-b border-border px-4 py-2.5 last:border-0"
      >
        <span class="w-40 shrink-0 pt-0.5 font-mono text-xs text-muted-foreground">{{ entry.key }}</span>
        <div class="min-w-0">
          <template v-if="isLongText(entry.value) && !expandedTexts.has(entry.key)">
            <span class="font-mono text-xs text-foreground">{{ truncateText(entry.value) }}</span>
            <button class="ml-1 text-[10px] text-muted-foreground hover:text-foreground" @click.stop="expandedTexts.toggle(entry.key)">show more ({{ formatSize(entry.value.length) }})</button>
          </template>
          <template v-else>
            <span
              class="font-mono text-xs whitespace-pre-wrap break-all"
              :class="entry.value === 'null' ? 'text-muted-foreground/50 italic' : 'text-foreground'"
            >{{ entry.value }}</span>
            <button v-if="isLongText(entry.value)" class="ml-1 text-[10px] text-muted-foreground hover:text-foreground" @click.stop="expandedTexts.toggle(entry.key)">show less</button>
          </template>
          <div v-if="entry.subtitle" class="mt-0.5 font-mono text-[10px] text-muted-foreground/60">{{ entry.subtitle }}</div>
        </div>
      </div>

      <!-- Meta section (collapsible, delegates to MetaViewer) — root only -->
      <div v-if="hasMeta" class="border-b border-border last:border-0">
        <button
          class="flex w-full items-center gap-2 px-4 py-2.5 text-left transition-colors hover:bg-accent/30"
          @click="expandedSections.toggle('meta')"
        >
          <ChevronRight
            class="h-3.5 w-3.5 text-muted-foreground transition-transform"
            :class="{ 'rotate-90': expandedSections.has('meta') }"
          />
          <span class="font-mono text-xs text-muted-foreground">meta</span>
        </button>
        <div v-if="expandedSections.has('meta')" class="px-4 pb-3">
          <MetaViewer :meta="metaData" :collapsible="false" />
        </div>
      </div>

      <!-- Object/array sections (collapsible) -->
      <div
        v-for="entry in objectEntries"
        :key="'o-' + entry.key"
        class="border-b border-border last:border-0"
      >
        <button
          class="flex w-full items-center gap-2 px-4 py-2.5 text-left transition-colors hover:bg-accent/30"
          @click="expandedSections.toggle(entry.key)"
        >
          <ChevronRight
            class="h-3.5 w-3.5 text-muted-foreground transition-transform"
            :class="{ 'rotate-90': expandedSections.has(entry.key) }"
          />
          <span class="font-mono text-xs text-muted-foreground">{{ entry.key }}</span>
          <span class="text-[10px] text-muted-foreground/50">
            {{ objectSummary(entry.value) }}
          </span>
        </button>
        <div v-if="expandedSections.has(entry.key)" class="pb-3 pl-4">
          <!-- Arrays: convert to indexed record and recurse -->
          <DataViewer v-if="Array.isArray(entry.value)" :data="toIndexedRecord(entry.value as unknown[])" :depth="depth + 1" />
          <!-- Objects: recurse with DataViewer -->
          <DataViewer v-else :data="(entry.value as Record<string, unknown>)" :depth="depth + 1" />
        </div>
      </div>

      <!-- Empty state -->
      <div v-if="isEmpty" class="px-4 py-3 text-xs text-muted-foreground">
        No data entries
      </div>
    </div>

    <!-- Raw view (root only) -->
    <div v-if="viewMode === 'raw' && depth === 0"
      :style="{ maxHeight, minHeight: '100px', overflow: 'auto', resize: 'vertical' }"
    >
      <JsonViewer :data="data" max-height="none" />
    </div>
  </div>
</template>
