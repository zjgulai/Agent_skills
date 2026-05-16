---
description: Uninstall a skill by name. Removes via portal API and cleans up INDEX.md + skills-graph.
agent: build
---

# /skill-uninstall

Cleanly remove a skill: physical files (via portal API) + INDEX.md row + graph node + re-render.

**Arguments**: `$ARGUMENTS` — the skill name (e.g., `guizang-ppt-skill`).

## Execute these 4 steps in order

### Step 1 — Confirm skill exists

```bash
portal/backend/.venv/bin/python -m agent.lib.portal_client ensure
portal/backend/.venv/bin/python -m agent.lib.portal_client get <name>
```

If `get` returns 404, abort: skill not installed.

Show the user the skill's domain + description and ask for confirmation:
> About to uninstall **<name>** (domain: <domain>):
> > <description>
>
> Proceed? (y/N)

Wait for explicit `y` / `yes`.

### Step 2 — Remove from skills-graph.mmd (do this BEFORE INDEX.md and BEFORE physical delete)

```bash
portal/backend/.venv/bin/python -m agent.lib.graph_writer remove <name>
portal/backend/.venv/bin/python -m agent.lib.graph_writer render
```

If graph remove fails, abort BEFORE INDEX/portal touch — no partial state.

### Step 3 — Remove from INDEX.md

```bash
portal/backend/.venv/bin/python -m agent.lib.index_md_writer remove <name>
```

If this fails, the graph is already updated — alert the user and tell them to manually re-add the row OR run `/skill-graph-sync` to reconstruct from INDEX.

### Step 4 — Physical uninstall via portal API + refresh

```bash
portal/backend/.venv/bin/python -m agent.lib.portal_client uninstall <name>
portal/backend/.venv/bin/python -m agent.lib.portal_client refresh
```

### Final report

```
✅ removed graph node (<short_id>, backup: <path>)
✅ skills-graph.png re-rendered
✅ removed INDEX.md row (backup: <path>)
✅ deleted ~/.config/opencode/skills/<name>/
✅ portal refreshed: skill_count=<N>
```

Print backup paths so the user can recover if needed. Do NOT delete backups automatically.
