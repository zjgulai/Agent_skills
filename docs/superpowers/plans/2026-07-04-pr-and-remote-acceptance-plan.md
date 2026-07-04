# PR And Remote Acceptance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use github:yeet for PR publication and superpowers:verification-before-completion for final status claims. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Open a reviewable GitHub draft PR for the verified Agent_skills release branch and inspect remote checks without performing a Tencent Cloud production publish.

**Architecture:** Keep `codex/agent-skills-console-release` as the review branch. Add this plan as a small fourth commit, push it, create a draft PR into `main`, then read GitHub PR metadata and check status through `gh`.

**Tech Stack:** Git, GitHub CLI, pytest, static docs builder, Tencent static dry-run, CodeGraph.

---

## Safety Boundary

- This plan may push the existing feature branch.
- This plan may create a GitHub draft PR.
- This plan must not push directly to `main`.
- This plan must not run `bin/deploy-tencent-static --apply`.
- Tencent Cloud production publish remains blocked until a target host/path and publish window are explicitly confirmed.

## TODO List

### Task 1: Add Plan Commit

**Files:**
- Create: `docs/superpowers/plans/2026-07-04-pr-and-remote-acceptance-plan.md`

- [x] **Step 1: Verify current branch**

Run:

```bash
git status --short --branch
```

Expected: on `codex/agent-skills-console-release`; no unrelated dirty files except this plan before committing.

- [x] **Step 2: Commit this plan**

Run:

```bash
git add docs/superpowers/plans/2026-07-04-pr-and-remote-acceptance-plan.md
git commit -m "docs: add pr acceptance plan"
```

Expected: one small docs commit.

### Task 2: Local PR Gate

**Files:** none.

- [x] **Step 1: Run full test suite**

Run:

```bash
portal/backend/.venv/bin/python -m pytest -q
```

Expected: `107 passed`.

- [x] **Step 2: Run static publish dry-run and integrity checks**

Run:

```bash
bin/deploy-tencent-static --target /tmp/agent-skills-tencent-smoke/ --dry-run
git diff --check
portal/backend/.venv/bin/python -m agent.lib.state_audit --check --metadata-only
```

Expected: dry-run only; whitespace clean; `state audit drift=false`.

### Task 3: Push Branch

**Files:** none.

- [ ] **Step 1: Push branch**

Run:

```bash
git push
```

Expected: `codex/agent-skills-console-release` updated on origin.

### Task 4: Create Draft PR

**Files:** none.

- [ ] **Step 1: Confirm no existing PR**

Run:

```bash
gh pr view --json number,url,state,headRefName,baseRefName
```

Expected: no PR yet, or return the existing PR if another process created it.

- [ ] **Step 2: Create draft PR**

Run:

```bash
gh pr create --draft --base main --head codex/agent-skills-console-release \
  --title "[codex] Redesign skills operating console and static publish gates" \
  --body "<PR body>"
```

Expected: GitHub returns the PR URL.

### Task 5: Remote Acceptance

**Files:** none.

- [ ] **Step 1: Read PR metadata**

Run:

```bash
gh pr view --json number,title,state,url,isDraft,mergeable,headRefName,baseRefName,statusCheckRollup
```

Expected: PR is draft, head is `codex/agent-skills-console-release`, base is `main`.

- [ ] **Step 2: Read checks**

Run:

```bash
gh pr checks --watch=false
```

Expected: report check state. If checks are pending or absent, report that explicitly rather than treating it as a pass.
