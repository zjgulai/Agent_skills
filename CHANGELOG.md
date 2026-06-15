# Changelog

All notable changes to **Agent_skills** are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning is [SemVer](https://semver.org/).

## [Unreleased]

Pre-1.0. Three-repo system stabilising. Once Agent_skills + Agent_hook + Agent_mcp pin their `manifest.py` schema and CLI surface, a coordinated `1.0.0` will follow across all three.

### Added — 2026-06-14 weekly hot skills refresh

- Installed 17 curated skills from recently active GitHub repositories:
  - `ast-grep`
  - `supabase`, `supabase-postgres-best-practices`
  - `deploy-to-vercel`, `vercel-optimize`, `vercel-react-best-practices`, `web-design-guidelines`
  - `context-engineering`, `source-driven-development`, `spec-driven-development`, `api-and-interface-design`
  - `performance-optimization`, `observability-and-instrumentation`, `shipping-and-launch`, `security-and-hardening`
  - `obsidian-markdown`, `json-canvas`
- Added `docs/_src/weekly-hot-skills.json` and generated `docs/data/weekly-hot-skills.json`.
- Added a bilingual homepage "Hot Skills Radar This Week" section showing installed curated groups plus watchlisted aggregator repos.
- Added `bin/deploy-docs`: one command for `sync-data` → docs data build → bilingual HTML build → metadata-only publish audit; `--push` commits and pushes Pages-triggering files.

### Fixed — local metadata drift

- Registered 4 already-installed `paper2skills-*` skills in `INDEX.md` and `skills-graph.mmd`:
  - `paper2skills-deploy`
  - `paper2skills-ps-override`
  - `paper2skills-ui-audit`
  - `paper2skills-workflow`
- Full state audit now converges on 164 installed/INDEX/graph/docs skills after sync.

## [0.4.0] — 2026-06-03

GitHub 近一周上升榜单深度挖掘 + 增量 skills 部署。skill_count 从 85 增至 141，新增 codegraph CLI + MCP 接入，修复 build.py 数据容错问题。

### Added — skill 批量增量部署（85 → 141，+56）

来源：6 个 GitHub 近一周高热仓库，基于 Shareuhack 周报 2026-05-27（+20K stars codegraph、+14.7K Understand-Anything 等）和 BuilderPulse 2026-06-01 周榜交叉筛选。

**写作质量域**
- `stop-slop` (hardikpandya/stop-slop) — 清除 AI 写作特征：结构陈词、泛用句型、可预测段落

**UI 视觉品味套件**（Leonxlnx/taste-skill，75K stars）
- `minimalist-ui` — 极简主义 UI：留白、克制、减法美学
- `industrial-brutalist-ui` — 工业/野兽派 UI：高对比、原始、结构性
- `redesign-existing-projects` — 系统化改造现有 UI 至新美学目标
- `stitch-design-taste` — 多参考拼合同一视觉语言
- `high-end-visual-design` — 高端柔软奢华视觉：深度、光晕、精致感

**工程方法论套件**（thananon/9arm-skills，2.3K 新热）
- `debug-mantra` — 结构化调试信条：系统化定位根因
- `scrutinize` — 深度代码审视：正确性、边界、隐藏假设
- `post-mortem` — 规范化故障复盘：5-whys、时间线、行动项
- `management-talk` — 技术工作翻译成业务语言给 stakeholder

**学术研究套件**（Imbad0202/academic-research-skills，+10.7K/周）
- `academic-paper` — 12-agent 学术论文全流程：研究→写作→评审→修订→定稿
- `academic-paper-reviewer` — 同行评审模拟：结构化批评与改进建议
- `academic-pipeline` — 端到端研究发表流水线编排
- `deep-research` — 通用深度研究：多源合成、证据驱动

**Anthropic 知识工作插件**（anthropics/knowledge-work-plugins，+2.7K/周，官方）— 35 个 role skill 覆盖：
- 工程：`architecture`、`debug`、`system-design`、`tech-debt`、`incident-response`、`code-review`、`write-spec`、`sprint-planning`、`metrics-review`
- 数据：`explore-data`、`sql-queries`、`statistical-analysis`、`data-visualization`
- 设计：`design-critique`、`accessibility-review`、`ux-copy`、`knowledge-synthesis`、`search`
- 市场：`content-creation`、`seo-audit`、`email-sequence`
- 法务：`review-contract`、`compliance-check`
- 运营：`runbook`、`risk-assessment`
- HR：`interview-prep`、`onboarding`、`performance-review`
- 财务：`variance-analysis`、`financial-statements`
- 销售：`account-research`、`pipeline-review`、`competitive-intelligence`、`draft-outreach`
- 客服：`ticket-triage`、`draft-response`
- 小微企业：`cash-flow-snapshot`、`lead-triage`

**安全专项套件**（mukul975/Anthropic-Cybersecurity-Skills，12K stars）
- `analyzing-threat-actor-ttps-with-mitre-attack` — MITRE ATT&CK TTP 映射分析
- `implementing-honeypot-for-ransomware-detection` — 勒索软件蜜罐早期检测实施

**codegraph 内置 skills**（colbymchenry/codegraph，+20K/周，本周榜首）
- `codegraph-agent-eval` — 对真实代码库做 codegraph 检索质量基准测试（with/without A/B）
- `codegraph-add-lang` — 端到端为 codegraph 添加新 tree-sitter 语言支持

### Added — codegraph CLI + MCP 接入

- codegraph v0.9.9 CLI 安装到 `~/.local/bin/codegraph`（官方 install.sh，darwin-arm64 bundle，自带 Node 运行时，不依赖系统 Node 版本）
- `codegraph install --target=opencode --yes` 写入 `~/.config/opencode/opencode.json` MCP server 配置：`{"type":"local","command":["codegraph","serve","--mcp"],"enabled":true}`
- 项目初始化方式：`cd <project> && codegraph init -i`，之后 opencode agent 通过 MCP tool 查询符号、调用链、import 关系，大幅减少 token 消耗

### Fixed — build.py 数据容错

- `docs/_src/build.py` `render_case_studies()` 改用 `.get()` 防御读取 `title/desc/bullets` 字段，兼容 case-studies.json 中数据不完整的 state 条目（State 15 anysearch 缺 `desc_zh`/`bullets_zh`）。之前 KeyError 导致 CI 构建失败

### Changed — portal 数据刷新

- portal 从 85 → 139 skills（`POST /api/refresh` 重建索引，`skill_count=139`）
- `data-mirror/INDEX.md` 注入 54 个新 skill 行（按域分类追加）
- `docs/data/{skills,domains,portal-status}.json` 本地预跑 `data-collect.py`，skill_count=132（data-mirror 真相源）后推送
- GitHub Pages CI 重新构建，`https://zjgulai.github.io/Agent_skills` 更新至最新 skill 数量

### Skill inventory

- 85 → 141 skills（+56），域分布：
  - meta 54（方法论 + 工程基础设施）
  - closeout 14（代码质量与交付闭环）
  - desktop 1、founder 1、ip 2
  - tooling 60（横切层工具，含全部 Anthropic kw-plugins）
- `/skill-doctor all`：141/141 PASS

## [0.3.0] — 2026-05-17

The "dynamic docs + monorepo install + dry-scan" release. Skill_count grew from 9 to 52 across 9 case-study state transitions. The site at https://zjgulai.github.io/Agent_skills now rebuilds automatically on every push.

### Added — dynamic docs site

- `bin/sync-data` — mirrors `~/.config/opencode/skills/{INDEX.md,skills-graph.{mmd,png}}` → `data-mirror/` (the git-tracked truth source). `--check` for dry-run, `--diff-skills` for machine-readable new-skill detection.
- `docs/_src/` build pipeline (Python, ~5s end-to-end on CI):
  - `data-collect.py` — `INDEX.md` → `docs/data/{skills,domains,portal-status}.json`
  - `i18n-extract.py` — original HTML → `i18n/zh.json` (285 zh entries across 4 pages, one-shot)
  - `build.py` — BeautifulSoup DOM rewrite, outputs `docs/{zh,en}/*.html`. Handles `data-i18n` / `data-i18n-html` / `data-i18n-attr`. Auto-injects dynamic skill_count and rewrites stale hero screenshot to live `skills-graph.png`.
- `docs/_src/case-studies.json` — 10 graph evolution states driven by data; build.py renders the entire `#case-studies` section from this file.
- `.github/workflows/deploy-docs.yml` — push to `main` triggers ~30s rebuild → GitHub Pages deploy. Trigger paths: `data-mirror/**`, `docs/**`.
- `docs/index.html` — language-aware redirect (navigator.language → `/zh/` or `/en/`).

### Added — monorepo install

- `portal/backend/installer.py::install_monorepo_from_github(url, subdirs=None)` — one git clone, many copies. Server-side iteration over subdirs avoids 18× round-trip latency that previously made gstack-class monorepo installs >10 min (and time out).
- `portal/backend/app.py::POST /api/install/github/monorepo` — new HTTP endpoint, request body `{url, subdirs?}`.
- `agent/lib/portal_client.py::install_monorepo()` / `scan_monorepo()` — client wrappers. `scan` walks GitHub git/trees API (one HTTP call) to discover all `*/SKILL.md`. `install_monorepo` calls the new endpoint with 900s read timeout, falls back to per-subdir loop if portal returns 404.
- CLI: `scan <url>` and `install-monorepo <url> [<subdir>...]` subcommands.

### Performance

- `--filter=blob:none` on git clone; timeout bumped 120s → 300s. **Measured 17× speedup** for 14-skill superpowers monorepo (~40s → 2.4s).

### Changed — /skill-install slash command

- Grew from 7 steps to 12: now includes Step 0 (auto-detect single / monorepo / catalog stub via `scan`) and Steps 8-12 (sync-data + case-study append + commit + push + CI link report). One sentence → one PR → one deploy.
- Step 9 case-study logic distinguishes single skill (3 questions) vs monorepo (single question, generates one combined State).
- Step 0 routing: 0 subdirs → single mode; 1 subdir → auto-fill; ≥2 subdirs → present menu (`A. install all / B. pick / C. cancel`).
- New `--dry-scan` flag: read-only preview. Performs scan + frontmatter read + domain inference + overlap analysis with already-installed skills; outputs a structured report; **installs nothing**. Validated on `nextlevelbuilder/ui-ux-pro-max-skill` (caught 6 invalid `ckm:` names) and `nexu-io/open-design` (identified catalog-stub pattern; recommended installing upstream repos instead).

### Fixed

- `install_upload` / `uninstall` / `refresh` were accidentally dropped from `portal_client.py` during the monorepo PR — restored from git history.
- `SCAN_SKIP_DIRS` ↔ installer `SKIP_DIRS` now aligned. Previously `scan` returned `.claude/skills/*` but installer's auto-discover silently filtered them; now both use a named list (`.git, .github, .idea, .vscode, .cache, .pytest_cache, node_modules, __pycache__, .venv, venv, dist, build`). User-defined hidden dirs (`.claude/`) remain discoverable.
- Friendlier frontmatter validation error for namespace-prefix names (`ckm:foo`): suggests `ckm-foo` sanitized form, points out that `:` is not part of the official SKILL.md spec.
- UTF-8 mojibake in `hero.badge` and similar zh translations: `i18n-extract.py` was wrongly calling `bytes.decode("unicode_escape")` on UTF-8 input, double-encoding Chinese characters. Replaced with explicit escape sequence handling.

### Skill inventory

- 9 → 52 skills across 6 domains. New additions span: agent-reach (twitter+reddit+youtube etc), superpowers suite (14 sub-skills, TDD+plan+subagent methodology), gstack 18-piece kit (plan reviews + QA + land-and-deploy + design), bb-browser (logged-in browser automation), notebooklm, ui-ux-pro-max (UI/UX reference library), and 8 skills sourced via dry-scan from 5 upstream repos (color-expert, design-taste-frontend, creative-director, marketing-psychology, copywriting, hig-foundations, hig-platforms, hig-components-controls).
- Domain distribution: meta 22 (was 2), closeout 8 (was 1), desktop 1, founder 1, ip 2, tooling 18 (was 2). `/skill-doctor`: 52/52 PASS.

## [0.2.0] — 2026-05-16

This release joins the three-repo system. Adds the shared manifest schema, 4-client adapter pattern, `agent-skill` CLI, portal three-way merge, and an idea→PR demo. Brings Agent_skills public state up to parity with [Agent_hook](https://github.com/zjgulai/Agent_hook) and [Agent_mcp](https://github.com/zjgulai/Agent_mcp).

### Added

- `registry/<name>/manifest.yaml` for 16 skills (5 P0 + 8 P1 + 3 P2)
- `agent/lib/manifest.py` — shared schema validator, byte-identical across 3 repos (md5 `b46c2f55980b9aa2ea93b87941c833e2`)
- `agent/lib/adapter_{opencode,codex,cursor,kimi}.py` — symlink-based skill distribution to 4 client directories + Kimi `extra_skill_dirs`
- `agent/lib/cli.py` + `bin/agent-skill` — `list / install / uninstall / doctor / show` subcommands
- `portal/backend/hooks_api.py` + `portal/backend/mcps_api.py` — `/api/hooks` and `/api/mcps` endpoints reading from the companion repos' registries
- `portal/frontend/components/KindView.vue` — 3-tab UI (Skills / Hooks / MCPs) with detail panel, env status, binary status
- `docs/demo/agent-kit.html` — 15815-byte single-file landing page (frontend-design skill product: serif headlines, amber accent, glass panels)
- `docs/demo/E2E-DEMO.md` — 7-step transcript of the idea→PR workflow with real evidence
- 28 schema tests + 17 skill-adapter tests (=45 new tests; total 65 with prior portal/index tests)

### Documentation

- README "Related repos" section links [Agent_hook](https://github.com/zjgulai/Agent_hook) and [Agent_mcp](https://github.com/zjgulai/Agent_mcp)

## [0.1.x] — 2026-05-13 to 2026-05-16

The original "Skills Manager AI Agent" project — local FastAPI (5174) + Vue (5173) portal that managed `~/.config/opencode/skills/`, with 11 slash commands, domain auto-inference, INDEX.md + skills-graph maintenance.

### Highlights

- `feat: bootstrap Skills Manager AI Agent monorepo` (3f40ad0)
- `feat: add 6-page GitHub Pages site` (2e786d1)
- `feat(docs): handbook page + bilingual EN/ZH toggle` (2fdd2cb)
- `i18n(docs): translate handbook §2-§5 detail content to Chinese` (16e5640)
- `feat: add MIT LICENSE + README badges + Why section` (8d4bb84)

The 0.1.x line still works standalone. The 0.2.0 release **adds** a three-repo layer on top — none of the 0.1.x portal lifecycle is removed.

## Compatibility

| Version | manifest.py md5 | Companion repos required |
|---|---|---|
| 0.2.0 | `b46c2f55980b9aa2ea93b87941c833e2` | Agent_hook ≥ 0.1.1, Agent_mcp ≥ 0.1.1 |
| 0.1.x | n/a (no shared manifest) | none |

Cross-repo `manifest.py` byte-identical is verified at every release via `agent/lib/sync_manifest_lib.sh`.
