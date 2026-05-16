---
description: List all installed skills, grouped by domain, with a one-line description each.
agent: build
---

# /skill-list

Quick read-only view of every installed skill, grouped by the 6 domains.

## Execute

```bash
portal/backend/.venv/bin/python -m agent.lib.portal_client list
```

Then format the output as a human-readable table grouped by domain. For each skill, show:
- name
- first 80 chars of description (one line)
- top 3 triggers (if any)

If a domain has 0 skills, print `(empty)`.

## Output format

```
=== AI 工程基础设施 (meta) — 1 skill ===
  • agent-dev-kit-architecture-designer
    给 AI 编码 agent 设计仓库五层架构...
    triggers: CLAUDE.md, agent directory structure, agent guardrails

=== 代码质量与交付闭环 (closeout) — 1 skill ===
  • codex-review
    用 codex review 做提交前的二次审查...
    triggers: codex review, autoreview, 二次审查

...

Total: <N> skills across <M> non-empty domains.
Portal: http://127.0.0.1:5174 (UI: http://localhost:5173 or https://skills-portal.localhost)
```

Read-only. No writes, no portal mutation.
