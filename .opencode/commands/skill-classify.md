---
description: Manually re-classify a skill into one of the 6 domains. Use when /skill-install picked the wrong domain.
agent: build
---

# /skill-classify

Move a skill from its current domain to a different one. Updates INDEX.md + skills-graph.mmd, re-renders PNG.

**Arguments**: `$ARGUMENTS` — the skill name (e.g., `guizang-ppt-skill`).

## Execute

### Step 1 — Show current state + the 6 options

```bash
portal/backend/.venv/bin/python -m agent.lib.portal_client get <name>
portal/backend/.venv/bin/python -m agent.lib.index_md_writer read | python3 -c "
import json, sys
d = json.load(sys.stdin)
for domain, names in d.items():
    if '<name>' in names:
        print(f'current domain: {domain}')
        break
"
```

Then print the 6 domain options to the user:

```
当前所属域：<current_domain>

可选目标域：
  1. meta       AI 工程基础设施（agent / skill / hook / plugin 治理）
  2. closeout   代码质量与交付闭环（review, commit, PR, release）
  3. desktop    桌面应用工程（Tauri / Electron / WebView / native）
  4. founder    创业与产品验证（MVP, ICP, pressure-test）
  5. ip         知识产权交付（专利, 软著, copyright）
  6. tooling    工具增强（PPT, docx, screenshot, image, etc.）

请回复目标域 ID（meta/closeout/desktop/founder/ip/tooling）：
```

### Step 2 — User picks a target

Wait for user response. Validate it's one of the 6 IDs. If invalid, ask again.

If user picks the same domain as current, exit with: "no change needed."

### Step 3 — Apply move

```bash
portal/backend/.venv/bin/python -m agent.lib.index_md_writer move <name> <new_domain>
```

If `move` succeeds, the row was relocated in INDEX.md. Now sync the graph:

```bash
portal/backend/.venv/bin/python -m agent.lib.graph_writer remove <name>
portal/backend/.venv/bin/python -m agent.lib.graph_writer add <name> <new_domain>
portal/backend/.venv/bin/python -m agent.lib.graph_writer render
```

### Step 4 — Refresh portal

```bash
portal/backend/.venv/bin/python -m agent.lib.portal_client refresh
```

### Final report

```
✅ moved <name>: <old_domain> → <new_domain>
   INDEX.md backup: <path>
   graph backup: <path>
   skills-graph.png re-rendered (<bytes> bytes)
```
