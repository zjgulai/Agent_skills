# Changelog

All notable changes to **Agent_skills** are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning is [SemVer](https://semver.org/).

## [Unreleased]

Pre-1.0. Three-repo system stabilising. Once Agent_skills + Agent_hook + Agent_mcp pin their `manifest.py` schema and CLI surface, a coordinated `1.0.0` will follow across all three.

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
