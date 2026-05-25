---
description: Install a skill from a GitHub URL. Auto-detects monorepo (multiple SKILL.md) and offers batch install. Integrates metadata, syncs to docs, commits and pushes (one-shot end-to-end deployment).
agent: build
---

# /skill-install

Install a new skill (or **whole monorepo of skills**) into `~/.config/opencode/skills/<name>/`, integrate into meta-data layer (`INDEX.md`, `skills-graph.mmd`, `skills-graph.png`), **sync to `data-mirror/`**, **append a case-study entry**, **commit and push** so the docs site auto-rebuilds.

**Arguments**: `$ARGUMENTS` — expected to contain the GitHub URL, optionally followed by `--subdir <X>` to force a specific subpath.

## Integrity guard (run BEFORE every step, fail-fast)

```bash
# 每次执行前确保在项目根目录
cd /Users/lute/project/Agent/Agent_skills

# 记录 AGENTS.md hash（防止写操作意外污染）
AGENTS_HASH_BEFORE=$(shasum -a 256 AGENTS.md | awk '{print $1}')
```

After **every** step that writes files, verify:
```bash
AGENTS_HASH_AFTER=$(shasum -a 256 AGENTS.md | awk '{print $1}')
if [ "$AGENTS_HASH_BEFORE" != "$AGENTS_HASH_AFTER" ]; then
  echo "❌ AGENTS.md was corrupted! Restoring from git..."
  git checkout HEAD -- AGENTS.md
  exit 1
fi
```

## Execute these 12 steps in order

Use `portal/backend/.venv/bin/python` (NOT system python). **All commands MUST run from the repository root** (`cd /Users/lute/project/Agent/Agent_skills` before every bash block).

### Step 0 — Detect monorepo (skip if user gave explicit --subdir)

```bash
portal/backend/.venv/bin/python -m agent.lib.portal_client scan <URL>
```

Returns `{"subdirs": [...]}`. Decision tree:

- **0 subdirs** → repo root has a SKILL.md (or none at all). Proceed to Step 1 with no `subdir`. If install in Step 2 fails with "no SKILL.md found", report to user.
- **1 subdir** → single skill packaged in a subfolder. Pass that subdir to Step 2.
- **2+ subdirs (monorepo)** → ask user:
  > 🔍 检测到 **monorepo**，仓库下有 N 个 SKILL.md：
  >   1. skills/foo
  >   2. skills/bar
  >   3. ...
  >
  > 你要：
  >   A. 全装（推荐，如果是工具集）
  >   B. 只装其中几个（告诉我编号或名字）
  >   C. 取消
  >
  Wait for user reply. If "A" → use `install-monorepo` (all). If "B" → list the chosen subdirs and pass them to `install-monorepo URL subdir1 subdir2 ...`. If "C" → abort.

### Step 1 — Ensure portal is running

```bash
portal/backend/.venv/bin/python -m agent.lib.portal_client ensure
```

If `ensure` fails, abort and report the error verbatim.

### Step 2 — Install via portal API

**Single skill mode**:
```bash
portal/backend/.venv/bin/python -m agent.lib.portal_client install <URL> [SUBDIR]
```

**Monorepo mode** (multiple subdirs):
```bash
portal/backend/.venv/bin/python -m agent.lib.portal_client install-monorepo <URL> [SUBDIR1 SUBDIR2 ...]
```

Capture all installed skill names from the JSON output. For monorepo, the `installed[]` array gives per-subdir result (continues on individual failures).

For each successfully installed skill, proceed through Steps 3-7. **For monorepo, treat each successful skill as a separate row to append to INDEX.md and graph.**

### Step 3 — Read frontmatter for each installed skill

```bash
portal/backend/.venv/bin/python -m agent.lib.portal_client get <skill_name>
```

### Step 4 — Infer domain for each skill

```bash
portal/backend/.venv/bin/python -m agent.lib.domain_inference <skill_name> "<description>"
```

If domain is `uncategorized`:
- **Single skill**: ask user which of 6 domains to use (meta / closeout / desktop / founder / ip / tooling).
- **Monorepo with many `uncategorized`**: batch-ask once — "我看到 N 个 skill 推断 uncategorized，按用途分组归类：方法论 → meta，提交闭环 → closeout，其他 → ?". Apply user's grouping.

### Step 5 — Append to INDEX.md (one row per skill)

For each skill:
```bash
portal/backend/.venv/bin/python -m agent.lib.index_md_writer append \
  "<skill_name>" "<domain>" "<role_one_liner>" "<top_3_triggers>"
```

### Step 6 — Add to skills-graph.mmd (one node per skill, then render once)

```bash
# For each skill:
portal/backend/.venv/bin/python -m agent.lib.graph_writer add "<skill_name>" "<domain>"
# Then render PNG once at the end:
portal/backend/.venv/bin/python -m agent.lib.graph_writer render
```

### Step 7 — Refresh portal index

```bash
portal/backend/.venv/bin/python -m agent.lib.portal_client refresh
```

### Step 8 — Sync metadata to data-mirror/

```bash
bin/sync-data
```

### Step 9 — Append to case-studies.json

**Auto-fill first, ask only if needed.**

#### 9-A: Collect auto-fillable facts

**CRITICAL**: Always use absolute path. Never use relative `open("docs/...")`.

```python
import json, pathlib

# 绝对路径 — 防止 cwd 漂移写坏无关文件
PROJECT_ROOT = pathlib.Path("/Users/lute/project/Agent/Agent_skills")
CASE_STUDIES = PROJECT_ROOT / "docs" / "_src" / "case-studies.json"

data = json.loads(CASE_STUDIES.read_text(encoding="utf-8"))
next_id = data["states"][-1]["id"] + 1

# From portal get <skill_name> (already fetched in Step 3):
#   name, description, domain
# From skills-graph delta (Step 6):
#   nodes added, PNG bytes before/after
# From portal refresh (Step 7):
#   skill_count before/after
# From git log / install result:
#   trigger_cmd = the URL/subdir the user gave
#   any install warnings (e.g. YAML parse fallback, timeout)
```

Auto-generate:
- `title_zh` / `title_en` — from skill name + domain
- `trigger_cmd` — the exact URL the user provided
- `skill_added` — name(s) from Step 2 install result
- `domain_added` — from Step 4 domain inference
- `delta_zh` / `delta_en` — "+N nodes · domain +M · PNG X→Y bytes · total skills A→B"
- `bullets_zh` / `bullets_en` (3 bullets auto-generated):
  - bullet 1: install method (portal API / manual fallback / monorepo batch) + any notable warnings
  - bullet 2: domain assignment rationale (from Step 4 evidence)
  - bullet 3: skill capability summary (first 200 chars of description)

#### 9-B: Ask ONLY if desc is ambiguous or >1 bullet needs human context

For **single skill** with clear frontmatter: **ask 0 questions** — auto-fill and proceed.

For **single skill** where description is <30 chars or `uncategorized` or install had notable workarounds:
> 补一句话定位（<40 字）给 State {next_id}？（或回「跳过」用 description 代替）

For **monorepo suite**: **ask 0 questions** — auto-generate bullets from (a) skill list (b) domain distribution (c) PNG delta. Use the suite repo name + skill count as title.

#### 9-C: Write

```python
# Append new_state to data["states"]
# Write back with absolute path — NEVER use open("docs/...") with relative path
CASE_STUDIES.write_text(
    json.dumps(data, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8"
)
```

Append to `docs/_src/case-studies.json` (Python read → append → write back).

> **Rule**: Step 9 is NEVER skipped. If user gives no answer within the same turn, auto-fill with 0 questions and proceed. The only acceptable outcome is a written State entry.

### Step 10 — Commit

```bash
cd /Users/lute/project/Agent/Agent_skills

# 1. 最终哨兵：确认 AGENTS.md 未被污染
AGENTS_HASH_FINAL=$(shasum -a 256 AGENTS.md | awk '{print $1}')
if [ "$AGENTS_HASH_BEFORE" != "$AGENTS_HASH_FINAL" ]; then
  echo "❌ AGENTS.md corrupted before commit! Restoring..."
  git checkout HEAD -- AGENTS.md
  exit 1
fi

# 2. 清理临时备份文件，不污染 git status
rm -f AGENTS.md.corrupted.bak

# 3. 只暂存预期文件，NEVER use git add .
git add data-mirror/ docs/_src/case-studies.json
git status --short
git commit -m "feat(skills): add <name> (<single skill or 'suite of N'>)

<one-line user-provided desc>

- domain: <domain or 'meta + closeout' for mixed>
- INDEX.md: appended <N> rows
- skills-graph: +<N> nodes
- case-studies.json: State <id> appended
"
```

### Step 11 — Push

```bash
git push origin main
```

### Step 12 — Report CI URL

```bash
sleep 5 && gh run list --limit 1 --json databaseId,status,name 2>/dev/null
```

### Final report

```
🎉 <skill_name | suite name> installed end-to-end!

Single skill mode:
✅ portal API health
✅ git clone / install ok
✅ frontmatter validated: name=<name>
✅ domain: <domain>
✅ INDEX.md updated
✅ skills-graph.mmd: node <SID> (<domain>)
✅ skills-graph.png re-rendered (<bytes>)
✅ portal refreshed: skill_count=<N>
✅ data-mirror/ synced
✅ case-studies.json: State <id>
✅ git push complete
🚀 CI: https://github.com/zjgulai/Agent_skills/actions/runs/<id>

Monorepo mode:
✅ scanned: <total> SKILL.md candidates
✅ installed <ok>/<total>: [list of skill names]
   (failed: [list, if any] — see install-monorepo output)
✅ domains: meta+<N>, closeout+<M>, ...
✅ skills-graph: +<N> nodes, PNG <old>→<new> bytes
✅ case-studies.json: State <id> ("suite of N skills")
🚀 CI: <url>

📡 Site updates in ~1 minute: https://zjgulai.github.io/Agent_skills/zh/handbook.html#state-<id>
```

## Failure handling

- Stop on first **infrastructure** failure (Steps 1, 2 for single, 5-7, 10-11).
- For **monorepo Step 2**: continue on per-subdir failures, report final tally.
- Steps 9-11 (case-study + commit + push): if these fail, **do NOT undo** Steps 1-8 — the skill is correctly installed locally. Report partial completion and manual finish path.
