# Skills Operating Console Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reorganize the static website from a broad skills navigator into a product-grade Skills Operating Console that explains current capabilities, source provenance, workflow coverage, and deployment readiness.

**Architecture:** Keep `docs/_src/originals/index.html` as the source template and `docs/_src/build.py` as the generator for source-driven sections. Add focused data and UI contracts in tests before changing the site. Generated files under `docs/zh`, `docs/en`, and `docs/data` must be rebuilt through `bin/deploy-docs`.

**Tech Stack:** Static HTML/CSS/JS, BeautifulSoup docs builder, JSON data files, pytest, Playwright CLI, `bin/deploy-docs`, `bin/deploy-tencent-static`.

---

## Product Brief

The site should behave like a management console for the current product shape:

- 227 installed skills.
- 50 problem workflow nodes from idea discovery to launch, growth, operations, IP, and retrospective learning.
- Alchaincyf source collection with 43 runtime installs, distill-only backlog, skip reasons, root/subdir/monorepo install modes, and source provenance.
- Static publishing path for Tencent Cloud lightweight server; no public FastAPI/Vite dependency.

The first viewport should be an operational console, not a marketing hero. It should answer:

1. What can this skills system do now?
2. Which problem workflow node should I start from?
3. Which skills were newly sourced and how were they installed?
4. Is the site ready to publish?

## Design Direction

- Keep the existing light, restrained, utilitarian style.
- Replace the oversized hero with dense status + workflow + source intake panels.
- Add a visible "capability map" that groups skills by user problem, not by repository name.
- Keep cards at 8px radius or less and avoid decorative gradients/orbs.
- Use the existing static data and graph assets; do not introduce external CDN dependencies.

## Change Groups

- **Group A: Current dirty tree audit**: document that the worktree contains previous Alchaincyf ingestion, website, docs, deploy wrapper, and generated-file changes. Do not revert unrelated changes.
- **Group B: Website source changes**: source template, builder, homepage tests.
- **Group C: Generated artifacts**: docs data, localized pages, graph image copies after `bin/deploy-docs`.
- **Group D: Verification**: pytest, state audit, Tencent dry-run, Playwright browser smoke.

## TODO List

### Task 1: Add Homepage Product Console Contracts

**Files:**
- Modify: `tests/test_docs_homepage_contract.py`

- [x] **Step 1: Add failing contract for console-first homepage**

Expected checks:

```python
def test_homepage_exposes_operating_console_sections():
    zh = _soup(DOCS / "zh" / "index.html")
    html = str(zh)

    for required_id in [
        "operating-console",
        "capability-map",
        "source-ledger",
        "publish-readiness",
    ]:
        assert zh.find(id=required_id), f"missing #{required_id}"

    assert "Skills Operating Console" in html or "Skills 运营控制台" in html
    assert "227" in html
    assert "50" in html
    assert "43" in html
```

- [x] **Step 2: Add failing contract for source provenance content**

Expected checks:

```python
def test_homepage_exposes_source_provenance_and_workflow_coverage():
    zh = _soup(DOCS / "zh" / "index.html")
    html = str(zh)

    assert "root / subdir / monorepo" in html
    assert "distill-only" in html
    assert "source.alchaincyf-intake" in html
    assert "agentops.skill-generation-optimization" in html
    assert "design.html-native-production" in html
```

- [x] **Step 3: Run focused tests and confirm RED**

Run:

```bash
portal/backend/.venv/bin/python -m pytest tests/test_docs_homepage_contract.py -q
```

Expected: fail because new sections do not exist yet.

### Task 2: Restructure Homepage Source Template

**Files:**
- Modify: `docs/_src/originals/index.html`

- [x] **Step 1: Replace first viewport with operating console**

Add these source sections:

- `#operating-console`: status metrics, workflow triage, source intake, publish readiness.
- `#capability-map`: stage groups from idea to retrospective.
- `#source-ledger`: source provenance, install modes, top problem-node coverage.
- `#publish-readiness`: build/test/deploy gates and static publish boundary.

- [x] **Step 2: Update copy dictionary**

Add Chinese and English copy keys for the new console. Keep existing keys when still used by other sections.

- [x] **Step 3: Keep existing explorer sections**

Preserve:

- `#skill-explorer`
- `#workflow-explorer`
- `#domain-overview`
- `#graph-overview`
- `#tencent-deploy`

### Task 3: Add Data-Driven Console Rendering

**Files:**
- Modify: `docs/_src/build.py`
- Modify: `docs/_src/originals/index.html`

- [x] **Step 1: Extend existing Alchaincyf manifest rendering**

Render source ledger fields:

- source owner and repo counts
- runtime install count
- direct root, subdir, monorepo counts
- distill-only and skip counts
- top problem nodes

- [x] **Step 2: Add static console metrics from available data**

The browser should render:

- `data-stat="skills"` from `skills.json`
- `data-stat="nodes"` from `problem-workflows.json`
- `data-stat="source-runtime"` from `alchaincyf-skill-manifest.json`
- `data-stat="publish-state"` as `Ready`

- [x] **Step 3: Fetch manifest in homepage JS**

Update homepage `init()` to load:

```js
fetchJson("../data/alchaincyf-skill-manifest.json")
```

and store it in `state.sourceManifest`.

### Task 4: Improve Skill and Workflow Interaction

**Files:**
- Modify: `docs/_src/originals/index.html`

- [x] **Step 1: Add workflow quick-entry controls**

From the console, quick buttons should set `state.stage` or `state.node`, scroll to the explorer, and re-render results.

- [x] **Step 2: Add source skill filter**

Source ledger buttons should filter to Alchaincyf runtime skills by runtime names from the manifest.

- [x] **Step 3: Add skill card source badge**

When a skill is from the Alchaincyf manifest, show a small source badge in the card.

### Task 5: Rebuild Docs and Run Tests

**Files:**
- Generated: `docs/data/*`, `docs/zh/index.html`, `docs/en/index.html`, root redirects as needed.

- [x] **Step 1: Run docs build**

Run:

```bash
bin/deploy-docs
```

Expected:

- `docs/data/skills.json` has 227 skills.
- `docs/data/problem-workflows.json` has 50 nodes.
- `state audit drift=false`.

- [x] **Step 2: Run focused and full tests**

Run:

```bash
portal/backend/.venv/bin/python -m pytest tests/test_docs_homepage_contract.py tests/test_problem_workflows.py tests/test_tencent_static_publish.py -q
portal/backend/.venv/bin/python -m pytest -q
```

Expected: all pass.

- [x] **Step 3: Run Tencent dry-run**

Run:

```bash
bin/deploy-tencent-static --target /tmp/agent-skills-tencent-smoke/ --dry-run
```

Expected: dry-run only; no `docs/_src/`, `docs/superpowers/`, `__pycache__/`, or `*.pyc` in transfer list.

### Task 6: Browser Acceptance and Commit Boundary

**Files:**
- Runtime artifact: `output/playwright/skills-operating-console-mobile.png`

- [x] **Step 1: Start local static server**

Run:

```bash
portal/backend/.venv/bin/python -m http.server 4187 --bind 127.0.0.1 --directory docs
```

- [x] **Step 2: Verify desktop and mobile homepage**

Use Playwright to verify:

- `#operating-console`, `#capability-map`, `#source-ledger`, `#publish-readiness` exist.
- 227 skill cards render.
- source runtime count is 43.
- console errors/warnings are 0.
- horizontal overflow is 0 at desktop and 390px mobile.

- [x] **Step 3: Stop local server and confirm port release**

Run:

```bash
lsof -ti:4187 || true
```

Expected: no output.

- [x] **Step 4: Final verification**

Run:

```bash
git diff --check
portal/backend/.venv/bin/python -m agent.lib.state_audit --check --metadata-only
PATH="/Users/lute/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH" codegraph sync
PATH="/Users/lute/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH" codegraph status
```

Expected: clean whitespace, `drift=false`, CodeGraph index up to date.

## Commit Plan

After browser acceptance, create grouped commits only if the user still wants commit/push in this same branch:

1. `feat: ingest alchaincyf skills and workflow manifest`
2. `feat: redesign skills operating console`
3. `test: add source ingestion and homepage contracts`

Do not push to Tencent with `--apply` unless the user provides the real target and explicitly confirms publish.
