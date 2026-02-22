<script setup lang="ts">
defineProps<{
  label: string
}>()
</script>

<template>
  <h4 class="border-l-2 border-primary/40 pl-3 mb-3 text-sm font-medium text-foreground">{{ label }}</h4>
</template>
