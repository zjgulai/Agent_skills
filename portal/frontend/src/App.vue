<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { fetchSkills, refreshIndex } from './api'
import type { Skill, SkillsData } from './types'
import TopBar from './components/TopBar.vue'
import DomainSection from './components/DomainSection.vue'
import GraphView from './components/GraphView.vue'
import SkillDetail from './components/SkillDetail.vue'
import InstallDialog from './components/InstallDialog.vue'
import ToastList from './components/ToastList.vue'

const data = ref<SkillsData | null>(null)
const loading = ref(true)
const errorMsg = ref('')
const query = ref('')
const showInstall = ref(false)
const activeSkill = ref<Skill | null>(null)
const toasts = ref<{ id: number; kind: 'info' | 'success' | 'error'; text: string }[]>([])
let toastCounter = 0

async function load() {
  loading.value = true
  errorMsg.value = ''
  try {
    data.value = await fetchSkills()
  } catch (e: any) {
    errorMsg.value = String(e?.message || e)
  } finally {
    loading.value = false
  }
}

function pushToast(kind: 'info' | 'success' | 'error', text: string) {
  const id = ++toastCounter
  toasts.value.push({ id, kind, text })
  setTimeout(() => { toasts.value = toasts.value.filter(t => t.id !== id) }, 4000)
}

async function onInstalled(message: string) {
  pushToast('success', message)
  showInstall.value = false
  await load()
}
async function onUninstalled(message: string) {
  pushToast('success', message)
  activeSkill.value = null
  await load()
}
async function onRefresh() {
  try {
    const r = await refreshIndex()
    pushToast('success', `Re-indexed (${r.skill_count} skills).`)
    await load()
  } catch (e: any) {
    pushToast('error', `Refresh failed: ${e?.message}`)
  }
}

function relTime(iso: string): string {
  if (!iso) return ''
  const diff = Date.now() - new Date(iso).getTime()
  const s = Math.floor(diff / 1000)
  if (s < 60) return 'just now'
  const m = Math.floor(s / 60)
  if (m < 60) return `${m}m ago`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h}h ago`
  const d = Math.floor(h / 24)
  if (d < 30) return `${d}d ago`
  return new Date(iso).toLocaleDateString('zh-CN')
}

const filteredDomains = computed(() => {
  if (!data.value) return []
  const q = query.value.trim().toLowerCase()
  return data.value.domains.map(d => {
    const skills = d.skill_names
      .map(n => data.value!.skills.find(s => s.name === n))
      .filter((s): s is Skill => !!s)
      .filter(s => {
        if (!q) return true
        return (
          s.name.toLowerCase().includes(q) ||
          s.description.toLowerCase().includes(q) ||
          s.triggers.some(t => t.toLowerCase().includes(q))
        )
      })
    return { domain: d, skills }
  })
})

const totalAfterFilter = computed(() =>
  filteredDomains.value.reduce((acc, x) => acc + x.skills.length, 0),
)

onMounted(load)
</script>

<template>
  <div class="app-shell">
    <TopBar
      :generated-at="data?.generated_at || ''"
      :loading="loading"
      @refresh="onRefresh"
    />

    <section class="hero">
      <h1>Skills <span class="accent">Portal</span></h1>
      <p class="subtitle">
        本地 OpenCode skills 的能力地图与一键管理。按域查看技术能力，搜索/安装/卸载，全在一个页面。
      </p>
      <div class="actions">
        <div class="search-wrap">
          <span class="icon">⌕</span>
          <input
            type="search"
            :value="query"
            placeholder="搜索 name / description / 触发词..."
            @input="query = ($event.target as HTMLInputElement).value"
          />
        </div>
        <button class="btn btn-primary" @click="showInstall = true">+ 安装新 skill</button>
      </div>
    </section>

    <div v-if="errorMsg" class="callout callout-error">⚠ {{ errorMsg }}</div>

    <template v-if="data">
      <div class="stat-strip">
        <div class="stat"><span class="num">{{ data.skill_count }}</span> skills</div>
        <div class="stat">
          <span class="num">{{ data.domains.filter(d => d.skill_names.length).length }}</span> domains
        </div>
        <div class="grow"></div>
        <span>indexed {{ relTime(data.generated_at) }}</span>
      </div>

      <section class="graph-section">
        <div class="section-heading">
          <h2>Skills Graph</h2>
          <span class="hint">协作关系层 · 同色为同一域 · 实线 = 生命周期 · 虚线 = 增援</span>
        </div>
        <GraphView :mermaid-source="data.graph.mermaid_source" />
      </section>

      <section>
        <div class="section-heading">
          <h2>By Domain</h2>
          <span class="hint">{{ totalAfterFilter }} / {{ data.skill_count }} shown</span>
        </div>

        <template v-for="bucket in filteredDomains" :key="bucket.domain.id">
          <DomainSection
            v-if="bucket.skills.length > 0"
            :domain="bucket.domain"
            :skills="bucket.skills"
            @select="activeSkill = $event"
          />
        </template>

        <div v-if="query && totalAfterFilter === 0" class="empty">
          <div class="big">∅</div>
          没有匹配「<code>{{ query }}</code>」的 skill
        </div>
      </section>
    </template>

    <SkillDetail
      v-if="activeSkill"
      :skill="activeSkill"
      @close="activeSkill = null"
      @uninstalled="onUninstalled"
      @toast="(k, t) => pushToast(k, t)"
    />

    <InstallDialog
      v-if="showInstall"
      @close="showInstall = false"
      @installed="onInstalled"
      @toast="(k, t) => pushToast(k, t)"
    />

    <ToastList :toasts="toasts" />
  </div>
</template>
