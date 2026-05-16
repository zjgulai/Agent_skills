---
name: create-pr
description: Package code changes into reviewable, mergeable, communicable pull requests with proper title, description, scope, test results, risks, screenshots, and rollback notes. Use whenever local changes need to land on remote as a PR a human reviewer can actually approve.
---

# create-pr

When the user asks to create a PR, you produce a PR a senior reviewer can approve **without back-and-forth**.

## Pre-flight (mandatory checks, no exceptions)

1. **Branch state**: not on default branch (`main`/`master`), no uncommitted changes (or stash/commit first)
2. **Remote tracking**: branch pushed to remote with upstream set (`-u`)
3. **CI/tests**: relevant tests pass locally (note pre-existing failures, do NOT silently ignore)
4. **Diff scope**: review `git diff <base>...HEAD` yourself before drafting the PR

## PR title

Format: `<type>(<scope>): <imperative summary>`

- `type` ∈ `feat | fix | refactor | docs | test | chore | perf | ci`
- `scope` is the touched module / area, not the file path
- summary in imperative mood, ≤ 72 chars, no period

Examples:
- `feat(auth): add JWT refresh-token rotation`
- `fix(ui): clamp progress bar to 0..100`

## PR body template

```markdown
## Summary

<2-3 bullet points: what changed, why now>

## Changes

<concrete list — modules, key behaviors, schema migrations>

## Verification

- Tests run: `<command>` → `<result>`
- Manual verification: `<what the reviewer should reproduce>`
- Pre-existing failures: `<list, or "none">`

## Risks & rollback

- Risk: `<what could go wrong>`
- Rollback: `<git revert <sha>` or feature flag>

## Screenshots / recordings

<for UI changes; omit otherwise>

## Checklist

- [ ] Tests pass locally
- [ ] No secrets, tokens, or credentials in diff
- [ ] Migrations are forward-only or have explicit rollback path
- [ ] Breaking changes called out in summary
```

## Rules

- **Never** use `git commit --no-verify` or `gh pr create --draft` to silence pre-commit hooks
- **Never** force-push to a branch with an open PR unless you wrote the PR yourself in this session
- **Always** include a `Verification` section with at least one runnable command
- **Always** call out pre-existing failures explicitly so reviewers don't assume you broke them

## Workflow (when invoked)

1. `git status` → confirm clean / staged
2. `git log <base>..HEAD --oneline` → enumerate commits
3. `git diff <base>...HEAD` → understand scope
4. Draft title + body using templates above
5. `gh pr create --title "..." --body "$(cat <<'EOF' ... EOF)"` (HEREDOC for formatting)
6. Print PR URL on completion
