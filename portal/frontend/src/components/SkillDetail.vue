<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { marked } from 'marked'
import { fetchSkillMarkdown, uninstallSkill } from '../api'
import type { Skill } from '../types'

const props = defineProps<{ skill: Skill }>()
const emit = defineEmits<{
  close: []
  uninstalled: [message: string]
  toast: [kind: 'info' | 'success' | 'error', text: string]
}>()

const renderedHtml = ref('')
const loading = ref(true)
const errorMsg = ref('')
const confirming = ref(false)

onMounted(async () => {
  try {
    const md = await fetchSkillMarkdown(props.skill.name)
    const stripped = md.replace(/^---\n[\s\S]*?\n---\n+/, '')
    renderedHtml.value = await marked.parse(stripped, { gfm: true, breaks: false })
  } catch (e: any) {
    errorMsg.value = String(e?.message || e)
  } finally {
    loading.value = false
  }
})

async function onCopy() {
  const snippet = `task(load_skills=["${props.skill.name}"], run_in_background=false, prompt="...")`
  try {
    await navigator.clipboard.writeText(snippet)
    emit('toast', 'success', `已复制 load_skills snippet`)
  } catch (e: any) {
    emit('toast', 'error', `复制失败: ${e?.message || e}`)
  }
}

async function onUninstall() {
  if (!confirming.value) {
    confirming.value = true
    return
  }
  try {
    const r = await uninstallSkill(props.skill.name)
    if (r.ok) emit('uninstalled', r.message)
    else emit('toast', 'error', r.message)
  } catch (e: any) {
    emit('toast', 'error', String(e?.message || e))
  }
}
</script>

<template>
  <div class="modal-shell" @click.self="emit('close')">
    <div class="modal-card">
      <div class="modal-head">
        <div class="title-block">
          <h2 class="name">{{ skill.name }}</h2>
          <div class="path">{{ skill.skill_md_path }}</div>
        </div>
        <button class="btn btn-icon btn-ghost" @click="emit('close')" title="关闭">✕</button>
      </div>

      <div v-if="skill.warnings.length" class="callout callout-warn" style="margin: 0 24px">
        <strong>⚠ 警告</strong>
        <ul>
          <li v-for="w in skill.warnings" :key="w">{{ w }}</li>
        </ul>
      </div>

      <div class="modal-body">
        <p v-if="loading">加载 SKILL.md ...</p>
        <p v-else-if="errorMsg" class="callout callout-error">⚠ {{ errorMsg }}</p>
        <div v-else v-html="renderedHtml"></div>
      </div>

      <div class="modal-foot">
        <div class="left">
          <button class="btn btn-ghost" @click="onCopy">📋 复制 load_skills</button>
        </div>
        <div class="right">
          <button v-if="confirming" class="btn btn-ghost" @click="confirming = false">取消</button>
          <button class="btn btn-danger" @click="onUninstall">
            {{ confirming ? '⚠ 确认卸载' : '🗑 卸载' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
