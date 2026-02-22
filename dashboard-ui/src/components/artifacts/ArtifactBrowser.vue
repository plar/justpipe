<script setup lang="ts">
import { ref, computed } from 'vue'
import type { ProcessedStep } from '@/lib/event-processor'
import { statusBadgeVariant } from '@/lib/view-helpers'
import { useSetToggle } from '@/composables/useSetToggle'
import Badge from '@/components/ui/Badge.vue'
import StatusIndicator from '@/components/ui/StatusIndicator.vue'
import DataViewer from '@/components/ui/DataViewer.vue'

const props = defineProps<{
  steps: ProcessedStep[]
}>()

const filter = ref('')
const expandedSteps = useSetToggle()

const stepsWithPayloads = computed(() =>
  props.steps.filter((s) => s.inputPayload !== null || s.outputPayload !== null)
)

const filteredSteps = computed(() => {
  const q = filter.value.trim().toLowerCase()
  if (!q) return stepsWithPayloads.value
  return stepsWithPayloads.value.filter((s) => s.name.toLowerCase().includes(q))
})

</script>

<template>
  <div>
    <!-- Filter input -->
    <div class="mb-4">
      <input
        v-model="filter"
        type="text"
        placeholder="Filter by step name..."
        class="w-full rounded-md border border-border bg-card px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
      />
    </div>

    <!-- Empty state -->
    <div
      v-if="filteredSteps.length === 0"
      class="rounded-lg border border-border bg-card/50 py-10 text-center"
    >
      <p class="text-sm text-muted-foreground">
        {{ stepsWithPayloads.length === 0 ? 'No step payloads captured' : 'No steps match the filter' }}
      </p>
    </div>

    <!-- Step cards -->
    <div v-else class="space-y-3">
      <div
        v-for="step in filteredSteps"
        :key="step.name"
        class="rounded-lg border border-border bg-card"
      >
        <!-- Card header -->
        <button
          class="flex w-full items-center gap-3 px-4 py-3 text-left transition-colors hover:bg-muted/30"
          @click="expandedSteps.toggle(step.name)"
        >
          <!-- Expand/collapse chevron -->
          <svg
            class="h-4 w-4 shrink-0 text-muted-foreground transition-transform"
            :class="{ 'rotate-90': expandedSteps.has(step.name) }"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="2"
          >
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
          </svg>

          <StatusIndicator :status="step.status" size="sm" />

          <span class="font-mono text-sm font-medium text-foreground">{{ step.name }}</span>

          <Badge v-if="step.kind" variant="muted">{{ step.kind }}</Badge>
          <Badge :variant="statusBadgeVariant(step.status)">{{ step.status }}</Badge>

          <span class="flex-1" />
        </button>

        <!-- Expanded content -->
        <div v-if="expandedSteps.has(step.name)" class="border-t border-border px-4 py-4">
          <div class="space-y-4">
            <!-- Input section -->
            <div>
              <h4 class="mb-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
                Input
              </h4>
              <DataViewer v-if="step.inputPayload" :data="step.inputPayload" />
              <p v-else class="text-xs text-muted-foreground">No input payload captured</p>
            </div>

            <!-- Output section -->
            <div>
              <h4 class="mb-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
                Output
              </h4>
              <DataViewer v-if="step.outputPayload" :data="step.outputPayload" />
              <p v-else class="text-xs text-muted-foreground">No output payload captured</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
