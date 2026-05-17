---
description: Install a skill from a GitHub URL, integrate metadata, sync to docs site, commit and push (one-shot end-to-end deployment).
agent: build
---

# /skill-install

Install a new skill into `~/.config/opencode/skills/<name>/`, integrate it into the meta-data layer (`INDEX.md`, `skills-graph.mmd`, `skills-graph.png`), **sync to `data-mirror/`**, **append a case-study entry**, **commit and push** so the docs site auto-rebuilds.

**Arguments**: `$ARGUMENTS` — expected to contain the GitHub URL, optionally followed by `--subdir <X>` if the skill lives in a subdirectory of the repo.

## Execute these 11 steps in order

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

### Step 7 — Refresh portal index

```bash
portal/backend/.venv/bin/python -m agent.lib.portal_client refresh
```

### Step 8 — Sync metadata to data-mirror/ (for docs site)

```bash
bin/sync-data
```

Should print "✅ 同步：INDEX.md" (and possibly skills-graph.{mmd,png}).

### Step 9 — Ask user for case-study metadata, then append to case-studies.json

Ask the user briefly (one round of 3 short questions, single response):
> 我要给 docs 站的 case study 补一条 State N+1 记录。三个问题一起回我：
> 1. 这个 skill 一句话定位（一行话，<40 字）？
> 2. 它做的最有意思的事情/独特能力（1-3 个 bullet 点）？
> 3. 还有什么我应该知道的（可选；比如装它有什么坑）？

After the user replies, append a new state to `docs/_src/case-studies.json`:
- `id`: `max(existing ids) + 1`
- `title_zh`: `"State <id>：装 <skill_name> 后"`
- `title_en`: `"State <id>: after installing <skill_name>"`
- `desc_zh` / `desc_en`: 1-sentence positioning (from user reply 1; translate if user only gave one language)
- `trigger_cmd`: `/skill-install <URL>`（如果是 pipx/其他来源则用真实命令）
- `skill_added`: `<skill_name>`
- `domain_added`: `<domain>`
- `delta_zh` / `delta_en`: `"+1 node (<SID> in <domain>) · ..."` (auto-construct from graph_writer output in Step 6)
- `bullets_zh` / `bullets_en`: bullet points (from user reply 2)
- `png`: `"skills-graph.png"` (always use the current graph, not a state-N PNG)
- `png_bytes`: file size of the rendered PNG

Use `python3` to safely edit the JSON (read → append to `states` → write back with `indent=2`).

### Step 10 — Commit changes

```bash
git add data-mirror/ docs/_src/case-studies.json
git status --short  # show user what's staged
git commit -m "feat(skills): add <skill_name> ($DOMAIN, State <id>)

<one-line description from case-study desc_zh>

- INDEX.md: appended under domain '<domain>'
- skills-graph.mmd: new node <SID> in <domain>
- case-studies.json: State <id> appended
"
```

### Step 11 — Push to remote

```bash
git push origin main
```

After push succeeds, fetch the GitHub Actions run ID and report it:
```bash
sleep 5 && gh run list --limit 1 --json databaseId,status,name 2>/dev/null | head
```

### Final report

Print a concise summary:

```
🎉 <skill_name> installed end-to-end!

✅ portal API health
✅ git clone / install ok
✅ frontmatter validation passed: name=<name>
✅ domain inference: <domain> (evidence: <hits>)
✅ INDEX.md updated (backup: <path>)
✅ skills-graph.mmd updated (short_id: <SID>, backup: <path>)
✅ skills-graph.png re-rendered (<bytes> bytes)
✅ portal refreshed: skill_count=<N>
✅ data-mirror/ synced (3 files)
✅ case-studies.json: State <id> appended
✅ git commit + push complete
🚀 GitHub Actions: https://github.com/zjgulai/Agent_skills/actions/runs/<run_id>

📡 Site will update in ~1 minute:
   https://zjgulai.github.io/Agent_skills/zh/handbook.html#state-<id>
```

## Failure handling

If ANY step fails, print:
- which step failed
- the verbatim error
- whether INDEX.md backup needs to be reviewed (path)
- explicit instructions to the user (e.g., "run /skill-uninstall <name> to clean up the partial install")

Do NOT silently fix or retry. Stop on first failure.

**Special handling for Step 9-11 failures**: if commit or push fails, do NOT undo Steps 1-8 — the skill is already correctly installed locally. Report the partial completion and let the user finish manually:
```
⚠️  Skill installed locally but push failed.
    Manual completion:
    git add data-mirror/ docs/_src/case-studies.json
    git commit -m "feat(skills): add <skill_name>"
    git push origin main
```
