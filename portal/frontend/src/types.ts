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
