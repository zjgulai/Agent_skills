---
description: Install a skill from a GitHub URL via portal API. Auto-classifies into domain, updates INDEX.md, redraws skills-graph.
agent: build
---

# /skill-install

Install a new skill into `~/.config/opencode/skills/<name>/` and integrate it into the meta-data layer (`INDEX.md`, `skills-graph.mmd`, `skills-graph.png`).

**Arguments**: `$ARGUMENTS` — expected to contain the GitHub URL, optionally followed by `--subdir <X>` if the skill lives in a subdirectory of the repo.

## Execute these 7 steps in order

Use `portal/backend/.venv/bin/python` (NOT system python). All commands run from the repository root.

### Step 1 — Ensure portal is running

```bash
portal/backend/.venv/bin/python -m agent.lib.portal_client ensure
```

If `ensure` fails, abort and report the error verbatim. Do NOT proceed.

### Step 2 — Install via portal API (delegates to portal's installer.py)

```bash
portal/backend/.venv/bin/python -m agent.lib.portal_client install <URL> [SUBDIR]
```

Capture the returned JSON. The `skill_name` field is the canonical name (from frontmatter, NOT the URL). Use this name for all subsequent steps.

### Step 3 — Read frontmatter for domain inference

```bash
portal/backend/.venv/bin/python -m agent.lib.portal_client get <skill_name>
```

Extract `frontmatter.description`. This is what feeds the inference.

### Step 4 — Infer domain

```bash
portal/backend/.venv/bin/python -m agent.lib.domain_inference <skill_name> "<description>"
```

If domain is `uncategorized`, ask the user which of the 6 domains to use:
> Domain inference returned `uncategorized` with no keyword hits. Pick a domain manually:
> 1. meta — AI engineering infra
> 2. closeout — code review/PR/release
> 3. desktop — native-feel cross-platform desktop
> 4. founder — startup validation
> 5. ip — patent/copyright deliverables
> 6. tooling — generic tooling (PPT, screenshot, docx, etc.)

Wait for the user reply before continuing.

### Step 5 — Append to INDEX.md

```bash
portal/backend/.venv/bin/python -m agent.lib.index_md_writer append \
  "<skill_name>" "<domain>" "<role_one_liner>" "<top_3_triggers_comma_separated>"
```

Construct the `role` from the SKILL.md (one terse sentence, ≤30 chars, what it does).
Construct `triggers` from the description's strongest keyword phrases (the same ones the inference matched).

If it returns ok=false, abort and report. Do NOT proceed to graph until INDEX is updated.

### Step 6 — Add to skills-graph.mmd + re-render PNG

```bash
portal/backend/.venv/bin/python -m agent.lib.graph_writer add "<skill_name>" "<domain>"
portal/backend/.venv/bin/python -m agent.lib.graph_writer render
```

Both must return ok=true.

### Step 7 — Refresh portal index + report

```bash
portal/backend/.venv/bin/python -m agent.lib.portal_client refresh
```

### Final report

Print a concise summary as a checklist:

```
✅ portal API health
✅ git clone / install ok
✅ frontmatter validation passed: name=<name>
✅ domain inference: <domain> (evidence: <hits>)
✅ INDEX.md updated (backup: <path>)
✅ skills-graph.mmd updated (short_id: <SID>, backup: <path>)
✅ skills-graph.png re-rendered (<bytes> bytes)
✅ portal refreshed: skill_count=<N>

Open https://skills-portal.localhost (or http://localhost:5173) to see the new skill in the "<domain label>" group.
```

If ANY step fails, print:
- which step failed
- the verbatim error
- whether INDEX.md backup needs to be reviewed (path)
- explicit instructions to the user (e.g., "run /skill-uninstall <name> to clean up the partial install")

Do NOT silently fix or retry. Stop on first failure.
