<script setup lang="ts">
import { Clipboard } from 'lucide-vue-next'

defineProps<{
  modelValue: 'smart' | 'raw'
  copyLabel: string
}>()

defineEmits<{
  'update:modelValue': [value: 'smart' | 'raw']
  copy: []
}>()
</script>

<template>
  <div class="flex items-center gap-2">
    <div class="flex items-center gap-0.5 rounded-md border border-border p-0.5">
      <button
        class="rounded px-2 py-0.5 text-[11px] font-medium transition-colors"
        :class="modelValue === 'smart' ? 'bg-accent text-foreground' : 'text-muted-foreground hover:text-foreground'"
        @click="$emit('update:modelValue', 'smart')"
      >
        Smart
      </button>
      <button
        class="rounded px-2 py-0.5 text-[11px] font-medium transition-colors"
        :class="modelValue === 'raw' ? 'bg-accent text-foreground' : 'text-muted-foreground hover:text-foreground'"
        @click="$emit('update:modelValue', 'raw')"
      >
        Raw
      </button>
    </div>
    <button
      class="inline-flex items-center gap-1 rounded-md border border-border px-2 py-0.5 text-[11px] text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
      @click="$emit('copy')"
    >
      <Clipboard class="h-3 w-3" />
      {{ copyLabel }}
    </button>
  </div>
</template>
