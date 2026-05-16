<script setup lang="ts">
import type { Skill } from '../types'

defineProps<{
  skill: Skill
  accent: string
}>()

function fmtDate(iso: string): string {
  if (!iso) return ''
  try {
    const d = new Date(iso)
    const m = String(d.getMonth() + 1).padStart(2, '0')
    const dd = String(d.getDate()).padStart(2, '0')
    return `${d.getFullYear()}.${m}.${dd}`
  } catch {
    return iso
  }
}
</script>

<template>
  <article class="skill-card" :style="{ '--accent': accent } as any">
    <div class="head">
      <span class="dot"></span>
      <span class="name">{{ skill.name }}</span>
    </div>

    <p class="desc">{{ skill.description }}</p>

    <div v-if="skill.triggers.length" class="triggers">
      <span v-for="t in skill.triggers.slice(0, 3)" :key="t" class="chip">{{ t }}</span>
      <span v-if="skill.triggers.length > 3" class="chip more">+{{ skill.triggers.length - 3 }}</span>
    </div>

    <div class="meta-row">
      <div class="left">
        <span>{{ skill.resources.length ? `${skill.resources.length} resources` : 'single file' }}</span>
        <span>·</span>
        <span>{{ fmtDate(skill.installed_at) }}</span>
      </div>
      <span class="arrow">→</span>
    </div>
  </article>
</template>
