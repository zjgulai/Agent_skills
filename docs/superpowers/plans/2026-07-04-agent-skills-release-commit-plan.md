# Agent Skills Release Commit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the verified Alchaincyf ingestion, workflow taxonomy, Tencent static deploy hardening, and Skills Operating Console redesign into reviewable commits without doing a real Tencent publish.

**Architecture:** Keep the current working tree intact, create a `codex/` work branch from `main`, then stage changes into three functional commits. Verification runs before and after commits; Tencent deploy remains dry-run only unless an explicit `--apply` target is confirmed later.

**Tech Stack:** Git, pytest, static docs builder, Tencent dry-run deploy wrapper, Playwright evidence artifact, CodeGraph.

---

## Risk And Rollback

- Risk: committing directly on `main` would make it harder to review or undo the large generated-site update.
- Mitigation: switch to `codex/agent-skills-console-release` before committing.
- Rollback before push: `git reset --soft HEAD~N` on the feature branch, or create a new branch from `main` and leave the current branch untouched.
- Rollback after push: revert the specific commit(s) on the feature branch or open a PR for review instead of merging.
- Out of scope: no `bin/deploy-tencent-static --apply`; only `--dry-run`.

## TODO List

### Task 1: Create Branch And Baseline

**Files:** none.

- [x] **Step 1: Create/switch branch**

Run:

```bash
git switch -c codex/agent-skills-console-release
```

If the branch already exists, run:

```bash
git switch codex/agent-skills-console-release
```

- [x] **Step 2: Verify branch and dirty tree**

Run:

```bash
git rev-parse --abbrev-ref HEAD
git status --short
```

Expected: branch is `codex/agent-skills-console-release`; dirty tree is preserved.

### Task 2: Run Commit-Gate Verification

**Files:** none.

- [x] **Step 1: Rebuild static docs**

Run:

```bash
bin/deploy-docs
```

Expected: `skill_count=227`, `console=4` on both homepages, `state audit drift=false`.

- [x] **Step 2: Run tests and publish dry-run**

Run:

```bash
portal/backend/.venv/bin/python -m pytest -q
bin/deploy-tencent-static --target /tmp/agent-skills-tencent-smoke/ --dry-run
git diff --check
```

Expected: all tests pass; dry-run excludes source/private folders; whitespace check is clean.

### Task 3: Commit Alchaincyf Ingestion And Workflow Manifest

**Files:**
- Stage: `agent/docs/domain-taxonomy.md`
- Stage: `agent/docs/problem-workflow-taxonomy.md`
- Stage: `agent/docs/source-digests/`
- Stage: `agent/lib/domain_inference.py`
- Stage: `agent/lib/graph_writer.py`
- Stage: `data-mirror/INDEX.md`
- Stage: `data-mirror/skills-graph.mmd`
- Stage: `data-mirror/skills-graph.png`
- Stage: `docs/_src/alchaincyf-skill-manifest.json`
- Stage: `docs/_src/problem-workflows.json`
- Stage: `docs/data/alchaincyf-skill-manifest.json`
- Stage: `docs/data/problem-workflows.json`
- Stage: `docs/data/domains.json`
- Stage: `docs/data/skills.json`
- Stage: `docs/assets/skills-graph.png`
- Stage: `tests/test_alchaincyf_ingestion_contract.py`
- Stage: `tests/test_alchaincyf_skill_manifest.py`
- Stage: `tests/test_domain_inference.py`
- Stage: `tests/test_graph_writer.py`
- Stage: `tests/test_problem_workflows.py`

- [x] **Step 1: Stage ingestion/workflow files**

Run:

```bash
git add agent/docs/domain-taxonomy.md agent/docs/problem-workflow-taxonomy.md agent/docs/source-digests \
  agent/lib/domain_inference.py agent/lib/graph_writer.py \
  data-mirror/INDEX.md data-mirror/skills-graph.mmd data-mirror/skills-graph.png \
  docs/_src/alchaincyf-skill-manifest.json docs/_src/problem-workflows.json \
  docs/data/alchaincyf-skill-manifest.json docs/data/problem-workflows.json docs/data/domains.json docs/data/skills.json \
  docs/assets/skills-graph.png \
  tests/test_alchaincyf_ingestion_contract.py tests/test_alchaincyf_skill_manifest.py tests/test_domain_inference.py tests/test_graph_writer.py tests/test_problem_workflows.py
```

- [x] **Step 2: Commit ingestion/workflow files**

Run:

```bash
git commit -m "feat: ingest alchaincyf skills and workflow manifest"
```

### Task 4: Commit Website Operating Console Redesign

**Files:**
- Stage: `docs/_src/build.py`
- Stage: `docs/_src/originals/index.html`
- Stage: `docs/en/index.html`
- Stage: `docs/zh/index.html`
- Stage: `docs/data/portal-status.json`
- Stage: `tests/test_docs_homepage_contract.py`
- Stage: `docs/superpowers/plans/2026-07-04-skills-operating-console-redesign.md`
- Stage: `docs/superpowers/plans/2026-07-04-agent-skills-release-commit-plan.md`

- [x] **Step 1: Stage console redesign files**

Run:

```bash
git add docs/_src/build.py docs/_src/originals/index.html docs/en/index.html docs/zh/index.html \
  docs/data/portal-status.json tests/test_docs_homepage_contract.py \
  docs/superpowers/plans/2026-07-04-skills-operating-console-redesign.md docs/superpowers/plans/2026-07-04-agent-skills-release-commit-plan.md
```

- [x] **Step 2: Commit console redesign files**

Run:

```bash
git commit -m "feat: redesign skills operating console"
```

### Task 5: Commit Tencent Static Publish And Docs Hardening

**Files:**
- Stage: `.gitignore`
- Stage: `agent/lib/doctor.py`
- Stage: `agent/lib/state_audit.py`
- Stage: `bin/deploy-tencent-static`
- Stage: `docs/_src/README.md`
- Stage: `docs/_src/data-collect.py`
- Stage: `docs/_src/i18n/zh.json`
- Stage: `docs/_src/originals/architecture.html`
- Stage: `docs/_src/originals/getting-started.html`
- Stage: `docs/_src/originals/handbook.html`
- Stage: `docs/_src/weekly-hot-skills.json`
- Stage: `docs/assets/favicon.svg`
- Stage: `docs/assets/vendor/`
- Stage: `docs/architecture.html`
- Stage: `docs/case-study.html`
- Stage: `docs/commands.html`
- Stage: `docs/data/weekly-hot-skills.json`
- Stage: `docs/domains.html`
- Stage: `docs/en/architecture.html`
- Stage: `docs/en/getting-started.html`
- Stage: `docs/en/handbook.html`
- Stage: `docs/getting-started.html`
- Stage: `docs/handbook.html`
- Stage: `docs/tencent-light-server-deploy.md`
- Stage: `docs/zh/architecture.html`
- Stage: `docs/zh/getting-started.html`
- Stage: `docs/zh/handbook.html`
- Stage: `portal/README.md`
- Stage: `portal/backend/build_index.py`
- Stage: `tests/test_docs_hot_skills.py`
- Stage: `tests/test_installer_security.py`
- Stage: `tests/test_state_audit.py`
- Stage: `tests/test_tencent_static_publish.py`

- [ ] **Step 1: Stage deploy/docs hardening files**

Run:

```bash
git add .gitignore agent/lib/doctor.py agent/lib/state_audit.py bin/deploy-tencent-static \
  docs/_src/README.md docs/_src/data-collect.py docs/_src/i18n/zh.json \
  docs/_src/originals/architecture.html docs/_src/originals/getting-started.html docs/_src/originals/handbook.html docs/_src/weekly-hot-skills.json \
  docs/assets/favicon.svg docs/assets/vendor docs/architecture.html docs/case-study.html docs/commands.html docs/data/weekly-hot-skills.json docs/domains.html \
  docs/en/architecture.html docs/en/getting-started.html docs/en/handbook.html docs/getting-started.html docs/handbook.html docs/tencent-light-server-deploy.md \
  docs/zh/architecture.html docs/zh/getting-started.html docs/zh/handbook.html \
  portal/README.md portal/backend/build_index.py \
  tests/test_docs_hot_skills.py tests/test_installer_security.py tests/test_state_audit.py tests/test_tencent_static_publish.py
```

- [ ] **Step 2: Commit deploy/docs hardening files**

Run:

```bash
git commit -m "test: add static publish and docs hardening contracts"
```

### Task 6: Final Verification And Push Decision

**Files:** none.

- [ ] **Step 1: Run final checks**

Run:

```bash
portal/backend/.venv/bin/python -m pytest -q
bin/deploy-tencent-static --target /tmp/agent-skills-tencent-smoke/ --dry-run
git diff --check
portal/backend/.venv/bin/python -m agent.lib.state_audit --check --metadata-only
PATH="/Users/lute/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH" codegraph index -f
PATH="/Users/lute/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH" codegraph status
```

Expected: tests pass, dry-run safe, whitespace clean, audit clean, CodeGraph index up to date.

- [ ] **Step 2: Push feature branch if final checks pass**

Run:

```bash
git push -u origin codex/agent-skills-console-release
```

Expected: branch pushed for review. Do not push `main` directly.
