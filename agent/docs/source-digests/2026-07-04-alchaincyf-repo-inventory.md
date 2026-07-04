# Alchaincyf Source Digest

Snapshot date: 2026-07-04

Source: https://github.com/alchaincyf

## Inventory Boundary

The upstream account currently exposes 70 public repositories:

- 46 non-fork repositories.
- 24 fork repositories.
- Runtime ingestion is limited to repositories or subdirectories with a `SKILL.md` boundary.
- Book, guide, product, and application repositories are kept as source material until distilled into explicit skills.

This digest supports `docs/_src/alchaincyf-skill-manifest.json`. The manifest is the machine-readable contract; this file is the human-readable audit trail.

## Installation Model

| Mode | Count | Meaning |
|---|---:|---|
| root | 22 | Install a repository root through the portal GitHub install API. |
| subdir | 1 | Install a nested skill path through the portal GitHub install API. |
| monorepo | 20 | Install selected subdirectories from a multi-skill repository. |
| none | 16 | Do not install at runtime in this batch. |

Runtime install candidates: 43

Distill-only records: 11

Skipped records: 5

## Tier A: Direct Core Skills

These repositories are direct runtime candidates because they are skill-shaped source repositories and map to the current product workflow:

- `huashu-design`: design production, prototypes, slides, animation, and review.
- `nuwa-skill`: skill generation and thinking-model distillation.
- `darwin-skill`: skill evaluation and autonomous improvement loop.
- `huashu-md-html`: markdown, HTML, and document publishing pipeline.
- `huashu-slide-codex`: Codex visual material and deck production.
- `huashu-weread`: reading advisory workflows on top of WeRead notes and shelves.
- `x-mentor-skill`: X/Twitter topic, writing, and growth workflows.
- `freud-skill`: prompt, skill, and agent cognitive diagnosis.
- `dukou`: nested `skill/dukou` runtime skill for article distribution bridges.

## Tier B: Huashu Skills Monorepo

`huashu-skills` is handled as a selected monorepo install, not as a blind clone. The standalone `huashu-design` repository is treated as canonical, so `huashu-skills/huashu-design` is skipped as a duplicate.

Selected runtime subdirectories:

- `huashu-agent-swarm`
- `huashu-article-edit`
- `huashu-article-to-x`
- `huashu-data-pro`
- `huashu-douyin-script`
- `huashu-image-upload`
- `huashu-info-search`
- `huashu-material-search`
- `huashu-md-to-pdf`
- `huashu-prompt-save`
- `huashu-proofreading`
- `huashu-research`
- `huashu-script-polish`
- `huashu-slides`
- `huashu-speech-coach`
- `huashu-topic-gen`
- `huashu-video-check`
- `huashu-video-outline`
- `huashu-wechat-image`
- `huashu-xhs-image`

## Tier C: Persona and Thinking Framework Skills

These are runtime candidates, but their product value comes from problem placement rather than a flat persona list. They are assigned to strategy, judgment, product thinking, creator growth, or technical reasoning workflow nodes.

- `zhangxuefeng-skill` -> `zhangxuefeng-perspective`
- `zhang-yiming-skill` -> `zhang-yiming-perspective`
- `trump-skill` -> `trump-perspective`
- `taleb-skill` -> `taleb-perspective`
- `sun-yuchen-perspective` -> `sun-yuchen-perspective`
- `paul-graham-skill` -> `paul-graham-perspective`
- `naval-skill` -> `naval-perspective`
- `munger-skill` -> `munger-perspective`
- `mrbeast-skill` -> `mrbeast-perspective`
- `ilya-sutskever-skill` -> `ilya-sutskever-perspective`
- `feynman-skill` -> `feynman-perspective`
- `elon-musk-skill` -> `elon-musk-perspective`
- `karpathy-skill` -> `andrej-karpathy-perspective`
- `steve-jobs-skill` -> `steve-jobs-perspective`

## Tier D: Distill-Only or Skip

Distill-only repositories are useful source material but are not runtime skills yet:

- `loop-engineering-orange-book`
- `hermes-agent-orange-book`
- `codex-orange-book`
- `agent-skills-orange-book`
- `harness-engineering-orange-book`
- `claude-code-orange-book`
- `claude-code-source-analysis-orange-book`
- `openclaw-orange-book`
- `obsidian-ai-orange-book`
- `polymarket-orange-book`
- `skills-guide`

Skipped records are product or app repositories outside this batch's runtime boundary:

- `fanbox`
- `huasheng_editor`
- `img2046`
- `nes-arcade`
- `huashu-skills/huashu-design` duplicate

## Workflow Placement Principle

Each installed skill is mapped to one of these problem-oriented stages:

- `00-source-intake`: source inventory and distillation backlog.
- `01-sensemaking`: research, reading, material search, and data intake.
- `02-strategy-judgment`: decision quality, founder/product strategy, and persona reasoning.
- `03-content-planning`: topic, outline, script, and platform-specific planning.
- `04-design-production`: slides, HTML-native design, visual assets, and document conversion.
- `05-quality-review`: editing, proofreading, review, and anti-slop checks.
- `06-distribution`: article bridges, upload, and channel packaging.
- `07-agent-ops`: skill generation, optimization, and multi-agent coordination.
- `08-closeout-publish`: docs rebuild, graph sync, Tencent dry-run/apply, and handoff.

## Runtime Safety

- No direct writes should be made to `~/.config/opencode/skills/<name>/`.
- Root and subdir installs must go through `POST /api/install/github`.
- Monorepo installs must go through `POST /api/install/github/monorepo`.
- Metadata writes must back up `INDEX.md` and graph files before mutation.
- Tencent publishing remains dry-run first unless a real target and `--apply` are explicitly confirmed.

## Dry-Run Evidence

Portal compatibility check on 2026-07-04:

- `portal_client ensure`: ok.
- `portal_client status`: API up on 5174, reported 184 indexed skills.
- `portal_client scan https://github.com/alchaincyf/huashu-skills`: returned 21 nested skill subdirectories.
- Manifest selects 20 monorepo installs and skips `huashu-design` because the standalone repository is canonical.
- `dukou` remains a subdir install candidate with `subdir=skill/dukou`; no runtime install was performed during this dry-run phase.

Runtime install check after Task 4:

- Backup timestamp: `20260704011107`.
- Portal refresh reported 227 indexed skills.
- Manifest runtime check: 43 expected install names, 43 present, 0 missing.
- `huashu-nuwa` returned a client timeout during install, but API lookup confirmed it was installed successfully; this was a client read-timeout symptom, not a runtime install failure.

Docs and publish verification:

- `bin/deploy-docs`: passed; data mirror and docs count are 227; state audit reported `drift=false`.
- `pytest -q`: 106 passed.
- Tencent static dry-run: passed; transfer list contained 54 static files and no source-only folders.
- Browser smoke: `/zh/index.html` rendered 227 cards, Alchaincyf collection, manifest link, no console errors or warnings, and no horizontal overflow at desktop or 390px mobile width.
- CodeGraph: `codegraph sync` succeeded with temporary bundled Node 24 PATH because system Node 26 is blocked by CodeGraph; `codegraph status` reported index up to date.
