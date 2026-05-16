# Security Policy

## Reporting a vulnerability

Please **do not** open a public GitHub issue. Instead:

1. Email **zjgulai@github.com** (or open a private GitHub Security Advisory at <https://github.com/zjgulai/Agent_skills/security/advisories>)
2. Include:
   - The repo and commit SHA you reproduced on
   - Minimum reproducing steps
   - The expected vs actual behavior
   - If the issue involves writing to a user's filesystem, include the **before / after** state of any client config you observed being mutated

We aim to triage within **3 business days**.

## What we consider a security issue

Agent_skills is the **methodology layer** of a three-repo system. The class of issues we treat as security:

| Severity | Example |
|---|---|
| Critical | A skill / adapter writes user-provided shell input into `~/.config/...` without escaping — leading to command injection on next CLI restart |
| High | Schema validator regresses and accepts a literal token (`ghp_*`, `sk-*`, `AIza*`) into a checked-in manifest |
| High | Adapter accidentally deletes a non-managed entry from a user's client config (no `_managed_by` anchor honored) |
| Medium | A symlink is followed across boundaries we don't intend(symlink target outside `~/.config` etc.) |
| Medium | `prune_backups()` deletes more than `keep=N` files |
| Low | Stale public docs claim a security property that the code no longer provides |

## What is NOT a security issue

- A user explicitly disabling a hook via the documented escape-hatch env var (`AGENT_HOOK_ALLOW_SENSITIVE=...`, `AGENT_HOOK_BASH_YOLO=1`, etc.). These are intentional opt-outs.
- A skill description triggering on a phrase you didn't expect — that's a UX issue, file a regular issue.
- An MCP that fails to start because its env var (e.g. `GITHUB_TOKEN`) isn't set. That's expected and reported by `agent-skill doctor`.
- A user of cursor not getting hook **enforcement** — cursor only supports degraded Rule (soft constraint), as documented in adapter compatibility.

## Token / secret model

**Tokens never live in any file managed by this repo.** The flow is:

1. User exports tokens in their shell (`~/.zshrc`): `export GITHUB_TOKEN=ghp_...`
2. Manifest declares the env name only: `requires.env: [GITHUB_TOKEN]`
3. Adapter writes the literal string `${GITHUB_TOKEN}` (interpolation directive) into client config
4. Client runtime inherits the actual value from shell env at process start

Schema validator includes a regex check rejecting literal `ghp_*`, `sk-[a-zA-Z0-9]{10,}`, `AIza[0-9A-Za-z_-]{20,}` patterns at manifest load time. **If you see a literal token committed to this repo, that is a critical bug — report it.**

## Update policy

Critical / High issues:
- Patch released within **7 business days** of confirmation
- CVE filed if applicable
- Fix is coordinated across all three companion repos if `manifest.py` or schema is involved

## Companion repos

This policy applies equally to:
- [Agent_hook](https://github.com/zjgulai/Agent_hook) (enforcement layer)
- [Agent_mcp](https://github.com/zjgulai/Agent_mcp) (context layer)

Issues touching the shared `agent/lib/manifest.py` (md5 `b46c2f55980b9aa2ea93b87941c833e2`) require coordinated patches across all three.
