<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import mermaid from 'mermaid'

const props = defineProps<{ mermaidSource: string }>()
const container = ref<HTMLDivElement | null>(null)
const inner = ref<HTMLDivElement | null>(null)
const scrollEl = ref<HTMLDivElement | null>(null)
const errorMsg = ref('')
const scale = ref(1)
const fitScale = ref(1)
const naturalSize = ref<{ w: number; h: number }>({ w: 0, h: 0 })

function applyScale() {
  if (!inner.value) return
  inner.value.style.transform = `scale(${scale.value})`
  inner.value.style.width = `${naturalSize.value.w * scale.value}px`
  inner.value.style.height = `${naturalSize.value.h * scale.value}px`
}

function fitToWidth() {
  if (!scrollEl.value || naturalSize.value.w === 0) return
  const containerWidth = scrollEl.value.clientWidth - 48
  fitScale.value = Math.min(1, containerWidth / naturalSize.value.w)
  scale.value = fitScale.value
  applyScale()
}

async function render() {
  if (!props.mermaidSource || !container.value) return
  try {
    mermaid.initialize({
      startOnLoad: false,
      theme: 'default',
      flowchart: { useMaxWidth: false, htmlLabels: true },
    })
    const id = `skills-graph-${Date.now()}`
    const { svg } = await mermaid.render(id, props.mermaidSource)
    container.value.innerHTML = svg
    await new Promise(r => setTimeout(r, 50))
    const svgEl = container.value.querySelector('svg') as SVGSVGElement | null
    if (svgEl) {
      const vb = svgEl.viewBox?.baseVal
      if (vb && vb.width > 0) {
        naturalSize.value = { w: vb.width, h: vb.height }
      } else {
        const r = svgEl.getBoundingClientRect()
        naturalSize.value = { w: r.width, h: r.height }
      }
      svgEl.style.width = `${naturalSize.value.w}px`
      svgEl.style.height = `${naturalSize.value.h}px`
    }
    fitToWidth()
  } catch (e: any) {
    errorMsg.value = String(e?.message || e)
  }
}

function reset() {
  scale.value = fitScale.value
  applyScale()
}
function full() {
  scale.value = 1
  applyScale()
}
function zoomIn() {
  scale.value = Math.min(2, scale.value + 0.2)
  applyScale()
}
function zoomOut() {
  scale.value = Math.max(0.3, scale.value - 0.2)
  applyScale()
}

let resizeObserver: ResizeObserver | null = null

onMounted(() => {
  render()
  if (scrollEl.value && 'ResizeObserver' in window) {
    resizeObserver = new ResizeObserver(() => {
      if (Math.abs(scale.value - fitScale.value) < 0.01) fitToWidth()
    })
    resizeObserver.observe(scrollEl.value)
  }
})

onUnmounted(() => {
  resizeObserver?.disconnect()
})
</script>

<template>
  <div class="graph-frame">
    <div class="graph-controls">
      <button class="btn btn-icon btn-ghost" title="缩小" @click="zoomOut">−</button>
      <button class="btn btn-icon btn-ghost" title="自适应宽度" @click="reset">⊙</button>
      <button class="btn btn-icon btn-ghost" title="100%" @click="full">1:1</button>
      <button class="btn btn-icon btn-ghost" title="放大" @click="zoomIn">+</button>
    </div>
    <div v-if="errorMsg" class="callout callout-error" style="margin: 16px">{{ errorMsg }}</div>
    <div ref="scrollEl" class="graph-scroll">
      <div ref="inner" class="graph-inner">
        <div ref="container"></div>
      </div>
    </div>
  </div>
</template>
