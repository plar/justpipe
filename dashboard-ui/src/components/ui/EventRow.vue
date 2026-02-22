<script setup lang="ts">
import { ChevronRight } from 'lucide-vue-next'
import Badge from '@/components/ui/Badge.vue'
import DataViewer from '@/components/ui/DataViewer.vue'
import type { PipelineEvent } from '@/types'

defineProps<{
  event: PipelineEvent
  expanded: boolean
  formattedTime: string
}>()

defineEmits<{
  toggle: [seq: number]
}>()
</script>

<template>
  <div class="text-sm">
    <button
      class="flex w-full items-center gap-3 px-4 py-2.5 text-left transition-colors hover:bg-accent/30"
      @click="$emit('toggle', event.seq)"
    >
      <ChevronRight
        class="h-3.5 w-3.5 shrink-0 text-muted-foreground transition-transform"
        :class="{ 'rotate-90': expanded }"
      />
      <span class="w-7 text-right font-mono text-xs text-muted-foreground tabular-nums">{{ event.seq }}</span>
      <Badge variant="muted">{{ event.event_type }}</Badge>
      <span class="flex-1 truncate font-mono text-xs text-muted-foreground">
        {{ event.step_name }}
      </span>
      <span class="text-xs text-muted-foreground tabular-nums">{{ formattedTime }}</span>
    </button>
    <div
      v-if="expanded"
      class="border-t border-border bg-muted/30 px-4 py-3"
    >
      <DataViewer :data="(event.data as Record<string, unknown>)" max-height="400px" />
    </div>
  </div>
</template>
