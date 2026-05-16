<script setup lang="ts">
defineProps<{
  generatedAt: string
  loading: boolean
}>()

defineEmits<{ refresh: [] }>()

function fmtTime(iso: string): string {
  if (!iso) return ''
  try {
    return new Date(iso).toLocaleTimeString('zh-CN', { hour12: false })
  } catch {
    return iso
  }
}
</script>

<template>
  <header class="brand-bar">
    <div class="logo">
      <span class="dot"></span>
      <span>skills-portal</span>
    </div>
    <div class="right">
      <span v-if="loading">loading...</span>
      <span v-else-if="generatedAt">indexed at {{ fmtTime(generatedAt) }}</span>
      <span class="sep"></span>
      <button class="btn btn-ghost btn-icon" title="重建索引" @click="$emit('refresh')">↻</button>
    </div>
  </header>
</template>
