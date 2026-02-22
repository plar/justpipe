<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { Factory, Search } from 'lucide-vue-next'
import { useCommandPalette } from '@/composables/useCommandPalette'
import { useHealth } from '@/composables/useHealth'
import { modKey } from '@/lib/platform'

const route = useRoute()
const { show: openSearch } = useCommandPalette()
const { status: healthStatus, lastSeenAt } = useHealth()

const healthLabel = computed(() => {
  if (healthStatus.value === 'online') return 'Online'
  if (healthStatus.value === 'checking') return 'Connecting...'
  if (!lastSeenAt.value) return 'Offline'
  const ago = Math.floor((Date.now() - new Date(lastSeenAt.value).getTime()) / 1000)
  if (ago < 60) return `Offline ${ago}s`
  if (ago < 3600) return `Offline ${Math.floor(ago / 60)}m`
  return `Offline ${Math.floor(ago / 3600)}h`
})

const navItems = [
  { to: '/', label: 'Pipelines', icon: Factory },
]
</script>

<template>
  <header class="border-b border-border bg-card/80 backdrop-blur-sm">
    <div class="mx-auto flex h-14 max-w-7xl items-center gap-6 px-6">
      <!-- Logo -->
      <RouterLink to="/" class="flex items-center gap-2.5 text-foreground">
        <div class="flex h-8 w-8 items-center justify-center rounded-md bg-primary/15">
          <svg class="h-4 w-4 text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4 12h4m4 0h4m4 0h-1" />
            <circle cx="6" cy="12" r="2" />
            <circle cx="14" cy="12" r="2" />
            <path d="M10 12l-2-4m0 8l2-4m4 0l2-4m0 8l-2-4" />
          </svg>
        </div>
        <span class="text-lg font-semibold tracking-tight">justpipe</span>
      </RouterLink>

      <!-- Nav -->
      <nav class="flex items-center gap-1">
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="flex items-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium transition-colors"
          :class="
            route.path === item.to || (item.to !== '/' && route.path.startsWith(item.to))
              ? 'bg-accent text-accent-foreground'
              : 'text-muted-foreground hover:text-foreground hover:bg-accent/50'
          "
        >
          <component :is="item.icon" class="h-4 w-4" />
          {{ item.label }}
        </RouterLink>
      </nav>

      <div class="flex-1" />

      <!-- Search trigger -->
      <button
        class="flex items-center gap-2 rounded-md border border-border bg-muted/50 px-3 py-1.5 text-sm text-muted-foreground transition-colors hover:bg-accent/50 hover:text-foreground"
        @click="openSearch()"
      >
        <Search class="h-3.5 w-3.5" />
        <span class="hidden sm:inline">Search</span>
        <kbd class="hidden rounded border border-border bg-background px-1.5 py-px text-[10px] font-medium sm:inline">
          {{ modKey }}K
        </kbd>
      </button>

      <!-- Health indicator -->
      <div class="flex items-center gap-2 text-xs text-muted-foreground">
        <span
          class="inline-block h-2 w-2 rounded-full"
          :class="{
            'bg-success pulse-glow': healthStatus === 'online',
            'bg-warning animate-pulse': healthStatus === 'checking',
            'bg-destructive': healthStatus === 'offline',
          }"
        />
        {{ healthLabel }}
      </div>
    </div>
  </header>
</template>
