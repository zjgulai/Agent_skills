# Alchaincyf Skills Ingestion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Distill, deduplicate, ingest, categorize, publish, and optionally Tencent-deploy the core skills from `https://github.com/alchaincyf` into Skills Manager AI Agent.

**Architecture:** Treat `alchaincyf` as an upstream source registry, not as a blind bulk install. Direct `SKILL.md` repositories are installed through the existing portal API; multi-skill repositories use the existing monorepo install API; non-skill books/apps are distilled into future candidate records only after source review. The public docs site remains the presentation layer: every ingested skill must show function, solved problem, domain, workflow node, and graph position.

**Tech Stack:** GitHub CLI/API, FastAPI portal API (`/api/install/github`, `/api/install/github/monorepo`, `/api/refresh`), `agent/lib/portal_client.py`, `agent/lib/index_md_writer.py`, `agent/lib/graph_writer.py`, `agent/lib/state_audit.py`, `bin/deploy-docs`, `bin/deploy-tencent-static`, pytest, Playwright smoke.

## First-Principles Execution Frame

The project is not a mirror of GitHub repositories. It is a management and publishing layer for skills. Therefore every execution step must preserve four invariants:

1. **Source truth before runtime mutation.** A repository can only become a runtime skill after it is represented in a manifest with source URL, install mode, workflow node, problem node, and domain.
2. **Problem orientation before collection size.** Classification answers "what user problem does this solve in the AI automation workflow?", not "which celebrity/tool/topic is this named after?".
3. **Portal API before filesystem writes.** Skill content under `~/.config/opencode/skills/<name>/` is modified only by the portal install APIs; direct writes are limited to approved metadata files with backups.
4. **Evidence before publish.** Each stage must leave a test, audit, dry-run, or browser screenshot proving the site and metadata still agree.

Execution order:

- **Discover and freeze:** build a stable upstream manifest and source digest.
- **Contract and compatibility:** prove root, subdir, monorepo, distill-only, and skip modes are explicit.
- **Install and classify:** run portal installs only after backups and duplicate checks.
- **Publish and verify:** rebuild docs, verify state drift, run Tencent dry-run, then browser-smoke the website.

Checkpoint rule: update this TODO list as each task finishes, and stop before any real external publish or push unless the user explicitly requests that action.

---

## Source Snapshot

Collected on 2026-07-04 from GitHub:

- Public repositories: 70
- Non-fork repositories: 46
- Fork repositories: 24
- Direct root `SKILL.md` candidates sampled: `huashu-design`, `nuwa-skill`, `darwin-skill`, `huashu-md-html`, `huashu-slide-codex`, `huashu-weread`, `x-mentor-skill`, `freud-skill`, persona skills such as `munger-skill`, `feynman-skill`, `karpathy-skill`, `steve-jobs-skill`
- Multi-skill repository: `huashu-skills`, with 22 nested `SKILL.md` files
- Nested skill repository: `dukou`, with `skill/dukou/SKILL.md`
- Product/app/book repositories that are not direct skills: `fanbox`, `huasheng_editor`, orange-book repositories, `img2046`, `nes-arcade`, and forks

## Product Fit

This project is a skills management and publishing system:

- `portal/` installs and indexes skills.
- `agent/lib/` updates INDEX/graph/state.
- `docs/` publishes the problem-oriented public website.
- `bin/deploy-docs` rebuilds local docs.
- `bin/deploy-tencent-static` safely publishes the static site, dry-run first.

The ingestion must therefore produce three surfaces:

1. Runtime skills installed under `~/.config/opencode/skills/`.
2. Metadata truth in `INDEX.md`, `skills-graph.mmd`, `skills-graph.png`, and generated docs data.
3. Public website clarity: each skill has a concrete problem, workflow node, category, and graph placement.

## Source Classification

### Tier A: Direct Core Install

Install through `POST /api/install/github`, then classify and graph:

- `alchaincyf/huashu-design` -> HTML-native design, prototypes, slides, animation, expert review
- `alchaincyf/nuwa-skill` -> distill people/thinking frameworks into runnable skills
- `alchaincyf/darwin-skill` -> skill evaluation and autonomous optimization
- `alchaincyf/huashu-md-html` -> markdown/html/docx conversion and visual publishing pipeline
- `alchaincyf/huashu-slide-codex` -> Codex image_gen visual asset and deck production
- `alchaincyf/huashu-weread` -> WeRead advisory workflows over shelf/notes
- `alchaincyf/x-mentor-skill` -> X/Twitter content growth mentor
- `alchaincyf/freud-skill` -> prompt/skill/agent cognitive diagnosis and tuning
- `alchaincyf/dukou`, subdir `skill/dukou` -> article bridge to X Articles, Bilibili columns, WeChat editor

### Tier B: Direct Monorepo Batch

Install through `POST /api/install/github/monorepo` from `alchaincyf/huashu-skills`.

Known nested skill paths:

- `huashu-agent-swarm/SKILL.md`
- `huashu-article-edit/SKILL.md`
- `huashu-article-to-x/SKILL.md`
- `huashu-data-pro/SKILL.md`
- `huashu-design/SKILL.md`
- `huashu-douyin-script/SKILL.md`
- `huashu-image-upload/SKILL.md`
- `huashu-info-search/SKILL.md`
- `huashu-material-search/SKILL.md`
- `huashu-md-to-pdf/SKILL.md`
- `huashu-prompt-save/SKILL.md`
- `huashu-proofreading/SKILL.md`
- `huashu-research/SKILL.md`
- `huashu-script-polish/SKILL.md`
- `huashu-slides/SKILL.md`
- `huashu-speech-coach/SKILL.md`
- `huashu-topic-gen/SKILL.md`
- `huashu-video-check/SKILL.md`
- `huashu-video-outline/SKILL.md`
- `huashu-wechat-image/SKILL.md`
- `huashu-xhs-image/SKILL.md`

Dedup rule: skip `huashu-skills/huashu-design` if standalone `alchaincyf/huashu-design` is installed, because the standalone repository is the canonical high-star, actively updated version.

### Tier C: Persona / Thinking Framework Skills

Install after dependency and license review; classify under problem nodes instead of leaving them as a flat celebrity list:

- Strategy and judgment: `munger-skill`, `taleb-skill`, `paul-graham-skill`, `naval-skill`, `zhang-yiming-skill`
- Product and creative judgment: `steve-jobs-skill`, `elon-musk-skill`, `karpathy-skill`, `feynman-skill`
- Education/career/content: `zhangxuefeng-skill`, `mrbeast-skill`, `x-mentor-skill`
- Power/attention analysis: `trump-skill`, `sun-yuchen-perspective`
- AI/research cognition: `ilya-sutskever-skill`

### Tier D: Distill-Only Candidates

Do not install directly. Create source digest records first:

- Orange books: `loop-engineering-orange-book`, `hermes-agent-orange-book`, `codex-orange-book`, `agent-skills-orange-book`, `harness-engineering-orange-book`, `claude-code-orange-book`, `claude-code-source-analysis-orange-book`, `openclaw-orange-book`, `obsidian-ai-orange-book`, `polymarket-orange-book`
- Product/app repositories: `fanbox`, `dukou` app surface, `huasheng_editor`, `img2046`, `nes-arcade`
- Forks: skip for runtime install unless a fork contains unique author-authored skill content

## Workflow Taxonomy Mapping

Use the project’s problem-oriented lifecycle:

- `00-source-intake`: source inventory, license, direct skill detection
- `01-sensemaking`: research, info search, material search, reading, WeRead
- `02-strategy-judgment`: persona thinking skills, founder/product strategy, decision quality
- `03-content-planning`: topic generation, video outline, X/Twitter strategy, Douyin scripts
- `04-design-production`: huashu-design, slides, image, md/html/pdf, visual assets
- `05-quality-review`: proofreading, article editing, script polish, speech coaching, Freud diagnosis
- `06-distribution`: article-to-X, image upload, Dukou publishing bridge
- `07-agent-ops`: Nuwa skill generation, Darwin optimization, agent swarm
- `08-closeout-publish`: docs rebuild, graph sync, Tencent static dry-run/apply

## Domain Mapping

- `meta`: `huashu-nuwa`, `darwin-skill`, `huashu-agent-swarm`, `freud-skill`
- `tooling`: content production, design, conversion, search, publishing, visual generation, data workflows
- `founder`: strategic/persona skills when primarily used for product, market, creator growth, career or business judgment
- `closeout`: quality/review skills when framed as launch gates or final publishing checks
- `desktop`: no direct install yet; `fanbox` is a product source digest only
- `ip`: no direct install from this batch

## Risk Controls

- Do not write into `~/.config/opencode/skills/<name>/` directly.
- Install/uninstall must go through portal API.
- Before metadata writes, `index_md_writer` must back up `INDEX.md`.
- Use dry-run inventory before installation.
- Use overwrite only after duplicate analysis.
- Treat API keys, browser cookies, WeChat/WeRead state, and publishing credentials as user-private.
- For real Tencent deploy, run `bin/deploy-tencent-static --dry-run` before `--apply`.

## Target Files

- Create: `agent/docs/source-digests/2026-07-04-alchaincyf-repo-inventory.md`
- Create: `docs/_src/alchaincyf-skill-manifest.json`
- Create: `tests/test_alchaincyf_skill_manifest.py`
- Create: `tests/test_alchaincyf_ingestion_contract.py`
- Modify: `docs/_src/problem-workflows.json`
- Modify: `docs/_src/build.py`
- Modify: `docs/_src/originals/index.html`
- Modify: `agent/lib/domain_inference.py`
- Modify: `agent/docs/domain-taxonomy.md`
- Modify: `docs/tencent-light-server-deploy.md`
- Optional create after plan approval: `bin/ingest-alchaincyf-skills`

---

## TODO List

### Task 1: Freeze Source Inventory

**Files:**
- Create: `agent/docs/source-digests/2026-07-04-alchaincyf-repo-inventory.md`
- Create: `docs/_src/alchaincyf-skill-manifest.json`
- Test: `tests/test_alchaincyf_skill_manifest.py`

- [x] **Step 1: Write failing manifest schema test**

```python
from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = REPO_ROOT / "docs" / "_src" / "alchaincyf-skill-manifest.json"


def test_alchaincyf_manifest_has_unique_runtime_names():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    names = [item["runtime_name"] for item in data["skills"] if item["action"] == "install"]
    assert len(names) == len(set(names))


def test_alchaincyf_manifest_records_source_and_install_mode():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for item in data["skills"]:
        assert item["repo"].startswith("https://github.com/alchaincyf/")
        assert item["action"] in {"install", "distill-only", "skip"}
        assert item["install_mode"] in {"root", "subdir", "monorepo", "none"}
        assert item["domain"] in {"meta", "closeout", "desktop", "founder", "ip", "tooling"}
        assert item["workflow_stage"]
        assert item["problem_node"]
```

- [x] **Step 2: Run the test and confirm it fails**

Run:

```bash
portal/backend/.venv/bin/python -m pytest tests/test_alchaincyf_skill_manifest.py -q
```

Expected: fail because the manifest file does not exist.

- [x] **Step 3: Create the manifest**

Minimum manifest root:

```json
{
  "source_owner": "alchaincyf",
  "snapshot_date": "2026-07-04",
  "repo_count": 70,
  "non_fork_count": 46,
  "fork_count": 24,
  "skills": []
}
```

Add one object per Tier A/Tier B/Tier C/Tier D record. Use `runtime_name` from frontmatter when available.

- [x] **Step 4: Run the test and confirm it passes**

Run:

```bash
portal/backend/.venv/bin/python -m pytest tests/test_alchaincyf_skill_manifest.py -q
```

Expected: pass.

### Task 2: Add Ingestion Contract Tests

**Files:**
- Create: `tests/test_alchaincyf_ingestion_contract.py`
- Modify: `docs/_src/alchaincyf-skill-manifest.json`

- [x] **Step 1: Write failing contract tests for direct and monorepo installs**

```python
from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = REPO_ROOT / "docs" / "_src" / "alchaincyf-skill-manifest.json"


def _data():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_manifest_marks_huashu_skills_as_monorepo():
    items = _data()["skills"]
    monorepo = [x for x in items if x["source_repo"] == "huashu-skills" and x["action"] == "install"]
    assert len(monorepo) >= 20
    assert all(x["install_mode"] == "monorepo" for x in monorepo)
    assert "huashu-skills/huashu-design" not in {x["source_key"] for x in monorepo}


def test_manifest_marks_dukou_as_subdir_install():
    items = _data()["skills"]
    dukou = next(x for x in items if x["runtime_name"] == "dukou")
    assert dukou["install_mode"] == "subdir"
    assert dukou["subdir"] == "skill/dukou"


def test_distill_only_repos_are_not_runtime_installs():
    items = _data()["skills"]
    orange_books = [x for x in items if x["source_repo"].endswith("orange-book")]
    assert orange_books
    assert all(x["action"] == "distill-only" for x in orange_books)
    assert all(x["install_mode"] == "none" for x in orange_books)
```

- [x] **Step 2: Run the test and confirm failure**

Run:

```bash
portal/backend/.venv/bin/python -m pytest tests/test_alchaincyf_ingestion_contract.py -q
```

Expected: fail until the manifest is filled.

- [x] **Step 3: Fill install-mode fields**

For each item:

- `root`: `POST /api/install/github` with no subdir
- `subdir`: `POST /api/install/github` with `subdir`
- `monorepo`: `POST /api/install/github/monorepo`
- `none`: no runtime install

- [x] **Step 4: Run focused tests**

Run:

```bash
portal/backend/.venv/bin/python -m pytest \
  tests/test_alchaincyf_skill_manifest.py \
  tests/test_alchaincyf_ingestion_contract.py -q
```

Expected: pass.

### Task 3: Dry-run Portal Compatibility

**Files:**
- Modify: `agent/docs/source-digests/2026-07-04-alchaincyf-repo-inventory.md`
- Optional create: `bin/ingest-alchaincyf-skills`

- [x] **Step 1: Start portal only if needed**

Run:

```bash
lsof -ti:5173,5174 || true
portal/backend/.venv/bin/python -m agent.lib.portal_client health
```

Expected: health ok or clear error requiring `portal/bin/start`.

- [x] **Step 2: Scan monorepo subdirs**

Run:

```bash
portal/backend/.venv/bin/python -m agent.lib.portal_client \
  scan https://github.com/alchaincyf/huashu-skills
```

Expected: output contains the Tier B subdirs except the skipped duplicate `huashu-design`.

- [x] **Step 3: Check one nested skill**

Run:

```bash
portal/backend/.venv/bin/python -m agent.lib.portal_client \
  install https://github.com/alchaincyf/dukou skill/dukou
```

Expected for plan dry-run phase: do not run this yet unless executing ingestion. Record that `dukou` requires `subdir=skill/dukou`.

Dry-run result: confirmed in manifest and source digest; no runtime install was performed during Task 3.

### Task 4: Runtime Install Batch

**Files:**
- Runtime API writes: `~/.config/opencode/skills/<name>/`
- Metadata writes: `~/.config/opencode/skills/INDEX.md`, `skills-graph.mmd`, `skills-graph.png`
- Modify: `data-mirror/`, `docs/data/`

- [x] **Step 1: Backup current state**

Run:

```bash
cp ~/.config/opencode/skills/INDEX.md ~/.config/opencode/skills/INDEX.md.bak.$(date +%Y%m%d%H%M%S)
cp ~/.config/opencode/skills/skills-graph.mmd ~/.config/opencode/skills/skills-graph.mmd.bak.$(date +%Y%m%d%H%M%S)
```

Expected: two timestamped backups exist.

- [x] **Step 2: Install Tier A direct root skills**

Use:

```bash
portal/backend/.venv/bin/python -m agent.lib.portal_client install https://github.com/alchaincyf/huashu-design
portal/backend/.venv/bin/python -m agent.lib.portal_client install https://github.com/alchaincyf/nuwa-skill
portal/backend/.venv/bin/python -m agent.lib.portal_client install https://github.com/alchaincyf/darwin-skill
portal/backend/.venv/bin/python -m agent.lib.portal_client install https://github.com/alchaincyf/huashu-md-html
portal/backend/.venv/bin/python -m agent.lib.portal_client install https://github.com/alchaincyf/huashu-slide-codex
portal/backend/.venv/bin/python -m agent.lib.portal_client install https://github.com/alchaincyf/huashu-weread
portal/backend/.venv/bin/python -m agent.lib.portal_client install https://github.com/alchaincyf/x-mentor-skill
portal/backend/.venv/bin/python -m agent.lib.portal_client install https://github.com/alchaincyf/freud-skill
```

Expected: each returns ok or duplicate/overwrite decision.

- [x] **Step 3: Install nested Dukou skill**

Run:

```bash
portal/backend/.venv/bin/python -m agent.lib.portal_client install https://github.com/alchaincyf/dukou skill/dukou
```

Expected: `dukou` installed.

- [x] **Step 4: Install Tier B monorepo skills**

Run with explicit subdir list from the manifest:

```bash
portal/backend/.venv/bin/python -m agent.lib.portal_client install-monorepo \
  https://github.com/alchaincyf/huashu-skills \
  huashu-agent-swarm \
  huashu-article-edit \
  huashu-article-to-x \
  huashu-data-pro \
  huashu-douyin-script \
  huashu-image-upload \
  huashu-info-search \
  huashu-material-search \
  huashu-md-to-pdf \
  huashu-prompt-save \
  huashu-proofreading \
  huashu-research \
  huashu-script-polish \
  huashu-slides \
  huashu-speech-coach \
  huashu-topic-gen \
  huashu-video-check \
  huashu-video-outline \
  huashu-wechat-image \
  huashu-xhs-image
```

Expected: all subdirs install or report explicit duplicates.

Runtime result: 43 manifest install candidates are present after refresh. Persona Tier C repositories installed as root skills in the same runtime batch; their actual runtime names use `*-perspective` frontmatter where applicable.

### Task 5: Metadata Classification and Graph Placement

**Files:**
- Modify: `agent/lib/domain_inference.py`
- Modify: `agent/docs/domain-taxonomy.md`
- Modify via tools: `~/.config/opencode/skills/INDEX.md`, `skills-graph.mmd`, `skills-graph.png`
- Test: `tests/test_domain_inference.py`, `tests/test_graph_writer.py`, `tests/test_index_md_idempotent.py`

- [x] **Step 1: Add domain inference regression examples**

Add cases:

```python
("huashu-nuwa", "自动深度调研并生成可运行的人物Skill", "meta"),
("darwin-skill", "autonomous skill optimizer", "meta"),
("huashu-slides", "端到端演示文稿制作", "tooling"),
("dukou", "稿件互通发布到 X Articles / B站专栏 / 公众号", "tooling"),
("munger-skill", "认知操作系统和决策框架", "founder"),
```

- [x] **Step 2: Run focused tests and confirm failure if rules are missing**

Run:

```bash
portal/backend/.venv/bin/python -m pytest tests/test_domain_inference.py -q
```

- [x] **Step 3: Update domain inference keywords**

Add keywords:

- `meta`: `skill optimizer`, `造skill`, `蒸馏`, `多Agent`, `agent swarm`, `认知调优`
- `tooling`: `PPT`, `配图`, `排版`, `发布`, `图床`, `Markdown`, `PDF`, `HTML`, `视频脚本`
- `founder`: `决策`, `创业`, `产品`, `增长`, `职业规划`, `认知操作系统`

- [x] **Step 4: Run tests**

Run:

```bash
portal/backend/.venv/bin/python -m pytest \
  tests/test_domain_inference.py \
  tests/test_graph_writer.py \
  tests/test_index_md_idempotent.py -q
```

Expected: pass.

Metadata result: INDEX and graph both contain 227 skills after Alchaincyf sync; graph extra/missing/domain mismatch are 0. `state_audit --metadata-only` remains drift=true until Task 7 rebuilds `data-mirror/` and `docs/data/`.

### Task 6: Problem Workflow Integration

**Files:**
- Modify: `docs/_src/problem-workflows.json`
- Modify: `docs/_src/originals/index.html`
- Modify: `docs/_src/build.py`
- Test: `tests/test_problem_workflows.py`, `tests/test_docs_homepage_contract.py`

- [x] **Step 1: Add workflow nodes for Alchaincyf source batch**

Add nodes:

- `source.alchaincyf-intake`
- `strategy.persona-judgment`
- `content.topic-to-platform`
- `design.html-native-production`
- `quality.anti-ai-slop-review`
- `distribution.article-bridge`
- `agentops.skill-generation-optimization`

- [x] **Step 2: Add homepage source collection section**

Expose:

- source owner
- installed count
- distill-only count
- direct install count
- monorepo install count
- duplicate skipped count

- [x] **Step 3: Run focused docs tests**

Run:

```bash
portal/backend/.venv/bin/python -m pytest \
  tests/test_problem_workflows.py \
  tests/test_docs_homepage_contract.py -q
```

Expected: pass.

Result: added 8 Alchaincyf workflow nodes, published `docs/data/alchaincyf-skill-manifest.json`, and rendered the homepage source collection. Focused docs tests pass after `bin/deploy-docs`.

### Task 7: Docs Rebuild and Static Publish Dry-run

**Files:**
- Generated: `data-mirror/`, `docs/data/`, `docs/zh/index.html`, `docs/en/index.html`, graph assets

- [x] **Step 1: Rebuild docs**

Run:

```bash
bin/deploy-docs
```

Expected:

- `state audit drift=false`
- docs skill count equals INDEX row count
- graph nodes equal INDEX row count

- [x] **Step 2: Run all tests**

Run:

```bash
portal/backend/.venv/bin/python -m pytest -q
```

Expected: all tests pass.

- [x] **Step 3: Run Tencent dry-run**

Run:

```bash
bin/deploy-tencent-static --target /tmp/agent-skills-tencent-smoke/ --dry-run
```

Expected: no `docs/_src/`, no `docs/superpowers/`, no `__pycache__/`, no `*.pyc` in transfer list.

Result: `bin/deploy-docs` passed with `drift=false`; `pytest -q` passed with 106 tests; Tencent dry-run listed 54 static files and included `data/alchaincyf-skill-manifest.json`.

### Task 8: Browser Verification

**Files:**
- Runtime artifact only: `output/playwright/alchaincyf-skills-site.png`

- [x] **Step 1: Start local static server**

Run:

```bash
portal/backend/.venv/bin/python -m http.server 4187 --bind 127.0.0.1 --directory docs
```

- [x] **Step 2: Open homepage and verify data**

Use Playwright CLI:

```bash
PWCLI="$HOME/.codex/skills/playwright/scripts/playwright_cli.sh"
"$PWCLI" -s=alchaincyf-site open http://127.0.0.1:4187/zh/index.html
"$PWCLI" -s=alchaincyf-site eval 'async () => { await new Promise(r => setTimeout(r, 1200)); return {cards: document.querySelectorAll(".skill-card").length, errors: 0, overflow: document.documentElement.scrollWidth - innerWidth}; }'
"$PWCLI" -s=alchaincyf-site console
```

Expected:

- skill cards render
- no console errors or warnings
- mobile width has no horizontal overflow
- Alchaincyf collection is visible

- [x] **Step 3: Stop static server**

Stop the server session with Ctrl-C and confirm:

```bash
lsof -ti:4187 || true
```

Expected: no output.

Result: Playwright verified `/zh/index.html` at desktop and 390px mobile widths: 227 skill cards, Alchaincyf collection visible, manifest link present, console errors/warnings 0, horizontal overflow 0. Screenshot saved to `output/playwright/alchaincyf-skills-site-mobile.png`.

### Task 9: Final Verification and Handoff

**Files:**
- Modify: `docs/superpowers/plans/2026-07-04-alchaincyf-skills-ingestion.md`

- [x] **Step 1: Run final verification**

Run:

```bash
git diff --check
portal/backend/.venv/bin/python -m agent.lib.state_audit --check --metadata-only
codegraph sync
codegraph status
```

Expected:

- whitespace clean
- `drift=false`
- CodeGraph index up to date

- [x] **Step 2: Report deploy boundary**

State explicitly:

- whether runtime skills were installed
- whether docs were rebuilt
- whether Tencent deploy was only dry-run or real `--apply`
- whether commit/push was performed

## Acceptance Criteria

- Every installed Alchaincyf skill has a clear function and solved problem in docs.
- Every installed skill belongs to one of the 6 domains.
- Every installed skill is assigned to at least one workflow node.
- Graph node count equals INDEX skill count.
- No direct filesystem install into `~/.config/opencode/skills/<name>/`.
- `bin/deploy-docs` passes.
- `pytest -q` passes.
- `state_audit --check --metadata-only` reports `drift=false`.
- Public site has no external CDN/runtime requests introduced by this batch.
- Tencent publish remains dry-run-first unless the user gives a real target and confirms `--apply`.
