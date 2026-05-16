# Contributing to Agent_skills

Thanks for considering a contribution! Agent_skills is the **methodology layer** of a three-repo system, so contributions here often touch shared concerns. This document explains the rules.

## Three-repo system

Agent_skills sits alongside two companion repos that share a common spine:

- **[Agent_skills](https://github.com/zjgulai/Agent_skills)** (this repo) — methodology · 16 skills
- **[Agent_hook](https://github.com/zjgulai/Agent_hook)** — enforcement · 9 hooks
- **[Agent_mcp](https://github.com/zjgulai/Agent_mcp)** — context · 10 MCPs

The three repos share **`agent/lib/manifest.py` byte-identically** (md5 `b46c2f55980b9aa2ea93b87941c833e2`). If you change schema in one repo, you must propagate to all three. See [Manifest schema rules](#manifest-schema-rules) below.

## Quick start (development)

```bash
git clone https://github.com/zjgulai/Agent_skills.git ~/project/Agent_skills
cd ~/project/Agent_skills
python3 -m pip install --user pyyaml tomli tomli_w pytest

# Run tests (must pass before any commit)
python3 -m pytest tests/

# Try the CLI
./bin/agent-skill list
./bin/agent-skill doctor
```

## Pull request rules

**Required for every PR**:

1. **Tests pass** — `python3 -m pytest tests/` must report all green. Add tests for new behavior.
2. **No `lsp_diagnostics` errors** on changed files (run `lsp_diagnostics` or your IDE equivalent).
3. **Conventional commit message** — `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`, `perf:`. Include scope if non-trivial: `feat(adapter-cursor): ...`.
4. **CHANGELOG.md updated** under `[Unreleased]` for user-visible changes.
5. **Type-safe code** — no `# type: ignore`, no broad `try / except / pass`.

## Manifest schema rules

`agent/lib/manifest.py` is the single source of truth for skill / hook / mcp metadata. **It is duplicated byte-identically into Agent_hook and Agent_mcp.**

If you change `manifest.py`:

```bash
# 1. Edit in the canonical location (Agent_hook is canonical, but any of the
#    three works as long as the helper script ends up byte-identical).
$EDITOR agent/lib/manifest.py

# 2. Run the sync helper (vendored in all 3 repos).
bash agent/lib/sync_manifest_lib.sh

# 3. Verify md5 match across the three repos.
for repo in Agent_skills Agent_hook Agent_mcp; do
  /sbin/md5 -q ~/project/$repo/agent/lib/manifest.py
done
# All three lines must match.

# 4. Commit + PR each repo separately, referencing the schema bump in CHANGELOG.
```

**Schema-breaking changes** (renaming/removing required fields) require **major version bumps in all three repos**, coordinated.

## Adapter contracts

Each `agent/lib/adapter_<client>.py` must implement:

- `install(m: Manifest) -> dict` — write client config, return result with `link` / `config` / `backup` keys
- `uninstall(name: str) -> dict` — remove by anchor, refuse non-managed entries
- `list_installed() -> list[dict]` — read current state from client config
- `status_for(name: str) -> str` — `managed | external | absent` (or `n/a` for unsupported clients)

**Hard rules**:

1. **Never delete user-written config** — anchor (`_managed_by: agent-skill`) check is the only delete authority.
2. **Always backup before write** — `cp <target> <target>.bak.{timestamp}` before any client config mutation.
3. **`prune_backups(keep=5)`** after every write — backups bounded.
4. **Symbolic refusal** — if `compatibility.<client> == "unsupported"` in manifest, return early with `skipped: True`.

## Test requirements

Every adapter, every hook, every CLI command needs a test:

| Surface | Test file | Style |
|---|---|---|
| Manifest schema field | `tests/test_manifest_schema.py` | parametrized validators |
| Adapter behavior | `tests/test_skill_adapters.py` | `monkeypatch` paths, no real client mutation |
| New skill source | `registry/<name>/tests/` (optional) | source-script smoke |

Adapters must **never test against the user's real `~/.config/...`** — always `monkeypatch` the path constants to a `tmp_path`.

## Documentation

- **README** — keep "Related repos" section in sync with companion repos.
- **CLAUDE.md** / **AGENTS.md** — same file (`CLAUDE.md` is symlink). Both opencode and Claude Code agents read it as project rules.
- **docs/*.html** — when changing user-facing behavior, also update `docs/handbook.html` and add a note in `docs/getting-started.html`.

## Code style

- **Python**: `ruff format` (or `black -q`). Type hints on all public functions.
- **TypeScript** (portal/frontend): Vite + Vue 3 native style; `prettier` if installed.
- **YAML manifests**: 2-space indent, no trailing whitespace, `kebab-case-name` for `name`.

## Issue reporting

Open an issue at <https://github.com/zjgulai/Agent_skills/issues>. Include:

- Repo + commit SHA you're on
- `python3 -m pytest tests/` output if test-related
- `./bin/agent-skill doctor` output if integration-related
- Minimal reproducing example

## License

By contributing, you agree your work is licensed under [MIT](LICENSE).
