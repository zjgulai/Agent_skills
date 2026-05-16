<script setup lang="ts">
import { computed } from 'vue'
import type { Domain, Skill } from '../types'
import SkillCard from './SkillCard.vue'

const props = defineProps<{ domain: Domain; skills: Skill[] }>()
defineEmits<{ select: [skill: Skill] }>()

const domainColor = computed(() => {
  const map: Record<string, string> = {
    meta: 'var(--domain-meta)',
    closeout: 'var(--domain-closeout)',
    desktop: 'var(--domain-desktop)',
    founder: 'var(--domain-founder)',
    ip: 'var(--domain-ip)',
    tooling: 'var(--domain-tooling)',
    uncategorized: 'var(--domain-uncategorized)',
  }
  return map[props.domain.id] || 'var(--domain-uncategorized)'
})
</script>

<template>
  <section class="domain-section">
    <header class="domain-header" :style="{ '--accent': domainColor } as any">
      <span class="dot"></span>
      <h3>{{ domain.label }}</h3>
      <span class="count">{{ skills.length }} {{ skills.length === 1 ? 'skill' : 'skills' }}</span>
    </header>
    <div class="cards-grid">
      <SkillCard
        v-for="s in skills"
        :key="s.name"
        :skill="s"
        :accent="domainColor"
        @click="$emit('select', s)"
      />
    </div>
  </section>
</template>
