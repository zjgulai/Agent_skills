import type { InstallResponse, SkillsData } from './types'

const BASE = '/api'

export async function fetchSkills(): Promise<SkillsData> {
  const res = await fetch(`${BASE}/skills`)
  if (!res.ok) throw new Error(`fetchSkills failed: ${res.status}`)
  return res.json()
}

export async function fetchSkillMarkdown(name: string): Promise<string> {
  const res = await fetch(`${BASE}/skills/${encodeURIComponent(name)}/markdown`)
  if (!res.ok) throw new Error(`fetchSkillMarkdown failed: ${res.status}`)
  return res.text()
}

export async function installFromGithub(url: string, subdir?: string): Promise<InstallResponse> {
  const res = await fetch(`${BASE}/install/github`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url, subdir: subdir || null }),
  })
  return res.json()
}

export async function installFromUpload(file: File): Promise<InstallResponse> {
  const fd = new FormData()
  fd.append('file', file)
  const res = await fetch(`${BASE}/install/upload`, { method: 'POST', body: fd })
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
