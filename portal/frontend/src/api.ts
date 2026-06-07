import type { HooksData, InstallResponse, McpsData, SkillsData } from './types'

const BASE = '/api'

export async function fetchSkills(): Promise<SkillsData> {
  const res = await fetch(`${BASE}/skills`)
  if (!res.ok) throw new Error(`fetchSkills failed: ${res.status}`)
  return res.json()
}

export async function fetchHooks(): Promise<HooksData> {
  const res = await fetch(`${BASE}/hooks`)
  if (!res.ok) throw new Error(`fetchHooks failed: ${res.status}`)
  return res.json()
}

export async function fetchMcps(): Promise<McpsData> {
  const res = await fetch(`${BASE}/mcps`)
  if (!res.ok) throw new Error(`fetchMcps failed: ${res.status}`)
  return res.json()
}

export async function fetchHookSource(name: string): Promise<string> {
  const res = await fetch(`${BASE}/hooks/${encodeURIComponent(name)}/source`)
  if (!res.ok) throw new Error(`fetchHookSource failed: ${res.status}`)
  return res.text()
}

export async function fetchSkillMarkdown(name: string): Promise<string> {
  const res = await fetch(`${BASE}/skills/${encodeURIComponent(name)}/markdown`)
  if (!res.ok) throw new Error(`fetchSkillMarkdown failed: ${res.status}`)
  return res.text()
}

export async function installFromGithub(url: string, subdir?: string, overwrite = false): Promise<InstallResponse> {
  const res = await fetch(`${BASE}/install/github`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url, subdir: subdir || null, overwrite }),
  })
  return res.json()
}

export async function installFromUpload(file: File, overwrite = false): Promise<InstallResponse> {
  const fd = new FormData()
  fd.append('file', file)
  const res = await fetch(`${BASE}/install/upload?overwrite=${overwrite ? 'true' : 'false'}`, { method: 'POST', body: fd })
  return res.json()
}

export async function uninstallSkill(name: string): Promise<InstallResponse> {
  const res = await fetch(`${BASE}/skills/${encodeURIComponent(name)}`, { method: 'DELETE' })
  return res.json()
}

export async function refreshIndex(): Promise<{ ok: boolean; skill_count: number }> {
  const res = await fetch(`${BASE}/refresh`, { method: 'POST' })
  return res.json()
}
