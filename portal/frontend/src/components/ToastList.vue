<script setup lang="ts">
defineProps<{
  toasts: { id: number; kind: 'info' | 'success' | 'error'; text: string }[]
}>()
</script>

<template>
  <div class="toast-stack">
    <div v-for="t in toasts" :key="t.id" :class="['toast', t.kind]">
      <span>{{ t.text }}</span>
    </div>
  </div>
</template>
