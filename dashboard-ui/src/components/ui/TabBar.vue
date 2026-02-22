<script setup lang="ts">
defineProps<{
  tabs: Array<{ key: string; label: string; count?: number | null }>
  active: string
}>()

defineEmits<{
  select: [key: string]
}>()
</script>

<template>
  <div class="flex gap-1 rounded-lg bg-muted p-1">
    <button
      v-for="tab in tabs"
      :key="tab.key"
      class="rounded-md px-3 py-1.5 text-sm font-medium transition-colors"
      :class="
        active === tab.key
          ? 'bg-card text-foreground shadow-sm'
          : 'text-muted-foreground hover:text-foreground'
      "
      @click="$emit('select', tab.key)"
    >
      {{ tab.label }}
      <span
        v-if="tab.count != null"
        class="ml-1.5 rounded-full bg-muted px-1.5 py-px text-[10px] font-medium tabular-nums text-muted-foreground"
      >{{ tab.count }}</span>
    </button>
  </div>
</template>
