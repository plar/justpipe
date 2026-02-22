<script setup lang="ts">
import { ref, computed } from 'vue'
import Badge from '@/components/ui/Badge.vue'
import JsonViewer from '@/components/ui/JsonViewer.vue'
import ViewModeToggle from '@/components/ui/ViewModeToggle.vue'
import { ChevronRight } from 'lucide-vue-next'
import { useCopyJson } from '@/composables/useCopyJson'
import { formatScalar, formatEntry, type DisplayEntry } from '@/lib/utils'

const props = withDefaults(defineProps<{
  meta: Record<string, unknown>
  collapsible?: boolean
  defaultExpanded?: boolean
}>(), {
  collapsible: true,
  defaultExpanded: false,
})

const { copyLabel, copy } = useCopyJson()
const expanded = ref(props.defaultExpanded)
const viewMode = ref<'smart' | 'raw'>('smart')

// Known structured sections (step-level meta)
const STRUCTURED_KEYS = new Set(['tags', 'framework', 'metrics', 'counters', 'data'])

const metaTags = computed<string[]>(() => {
  const tags = props.meta?.tags
  return Array.isArray(tags) ? tags : []
})

function extractSection(key: string, formatter?: (k: string, v: unknown) => DisplayEntry): DisplayEntry[] {
  const section = props.meta?.[key]
  if (!section || typeof section !== 'object' || Array.isArray(section)) return []
  return Object.entries(section as Record<string, unknown>).map(([k, v]) =>
    formatter ? formatter(k, v) : { key: k, value: formatScalar(v) },
  )
}

const frameworkEntries = computed(() => extractSection('framework', formatEntry))

const countersEntries = computed(() => extractSection('counters'))

const metricsEntries = computed(() =>
  extractSection('metrics', (k, v) => ({
    key: k,
    value: Array.isArray(v) ? v.map(formatScalar).join(', ') : formatScalar(v),
  })),
)

const dataEntries = computed(() =>
  extractSection('data', (k, v) => ({
    key: k,
    value: typeof v === 'object' ? JSON.stringify(v) : formatScalar(v),
  })),
)

// Fallback: top-level keys not in structured categories (handles run-level meta)
const fallbackEntries = computed<DisplayEntry[]>(() => {
  if (!props.meta || typeof props.meta !== 'object') return []
  const entries: DisplayEntry[] = []
  for (const [k, v] of Object.entries(props.meta)) {
    if (STRUCTURED_KEYS.has(k)) continue
    if (v !== null && typeof v === 'object' && !Array.isArray(v)) {
      for (const [subKey, subVal] of Object.entries(v as Record<string, unknown>)) {
        entries.push(formatEntry(subKey, subVal))
      }
    } else {
      entries.push(formatEntry(k, v))
    }
  }
  return entries
})

/** Sections with a header row followed by key-value rows (metrics, counters). */
const namedSections = computed(() => [
  { label: 'Metrics', prefix: 'met', entries: metricsEntries.value },
  { label: 'Counters', prefix: 'cnt', entries: countersEntries.value },
].filter((s) => s.entries.length > 0))

const isEmpty = computed(() =>
  metaTags.value.length === 0 &&
  frameworkEntries.value.length === 0 &&
  namedSections.value.length === 0 &&
  dataEntries.value.length === 0 &&
  fallbackEntries.value.length === 0,
)

function statusClass(value: string): string {
  switch (value) {
    case 'success': return 'text-success'
    case 'failed': case 'error': return 'text-destructive'
    case 'running': return 'text-warning'
    default: return 'text-foreground'
  }
}

function copyMeta() {
  copy(props.meta, 'Meta')
}
</script>

<template>
  <div>
    <!-- Header -->
    <div class="flex items-center gap-2">
      <button
        v-if="collapsible"
        class="inline-flex items-center gap-1.5 rounded-md border border-border bg-card px-2.5 py-1 text-xs text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
        @click="expanded = !expanded"
      >
        <ChevronRight class="h-3.5 w-3.5 transition-transform" :class="{ 'rotate-90': expanded }" />
        Meta
      </button>
      <ViewModeToggle
        v-if="!collapsible || expanded"
        v-model="viewMode"
        :copy-label="copyLabel"
        @copy="copyMeta"
      />
    </div>

    <!-- Content (visible when expanded, or always when not collapsible) -->
    <template v-if="!collapsible || expanded">
      <!-- Smart view -->
      <div v-if="viewMode === 'smart'" class="mt-2 rounded-lg border border-border bg-card">
        <!-- Tags -->
        <div v-if="metaTags.length > 0" class="flex flex-wrap items-center gap-1.5 border-b border-border px-4 py-3">
          <span class="w-40 shrink-0 font-mono text-xs text-muted-foreground">tags</span>
          <Badge v-for="tag in metaTags" :key="tag" variant="muted">{{ tag }}</Badge>
        </div>

        <!-- Framework -->
        <template v-if="frameworkEntries.length > 0">
          <div class="border-b border-border bg-muted/30 px-4 py-1.5">
            <span class="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Framework</span>
          </div>
          <div
            v-for="entry in frameworkEntries"
            :key="'fw-' + entry.key"
            class="flex items-start gap-4 border-b border-border px-4 py-2.5 last:border-0"
          >
            <span class="w-40 shrink-0 pt-0.5 pl-2 font-mono text-xs text-muted-foreground">{{ entry.key }}</span>
            <div>
              <span
                class="font-mono text-xs"
                :class="entry.key === 'status' ? statusClass(entry.value) : 'text-foreground'"
              >{{ entry.value }}</span>
              <div v-if="entry.subtitle" class="mt-0.5 font-mono text-[10px] text-muted-foreground/60">{{ entry.subtitle }}</div>
            </div>
          </div>
        </template>

        <!-- Metrics / Counters -->
        <template v-for="section in namedSections" :key="section.label">
          <div class="border-b border-border bg-muted/30 px-4 py-1.5">
            <span class="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">{{ section.label }}</span>
          </div>
          <div
            v-for="entry in section.entries"
            :key="section.prefix + '-' + entry.key"
            class="flex items-start gap-4 border-b border-border px-4 py-2.5 last:border-0"
          >
            <span class="w-40 shrink-0 pt-0.5 pl-2 font-mono text-xs text-muted-foreground">{{ entry.key }}</span>
            <span class="font-mono text-xs text-foreground">{{ entry.value }}</span>
          </div>
        </template>

        <!-- Data entries -->
        <div
          v-for="entry in dataEntries"
          :key="'data-' + entry.key"
          class="flex items-start gap-4 border-b border-border px-4 py-2.5 last:border-0"
        >
          <span class="w-40 shrink-0 pt-0.5 font-mono text-xs text-muted-foreground">{{ entry.key }}</span>
          <span class="font-mono text-xs text-foreground">{{ entry.value }}</span>
        </div>

        <!-- Fallback entries (run-level or unstructured) -->
        <div
          v-for="entry in fallbackEntries"
          :key="'fb-' + entry.key"
          class="flex items-start gap-4 border-b border-border px-4 py-2.5 last:border-0"
        >
          <span class="w-40 shrink-0 pt-0.5 font-mono text-xs text-muted-foreground">{{ entry.key }}</span>
          <div>
            <span class="font-mono text-xs text-foreground">{{ entry.value }}</span>
            <div v-if="entry.subtitle" class="mt-0.5 font-mono text-[10px] text-muted-foreground/60">{{ entry.subtitle }}</div>
          </div>
        </div>

        <!-- Empty state -->
        <div v-if="isEmpty" class="px-4 py-3 text-xs text-muted-foreground">
          No meta entries
        </div>
      </div>

      <!-- Raw view -->
      <div v-if="viewMode === 'raw'" class="mt-2">
        <JsonViewer :data="meta" max-height="400px" />
      </div>
    </template>
  </div>
</template>
