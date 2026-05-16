# PR drafts · OpenCode ecosystem outreach

> Filled in 2026-05-16 from librarian audit (bg_356d719b).
> **I never submit these PRs automatically — they are drafts for you to review and push manually.**

---

## ⚠️ One critical caveat before any PR

The most popular aggregator (`ComposioHQ/awesome-claude-skills`) **requires a `SKILL.md` in your repo root**. `Agent_skills` is a **lifecycle manager**, not a Skill itself — there is no SKILL.md.

Two options:

- **Option A — skip ComposioHQ**: most natural; submit to OpenCode-native + general-aggregator targets only.
- **Option B — add a `SKILL.md` to the repo** that wraps the agent as a callable skill. This is **possible but not free** — it means `/skill-install zjgulai/Agent_skills` would itself install Agent_skills as a meta-skill. Doable, but conceptually circular (a skill that manages skills).

**Recommendation**: Option A. Hit the 3 strong targets that DON'T require SKILL.md.

---

## 🎯 Target 1 — `awesome-opencode/awesome-opencode` ★★★

> **Best fit for an OpenCode-specific lifecycle tool.** Submit FIRST.

| | |
|---|---|
| URL | https://github.com/awesome-opencode/awesome-opencode |
| Stars / Forks | 6,945 / 467 |
| Last commit | Mar 21, 2026 (~56 days; queue backed up but maintained) |
| Open PRs | 30 (recently reviewed May 15) |
| Format | YAML file in `data/projects/` |
| Model | PR-only, auto-validates YAML on PR |

### Action

Create file `data/projects/agent-skills.yaml` in a fork:

```yaml
name: Agent Skills
repo: https://github.com/zjgulai/Agent_skills
tagline: Skills lifecycle manager for OpenCode
description: Lifecycle manager for OpenCode skills — install, classify, dependency graph, health doctor, and a local FastAPI + Vite web portal for browsing and managing installed skills.
```

### PR title

`docs: add agent-skills to projects`

### PR body (short)

```markdown
Adds [Agent_skills](https://github.com/zjgulai/Agent_skills) — a lifecycle manager for OpenCode skills.

Provides 11 slash commands covering install / classify / graph / doctor / recommend, backed by a local FastAPI + Vite portal.

- Online handbook (EN + 中文): https://zjgulai.github.io/Agent_skills/handbook.html
- v1.0.0 released, MIT licensed
- Recently verified end-to-end with two real installs (guizang-ppt-skill + skill-creator)
```

### Steps to submit

```bash
gh repo fork awesome-opencode/awesome-opencode --clone
cd awesome-opencode
cat > data/projects/agent-skills.yaml <<'YAML'
name: Agent Skills
repo: https://github.com/zjgulai/Agent_skills
tagline: Skills lifecycle manager for OpenCode
description: Lifecycle manager for OpenCode skills — install, classify, dependency graph, health doctor, and a local FastAPI + Vite web portal for browsing and managing installed skills.
YAML
git checkout -b add-agent-skills
git add data/projects/agent-skills.yaml
git commit -m "docs: add agent-skills to projects"
git push origin add-agent-skills
gh pr create --fill
```

---

## 🎯 Target 2 — `Chat2AnyLLM/awesome-repo-configs` ★★

> **Lowest-friction PR.** Auto-aggregated downstream into `Chat2AnyLLM/awesome-claude-skills` (122★).

| | |
|---|---|
| URL | https://github.com/Chat2AnyLLM/awesome-repo-configs |
| Downstream | https://github.com/Chat2AnyLLM/awesome-claude-skills (122★, daily commits) |
| Format | Config file entry (need to read repo's exact format) |
| Model | PR-only, auto-aggregated downstream |

### Action

1. Fork the config repo
2. Find their schema (likely YAML/JSON with `repo`, `description`, `category`)
3. Add Agent_skills entry under `Tools & Utilities` category
4. PR

### PR title

`Add zjgulai/Agent_skills to Tools & Utilities`

### Why lower priority than Target 1

Downstream list is only 122★. Not a prestige target — purely for discoverability via auto-aggregation.

---

## 🎯 Target 3 — `ComposioHQ/awesome-claude-skills` ⚠️ skip unless you add SKILL.md

> Biggest list (60K★) but **requires a working SKILL.md** in your repo. See "One critical caveat" above.

If you decide to add a SKILL.md to make this eligible:

| | |
|---|---|
| URL | https://github.com/ComposioHQ/awesome-claude-skills |
| Stars | 60,043 |
| Last commit | May 7, 2026 |
| Section | `### Development & Code Tools` in README.md |
| Format | Markdown list item |

### Entry

```markdown
- [Agent_skills](https://github.com/zjgulai/Agent_skills) - OpenCode skills lifecycle manager with install, classify, graph, and doctor commands via FastAPI + Vite portal.
```

### Caveat

Don't submit unless you've added a real SKILL.md to the repo root. They will close the PR otherwise.

---

## 🕒 Target 4 — `VoltAgent/awesome-agent-skills` (wait 2-3 weeks)

| | |
|---|---|
| URL | https://github.com/VoltAgent/awesome-agent-skills |
| Stars | 21,892 |
| Last commit | May 10, 2026 |
| Hard policy | **"Brand new skills that were just created are not accepted."** |
| When to submit | After Agent_skills has ≥15 stars + 1 issue/discussion |

### Entry format (when ready)

```markdown
- **[zjgulai/Agent_skills](https://github.com/zjgulai/Agent_skills)** - OpenCode skills lifecycle: install, classify, graph, doctor
```

≤10-word description requirement is strict.

### PR title

`Add skill: zjgulai/Agent_skills`

---

## 📋 Recommended order

1. **Today**: Target 1 (awesome-opencode/awesome-opencode) — best fit, OpenCode native
2. **Today** (optional): Target 2 (Chat2AnyLLM/awesome-repo-configs) — easy win, downstream auto-aggregate
3. **Defer**: Target 3 (ComposioHQ) unless you add SKILL.md
4. **In 2-3 weeks**: Target 4 (VoltAgent) once Agent_skills has community traction

---

## 📋 Skipped (do NOT submit)

| Repo | Reason |
|---|---|
| `anantsharma67/awesome-opencode-skills` | 0 stars, abandoned |
| `jshsakura/awesome-opencode-skills` | Auto-port only, doesn't accept community PRs |
| `TheArchitectit/awesome-opencode-skills` | Last push Dec 2025 — abandoned |
| `ranbot-ai/awesome-skills` | 4 stars, no CONTRIBUTING.md, personal |
| `JasonxzWen/skill-hub` | 0 stars, no contribution model |
| `anomalyco/opencode` (the OpenCode main repo) | README doesn't list community skills — wrong target |

---

## 🛠️ PR etiquette (review before each submit)

- [ ] Look at the most recent **5 merged PRs** in the target repo — copy their style
- [ ] If repo has CONTRIBUTING.md, **read all of it** before submitting
- [ ] Use a fork, not direct branch
- [ ] One concern per PR — don't bundle multiple changes
- [ ] PR description: **what** + **why** + **proof** (working URL + verification)
- [ ] No marketing language ("the best", "revolutionary", "ultimate")
- [ ] Don't tag maintainers unless they explicitly ask
- [ ] If declined, close politely. Don't argue.
- [ ] One repo per week. Don't shotgun the ecosystem.

---

## 🌱 Non-PR promotion paths

If PR route is too uncertain or you want broader reach:

| Channel | Effort | Audience | When |
|---|---|---|---|
| Dev.to / Medium long-form post | 2-3h | English devs | After PR #1 lands |
| Hacker News Show HN | 1h | Tech generalists | Tuesday-Thursday morning PT |
| anomalyco/opencode Discussions | 30min | OpenCode core users | After PR #1 lands |
| 小红书技术分享笔记 | 1h | 中文 dev 社区 | Anytime |
| X / Mastodon thread | 30min | Mixed | After v1.0 + screenshot |
| Reddit r/ClaudeAI | 1h | Anthropic ecosystem | Weekend |

Top suggestion: **Tuesday morning HN post + Dev.to long-form same day**, threading them together. Both link to handbook + repo.

---

## 📝 General PR body template (reusable)

```markdown
Adds [Skills Manager AI Agent](https://github.com/zjgulai/Agent_skills) — an OpenCode skills lifecycle layer.

If you have 3+ skills installed in `~/.config/opencode/skills/`, this gives you 11 slash commands covering install / uninstall / update / classify / doctor / recommend / graph-sync / portal-control.

**Highlights:**
- One-command install: `/skill-install <github_url>` runs end-to-end in ~30s (clone → infer 6-domain classification → update INDEX.md → add graph node → re-render PNG → refresh portal)
- 5-rule health check across every installed skill via `/skill-doctor`
- Task-to-skills recommendation: free-form description → `load_skills=[...]` suggestion
- Local FastAPI + Vue portal (UI on :5173, REST on :5174)
- Bilingual docs (EN + 中文) at https://zjgulai.github.io/Agent_skills/handbook.html
- v1.0.0 released, MIT licensed

End-to-end verified by installing two real skills:
- `op7418/guizang-ppt-skill` (auto-classified into `tooling`)
- `anthropics/skills/skills/skill-creator` (uncategorized → manual classify into `meta`)

Both passed all 5 doctor rules; graph rendered correctly through both transitions.
```
