<script setup lang="ts">
import { ref } from 'vue'
import AppLayout from './components/layout/AppLayout.vue'
import ToastContainer from './components/ui/ToastContainer.vue'
import CommandPalette from './components/ui/CommandPalette.vue'
import ShortcutOverlay from './components/ui/ShortcutOverlay.vue'
import { useCommandPalette } from './composables/useCommandPalette'

const { open: commandPaletteOpen } = useCommandPalette()
const shortcutOverlayOpen = ref(false)
</script>

<template>
  <AppLayout>
    <router-view v-slot="{ Component }">
      <transition name="route" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
  </AppLayout>
  <ToastContainer />
  <CommandPalette v-model:open="commandPaletteOpen" />
  <ShortcutOverlay v-model:open="shortcutOverlayOpen" />
</template>
