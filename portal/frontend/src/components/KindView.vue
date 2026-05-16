<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { fetchHooks, fetchMcps } from '../api'
import type { HookItem, HooksData, McpItem, McpsData } from '../types'

const tab = defineProps<{ kind: 'hook' | 'mcp' }>()

const loading = ref(true)
const errorMsg = ref('')
const data = ref<HooksData | McpsData | null>(null)
const filter = ref('')
const activeName = ref<string | null>(null)

async function load() {
  loading.value = true
  errorMsg.value = ''
  try {
    data.value = tab.kind === 'hook' ? await fetchHooks() : await fetchMcps()
  } catch (e: any) {
    errorMsg.value = String(e?.message || e)
  } finally {
    loading.value = false
  }
}

watch(() => tab.kind, load)
onMounted(load)

function isHookItem(it: HookItem | McpItem): it is HookItem {
  return tab.kind === 'hook'
}

const filtered = computed(() => {
  if (!data.value) return []
  const q = filter.value.trim().toLowerCase()
  return data.value.items.filter(it => {
    if (!q) return true
    if (it.name.toLowerCase().includes(q)) return true
    if (it.description.toLowerCase().includes(q)) return true
    if (it.triggers.some(t => t.toLowerCase().includes(q))) return true
    return false
  })
})

const activeItem = computed(() => {
  if (!activeName.value || !data.value) return null
  return data.value.items.find(it => it.name === activeName.value) || null
})

function clientChip(value: string): string {
  switch (value) {
    case 'native': return '#2e7d32'
    case 'adapter': return '#e65100'
    case 'unsupported': return '#9e9e9e'
    default: return '#1976d2'
  }
}

function priorityClass(p: string): string {
  return p === 'P0' ? 'pri-p0' : p === 'P1' ? 'pri-p1' : 'pri-p2'
}
</script>

<template>
  <section class="kind-view">
    <div class="kind-header">
      <h2>{{ tab.kind === 'hook' ? 'Hooks' : 'MCPs' }}</h2>
      <span v-if="data" class="hint">{{ data.count }} registered · {{ data.repo }}</span>
    </div>

    <div v-if="loading" class="empty">loading…</div>
    <div v-else-if="errorMsg" class="callout callout-error">⚠ {{ errorMsg }}</div>

    <template v-else-if="data">
      <div class="kind-toolbar">
        <input
          type="search"
          :value="filter"
          @input="filter = ($event.target as HTMLInputElement).value"
          :placeholder="`search ${tab.kind === 'hook' ? 'hooks' : 'mcps'}…`"
        />
        <span class="hint">{{ filtered.length }} / {{ data.count }} shown</span>
      </div>

      <div class="kind-grid">
        <div
          v-for="it in filtered"
          :key="it.name"
          class="kind-card"
          :class="{ active: activeName === it.name }"
          @click="activeName = (activeName === it.name ? null : it.name)"
        >
          <div class="kind-card-head">
            <span class="kind-card-name">{{ it.name }}</span>
            <span class="kind-card-pri" :class="priorityClass(it.priority)">{{ it.priority }}</span>
          </div>
          <p class="kind-card-desc">{{ it.description }}</p>
          <div class="kind-card-tags">
            <span class="kind-tag" v-if="isHookItem(it)">⚡ {{ it.hook_events.join(', ') }}</span>
            <span class="kind-tag" v-if="!isHookItem(it)">▶ {{ it.mcp_command.slice(0, 2).join(' ') }}…</span>
            <span class="kind-tag domain-{{ it.domain }}">{{ it.domain }}</span>
          </div>
          <div class="kind-card-clients">
            <span
              v-for="(v, c) in it.compatibility"
              :key="c"
              class="client-chip"
              :style="{ background: clientChip(v) }"
              :title="`${c}: ${v}`"
            >{{ c }}</span>
          </div>
        </div>
      </div>

      <div v-if="!filtered.length" class="empty">
        <div class="big">∅</div>
        没有匹配的 {{ tab.kind }}
      </div>

      <aside v-if="activeItem" class="kind-detail" @click.self="activeName = null">
        <div class="kind-detail-card">
          <header>
            <h3>{{ activeItem.name }} <small>v{{ activeItem.version }}</small></h3>
            <button class="btn btn-ghost" @click="activeName = null">✕</button>
          </header>
          <p>{{ activeItem.description }}</p>

          <h4>Compatibility</h4>
          <table class="kind-table">
            <tr v-for="(v, c) in activeItem.compatibility" :key="c">
              <td><code>{{ c }}</code></td>
              <td><span class="client-chip" :style="{ background: clientChip(v) }">{{ v }}</span></td>
            </tr>
          </table>

          <template v-if="isHookItem(activeItem)">
            <h4>Events / Matchers</h4>
            <p>events: <code>{{ activeItem.hook_events.join(', ') }}</code></p>
            <p v-if="activeItem.matchers.length">matchers: <code>{{ activeItem.matchers.join(', ') }}</code></p>
          </template>

          <template v-if="!isHookItem(activeItem)">
            <h4>Launch command</h4>
            <pre class="kind-code">{{ activeItem.mcp_command.join(' ') }}</pre>
            <h4>Environment</h4>
            <table class="kind-table">
              <tr v-for="(ok, k) in activeItem.env_satisfied" :key="k">
                <td><code>{{ k }}</code></td>
                <td>{{ ok ? '✓ set' : '✗ NOT set' }}</td>
              </tr>
              <tr v-if="!Object.keys(activeItem.env_satisfied).length"><td colspan="2"><em>(no env required)</em></td></tr>
            </table>
            <h4>Binaries</h4>
            <table class="kind-table">
              <tr v-for="(ok, k) in activeItem.binaries_satisfied" :key="k">
                <td><code>{{ k }}</code></td>
                <td>{{ ok ? '✓ on PATH' : '✗ MISSING' }}</td>
              </tr>
            </table>
          </template>

          <h4 v-if="activeItem.triggers.length">Triggers</h4>
          <p v-if="activeItem.triggers.length">
            <span v-for="t in activeItem.triggers" :key="t" class="kind-trigger">{{ t }}</span>
          </p>
        </div>
      </aside>
    </template>
  </section>
</template>

<style scoped>
.kind-view { padding: 0 0 4rem; }
.kind-header { display: flex; align-items: baseline; gap: 1rem; margin: 1.5rem 0 0.75rem; }
.kind-header h2 { margin: 0; }
.hint { color: #666; font-size: 0.85rem; }

.kind-toolbar { display: flex; gap: 1rem; align-items: center; margin-bottom: 1rem; }
.kind-toolbar input { flex: 0 0 360px; padding: 0.5rem 0.75rem; border: 1px solid #ddd; border-radius: 6px; }

.kind-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 1rem; }
.kind-card { background: #fff; border: 1px solid #e5e5e5; border-radius: 10px; padding: 1rem; cursor: pointer; transition: all 0.15s; }
.kind-card:hover { border-color: #1976d2; box-shadow: 0 2px 8px rgba(25, 118, 210, 0.1); }
.kind-card.active { border-color: #1976d2; background: #f5faff; }
.kind-card-head { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 0.5rem; }
.kind-card-name { font-weight: 600; font-family: ui-monospace, SFMono-Regular, monospace; }
.kind-card-pri { font-size: 0.75rem; padding: 2px 8px; border-radius: 10px; color: #fff; }
.pri-p0 { background: #d32f2f; }
.pri-p1 { background: #f57c00; }
.pri-p2 { background: #757575; }
.kind-card-desc { font-size: 0.85rem; color: #444; margin: 0 0 0.75rem; line-height: 1.4; max-height: 4em; overflow: hidden; text-overflow: ellipsis; }
.kind-card-tags { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-bottom: 0.5rem; }
.kind-tag { font-size: 0.72rem; padding: 2px 8px; background: #f0f0f0; border-radius: 4px; font-family: ui-monospace, SFMono-Regular, monospace; }
.kind-card-clients { display: flex; gap: 4px; }
.client-chip { font-size: 0.7rem; color: #fff; padding: 2px 8px; border-radius: 10px; }

.kind-detail { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; justify-content: flex-end; z-index: 100; }
.kind-detail-card { background: #fff; width: 540px; max-width: 100%; height: 100%; padding: 1.5rem; overflow-y: auto; }
.kind-detail-card header { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 1rem; }
.kind-detail-card h3 { margin: 0; font-family: ui-monospace, SFMono-Regular, monospace; }
.kind-detail-card h3 small { color: #888; font-weight: 400; font-size: 0.85rem; }
.kind-detail-card h4 { margin: 1.25rem 0 0.5rem; font-size: 0.85rem; text-transform: uppercase; color: #666; letter-spacing: 0.05em; }
.kind-table { width: 100%; border-collapse: collapse; }
.kind-table td { padding: 0.4rem 0; border-bottom: 1px solid #f0f0f0; font-size: 0.85rem; }
.kind-table td:first-child { width: 40%; }
.kind-code { background: #1e1e1e; color: #d4d4d4; padding: 0.75rem; border-radius: 6px; font-size: 0.78rem; overflow-x: auto; }
.kind-trigger { display: inline-block; font-size: 0.75rem; background: #e3f2fd; color: #1976d2; padding: 2px 8px; border-radius: 4px; margin: 2px; }
.btn-ghost { background: transparent; border: 1px solid #ddd; padding: 4px 10px; border-radius: 6px; cursor: pointer; }
.empty { text-align: center; padding: 3rem; color: #888; }
.empty .big { font-size: 3rem; margin-bottom: 0.5rem; }
.callout { padding: 0.75rem 1rem; border-radius: 6px; margin: 1rem 0; }
.callout-error { background: #ffebee; color: #b71c1c; border: 1px solid #ffcdd2; }
</style>
