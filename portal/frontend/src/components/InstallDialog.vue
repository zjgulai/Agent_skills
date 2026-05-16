<script setup lang="ts">
import { ref } from 'vue'
import { installFromGithub, installFromUpload } from '../api'

const emit = defineEmits<{
  close: []
  installed: [message: string]
  toast: [kind: 'info' | 'success' | 'error', text: string]
}>()

const tab = ref<'github' | 'upload'>('github')
const url = ref('')
const subdir = ref('')
const fileInput = ref<HTMLInputElement | null>(null)
const submitting = ref(false)
const lastError = ref('')
const warnings = ref<string[]>([])

async function submitGithub() {
  if (!url.value.trim()) {
    lastError.value = '请填写 GitHub URL'
    return
  }
  submitting.value = true
  lastError.value = ''
  warnings.value = []
  try {
    const r = await installFromGithub(url.value.trim(), subdir.value.trim() || undefined)
    if (r.ok) {
      warnings.value = r.warnings || []
      emit('installed', `${r.message}`)
    } else {
      lastError.value = r.message
    }
  } catch (e: any) {
    lastError.value = String(e?.message || e)
  } finally {
    submitting.value = false
  }
}

async function submitUpload() {
  const f = fileInput.value?.files?.[0]
  if (!f) {
    lastError.value = '请选择一个 .md 文件'
    return
  }
  submitting.value = true
  lastError.value = ''
  warnings.value = []
  try {
    const r = await installFromUpload(f)
    if (r.ok) {
      warnings.value = r.warnings || []
      emit('installed', `${r.message}`)
    } else {
      lastError.value = r.message
    }
  } catch (e: any) {
    lastError.value = String(e?.message || e)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="modal-shell" @click.self="emit('close')">
    <div class="modal-card size-small">
      <div class="modal-head">
        <div class="title-block">
          <h2 class="name">安装新 skill</h2>
          <div class="path">从 GitHub 仓库克隆，或上传单个 SKILL.md 文件</div>
        </div>
        <button class="btn btn-icon btn-ghost" @click="emit('close')" title="关闭">✕</button>
      </div>

      <div class="dialog-form">
        <div class="tabs">
          <button :class="{ active: tab === 'github' }" @click="tab = 'github'">GitHub URL</button>
          <button :class="{ active: tab === 'upload' }" @click="tab = 'upload'">上传 .md</button>
        </div>

        <template v-if="tab === 'github'">
          <div class="field">
            <label>GitHub 仓库 URL</label>
            <input
              v-model="url"
              type="url"
              placeholder="https://github.com/owner/repo"
              :disabled="submitting"
            />
          </div>
          <div class="field">
            <label>子目录（可选）</label>
            <input
              v-model="subdir"
              type="text"
              placeholder="仓库根没有 SKILL.md 时使用，例如：startup-pressure-test"
              :disabled="submitting"
            />
            <div class="hint">仓库根直接有 SKILL.md 时留空。多个 SKILL.md 候选会报错，需要用 subdir 指定。</div>
          </div>
          <button class="btn btn-primary" :disabled="submitting" @click="submitGithub">
            {{ submitting ? '安装中...' : '开始安装' }}
          </button>
        </template>

        <template v-else>
          <div class="field">
            <label>选择本地 SKILL.md</label>
            <input ref="fileInput" type="file" accept=".md" :disabled="submitting" />
            <div class="hint">
              单文件上传只装 SKILL.md 本身（自动剥除 markdown 代码栅栏包裹）。带资源的 skill 请用 GitHub URL。
            </div>
          </div>
          <button class="btn btn-primary" :disabled="submitting" @click="submitUpload">
            {{ submitting ? '安装中...' : '上传并安装' }}
          </button>
        </template>

        <div v-if="lastError" class="callout callout-error">⚠ {{ lastError }}</div>
        <div v-if="warnings.length" class="callout callout-warn">
          <strong>注意</strong>
          <ul>
            <li v-for="w in warnings" :key="w">{{ w }}</li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>
