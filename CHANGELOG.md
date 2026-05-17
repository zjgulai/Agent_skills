# Changelog

All notable changes to **Agent_skills** are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning is [SemVer](https://semver.org/).

## [Unreleased]

Pre-1.0. Three-repo system stabilising. Once Agent_skills + Agent_hook + Agent_mcp pin their `manifest.py` schema and CLI surface, a coordinated `1.0.0` will follow across all three.

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
