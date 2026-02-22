<script setup lang="ts">
import { ChevronRight } from 'lucide-vue-next'

defineProps<{
  items: Array<{ label: string; to?: string }>
}>()
</script>

<template>
  <nav class="flex items-center gap-1 text-sm">
    <template v-for="(item, i) in items" :key="i">
      <ChevronRight v-if="i > 0" class="h-3.5 w-3.5 text-muted-foreground/50" />
      <RouterLink
        v-if="item.to"
        :to="item.to"
        class="text-muted-foreground transition-colors hover:text-foreground"
      >
        {{ item.label }}
      </RouterLink>
      <span v-else class="text-foreground">{{ item.label }}</span>
    </template>
  </nav>
</template>
