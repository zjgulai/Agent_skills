export interface SkillResource {
  kind: 'dir' | 'file'
  name: string
  path: string
}

export interface Skill {
  name: string
  domain: string
  description: string
  triggers: string[]
  skill_md_path: string
  skill_dir: string
  resources: SkillResource[]
  installed_at: string
  warnings: string[]
}

export interface Domain {
  id: string
  label: string
  color: string
  stroke: string
  skill_names: string[]
}

export interface Graph {
  mermaid_source: string
  png_path: string
}

export interface SkillsData {
  generated_at: string
  skills_root: string
  skill_count: number
  domains: Domain[]
  skills: Skill[]
  graph: Graph
}

export interface InstallResponse {
  ok: boolean
  message: string
  skill_name?: string
  skill_dir?: string
  warnings?: string[]
}

export interface HookItem {
  name: string
  version: string
  description: string
  domain: string
  priority: 'P0' | 'P1' | 'P2'
  hook_events: string[]
  matchers: string[]
  compatibility: { opencode: string; codex: string; cursor: string; kimi: string }
  requires: { binaries?: string[]; env?: string[] }
  triggers: string[]
  links: Record<string, string>
}

export interface HooksData {
  kind: 'hook'
  repo: string
  count: number
  items: HookItem[]
}

export interface McpItem {
  name: string
  version: string
  description: string
  domain: string
  priority: 'P0' | 'P1' | 'P2'
  mcp_command: string[]
  compatibility: { opencode: string; codex: string; cursor: string; kimi: string }
  requires: { binaries?: string[]; env?: string[] }
  triggers: string[]
  links: Record<string, string>
  env_satisfied: Record<string, boolean>
  binaries_satisfied: Record<string, boolean>
}

export interface McpsData {
  kind: 'mcp'
  repo: string
  count: number
  items: McpItem[]
}
