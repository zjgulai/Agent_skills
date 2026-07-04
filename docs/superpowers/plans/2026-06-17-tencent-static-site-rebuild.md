# Tencent Static Site Rebuild Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the public docs website into a Tencent-light-server-ready skills navigator where every skill has a clear function, problem focus, category, and graph/workflow context.

**Architecture:** Keep `docs/_src/` as the source and `docs/` as generated static output. Fix the build pipeline so localized pages link to localized pages, root legacy pages redirect instead of serving stale content, and the homepage becomes a data-driven static app that reads `docs/data/*.json` without a backend.

**Tech Stack:** Static HTML/CSS/JavaScript, Python 3.14-compatible BeautifulSoup build step, JSON data generated from `data-mirror/INDEX.md`, pytest, local HTTP smoke tests.

---

### Task 1: Audit and Build Contract

**Files:**
- Modify: `docs/_src/build.py`
- Modify: `tests/test_docs_deploy_contract.py`
- Create: `tests/test_docs_homepage_contract.py`

- [ ] **Step 1: Add tests for localized links and stale root redirects**

Add assertions that generated `docs/zh/index.html` and `docs/en/index.html` keep links such as `./handbook.html`, while root `docs/handbook.html` redirects to the localized build instead of serving stale content.

- [ ] **Step 2: Fix path rewriting**

Change `fix_relative_paths()` so page links stay language-local and only asset/data/script/image paths receive `../` prefixes.

- [ ] **Step 3: Generate root legacy redirects**

Generate redirect wrappers for legacy root pages: `handbook.html`, `getting-started.html`, `architecture.html`, `domains.html`, `commands.html`, and `case-study.html`.

### Task 2: Homepage Product Rebuild

**Files:**
- Replace: `docs/_src/originals/index.html`
- Modify: `docs/_src/build.py`
- Modify: `tests/test_docs_homepage_contract.py`

- [ ] **Step 1: Replace marketing homepage with skills navigator**

The first screen should show current skill count, domain count, problem-node count, and clear entry points: search skills, browse workflows, inspect graph, and deploy static site.

- [ ] **Step 2: Add data-driven skill explorer**

Client-side JavaScript loads `../data/skills.json`, `../data/domains.json`, and `../data/problem-workflows.json`. Users can search by name/function/trigger/problem node, filter by domain, filter by workflow stage, and copy `task(load_skills=[...])`.

- [ ] **Step 3: Add workflow and domain sections**

Render workflow stage cards, problem-node details, domain cards, and a graph overview that links to `../assets/skills-graph.png`.

- [ ] **Step 4: Keep weekly radar and docs links**

Render the weekly radar with local CSS classes and preserve links to the generated JSON.

### Task 3: Tencent Deployment Notes

**Files:**
- Create: `docs/tencent-light-server-deploy.md`
- Modify: `docs/_src/README.md`

- [ ] **Step 1: Document static deployment contract**

Explain the generated artifact boundary: deploy `docs/` as static files, no portal backend required.

- [ ] **Step 2: Add nginx example**

Include a minimal nginx server block for `/`, immutable assets, JSON cache behavior, and fallback to `index.html`.

### Task 4: Verification

**Files:**
- Test: `tests/test_docs_homepage_contract.py`
- Test: existing docs/build/state tests

- [ ] **Step 1: Rebuild docs**

Run `bin/deploy-docs`.

- [ ] **Step 2: Run tests**

Run focused docs tests and full `pytest -q`.

- [ ] **Step 3: Browser-style smoke**

Serve `docs/` over local HTTP and verify `zh/index.html`, `en/index.html`, `data/*.json`, and graph image resolve with 200 responses.

- [ ] **Step 4: Final release checks**

Run `git diff --check`, `state_audit --check --metadata-only`, and `codegraph sync && codegraph status`.
