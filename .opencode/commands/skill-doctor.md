---
description: Health check across 5 rules per skill. Pass `<name>` for one skill, no arg or `all` for full scan.
agent: build
---

# /skill-doctor

Run 5 health-check rules over an installed skill (or all):

- **R1** — SKILL.md frontmatter parses (name + description)
- **R2** — directory name matches frontmatter name
- **R3** — present in INDEX.md
- **R4** — present in skills-graph.mmd with matching domain
- **R5** — declared external dependencies are available

**Arguments**: `$ARGUMENTS` — skill name, or `all` (default if empty).

## Execute

```bash
portal/backend/.venv/bin/python -m agent.lib.doctor "$ARGUMENTS"
```

Then format the JSON output as a human-readable red/yellow/green table.

## Output format

For single skill:
```
=== <skill_name> [<overall>] ===
  ✅ R1: frontmatter parses
  ✅ R2: dir matches
  ✅ R3: in INDEX (domain=tooling)
  ✅ R4: in graph as GPS (tooling)
  ⚠️  R5: dependency 'node' not found
```

For all:
```
| skill                              | overall | issues                          |
|------------------------------------|---------|---------------------------------|
| agent-dev-kit-architecture-designer | PASS    | —                               |
| codex-review                       | WARN    | R5: codex CLI not in PATH       |
| guizang-ppt-skill                  | PASS    | —                               |
...

Totals: <P> PASS, <W> WARN, <F> FAIL
```

If any FAIL, list specific remediation:
- R1/R2 → "skill needs reinstall"
- R3 → "run /skill-classify to add it"
- R4 → "run /skill-graph-sync"
- R5 → install the missing dependency, or accept degraded mode

Read-only. No writes.
