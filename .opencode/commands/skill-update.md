---
description: Update one skill (or all skills) via git pull, then refresh portal index.
agent: build
---

# /skill-update

Pull the latest version of an installed skill from its origin git repo, then refresh portal's index.

**Arguments**: `$ARGUMENTS` — either a skill name (e.g., `guizang-ppt-skill`) or the literal word `all`.

## Execute

### Step 1 — Ensure portal is up

```bash
portal/backend/.venv/bin/python -m agent.lib.portal_client ensure
```

### Step 2 — Identify targets

If `$ARGUMENTS` is `all`:
```bash
ls -d ~/.config/opencode/skills/*/.git 2>/dev/null | sed 's|/.git||;s|.*/||'
```

Otherwise, treat `$ARGUMENTS` as a single skill name. Verify `~/.config/opencode/skills/<name>/.git` exists. If not, report: "skill `<name>` was not installed via git, cannot update; uninstall and reinstall instead."

### Step 3 — git pull each target

For each target, in order:

```bash
cd ~/.config/opencode/skills/<name> && git pull --ff-only --no-rebase 2>&1
```

Track per-target outcome:
- `Already up to date.` → ok, no change
- diff summary → ok, updated
- merge conflict / non-fast-forward → ERROR, leave repo as-is, do NOT abort the loop, record for final report

### Step 4 — Refresh portal index after all pulls

```bash
portal/backend/.venv/bin/python -m agent.lib.portal_client refresh
```

### Final report

Per-target table:
```
| name                              | status                    |
|-----------------------------------|---------------------------|
| guizang-ppt-skill                 | Already up to date        |
| codex-review                      | Updated (3 commits)       |
| custom-skill-broken               | ERROR: merge conflict     |
```

Then portal refresh result:
```
portal refreshed: skill_count=<N>
```

If any target errored, list **next steps** for the user (`cd ~/.config/opencode/skills/<name> && git status`).

> Update does NOT touch INDEX.md / graph — only the skill content updates. Domain classification stays as-is. If a `git pull` brings new content suggesting a different domain, run `/skill-classify <name>` afterward.
