# Addy Osmani Agent Skills Source Digest

## Source Trace

| Field | Evidence |
|---|---|
| WeChat article | <https://mp.weixin.qq.com/s/eYWF7ro6h9t2yD1dFJy30g> |
| Article title | 狂揽 50000 Star！谷歌悄悄开源了 Agent Skills 神器 |
| Primary source named by article | <https://github.com/addyosmani/agent-skills> |
| Canonical repository | `addyosmani/agent-skills` |
| Repository description | Production-grade engineering skills for AI coding agents. |
| Default branch | `main` |
| License | MIT |
| Live source check | `gh repo view addyosmani/agent-skills --json nameWithOwner,description,stargazerCount,updatedAt,url,defaultBranchRef,licenseInfo` |

The article frames the project as a way to make AI coding agents follow senior-engineer workflows instead of only generating code. The official repository confirms the same lifecycle framing: define, plan, build, verify, review, and ship.

The article's "50,000+ stars" claim was treated as a historical article claim. A live GitHub check during ingestion reported `61,282` stars and `updatedAt=2026-06-17T01:39:45Z`, so local documentation should avoid hard-coding the article count as current truth.

## Official Suite Shape

The repository ships 7 lifecycle slash commands and 24 skills:

| Lifecycle | Command | Local routing intent |
|---|---|---|
| Define | `/spec` | Clarify idea, intent, PRD, and boundaries before code. |
| Plan | `/plan` | Turn a spec into ordered, verifiable tasks. |
| Build | `/build` | Implement thin slices with tests and checkpoints. |
| Verify | `/test` | Prove behavior in tests, browser runtime, and debugging loops. |
| Review | `/review` | Run quality, simplification, security, and performance gates. |
| Simplify | `/code-simplify` | Reduce complexity without changing behavior. |
| Ship | `/ship` | Prepare CI, rollout, observability, docs, migration, and launch evidence. |

The repository also contains agent personas (`code-reviewer`, `test-engineer`, `security-auditor`, `web-performance-auditor`) and reference checklists. These are source context, but they are not installed as OpenCode skills because the local skill warehouse ingests `skills/*/SKILL.md` entries.

## 24-Skill Distillation

| Skill | Lifecycle role | Problem-solving focus | Local domain |
|---|---|---|---|
| `using-agent-skills` | Meta | Decide which Addy skill workflow applies and enforce shared skill-use rules. | `meta` |
| `interview-me` | Define | Extract real intent through one-question-at-a-time clarification. | `meta` |
| `idea-refine` | Define | Expand, stress-test, and converge raw ideas into actionable concepts. | `meta` |
| `spec-driven-development` | Define | Write a spec before implementation for new projects, features, or significant changes. | `meta` |
| `planning-and-task-breakdown` | Plan | Break specs into ordered tasks with acceptance criteria and dependencies. | `meta` |
| `incremental-implementation` | Build | Land multi-file work as thin, tested, rollback-friendly slices. | `meta` |
| `test-driven-development` | Build | Apply red-green-refactor before feature or bugfix implementation. | `meta` |
| `context-engineering` | Build | Prepare rules, project context, and MCP/context inputs when agent quality depends on context. | `meta` |
| `source-driven-development` | Build | Ground implementation choices in official documentation and mark unverified assumptions. | `meta` |
| `doubt-driven-development` | Build | Use adversarial fresh-context review for high-risk decisions. | `meta` |
| `frontend-ui-engineering` | Build | Build production-quality user-facing UI with components, responsiveness, and accessibility. | `tooling` |
| `api-and-interface-design` | Build | Design stable APIs, type contracts, and module boundaries. | `meta` |
| `browser-testing-with-devtools` | Verify | Use real browser runtime evidence: DOM, console, network, performance. | `closeout` |
| `debugging-and-error-recovery` | Verify | Reproduce, localize, reduce, fix, and guard against regressions. | `closeout` |
| `code-review-and-quality` | Review | Review changes across correctness, maintainability, safety, and merge readiness. | `closeout` |
| `code-simplification` | Review | Simplify working code while preserving exact behavior. | `closeout` |
| `security-and-hardening` | Review | Harden user input, auth, data storage, and third-party integration paths. | `tooling` |
| `performance-optimization` | Review | Measure first, then optimize Core Web Vitals, load time, or bottlenecks. | `tooling` |
| `git-workflow-and-versioning` | Ship | Use atomic commits, branch hygiene, and versioning discipline. | `closeout` |
| `ci-cd-and-automation` | Ship | Build CI/CD pipelines, quality gates, and deployment automation. | `closeout` |
| `deprecation-and-migration` | Ship | Retire old systems, migrate users, and remove zombie code deliberately. | `closeout` |
| `documentation-and-adrs` | Ship | Capture decisions, API docs, and the "why" future agents need. | `closeout` |
| `observability-and-instrumentation` | Ship | Add logs, metrics, traces, and alerts while building production features. | `tooling` |
| `shipping-and-launch` | Ship | Prepare rollout, rollback, monitoring, and production launch gates. | `closeout` |

## Local Ingestion Decision

Already installed before this ingestion:

- `api-and-interface-design`
- `context-engineering`
- `observability-and-instrumentation`
- `performance-optimization`
- `security-and-hardening`
- `shipping-and-launch`
- `source-driven-development`
- `spec-driven-development`
- `test-driven-development`

Installed during this ingestion through the portal API:

- `browser-testing-with-devtools`
- `ci-cd-and-automation`
- `code-review-and-quality`
- `code-simplification`
- `debugging-and-error-recovery`
- `deprecation-and-migration`
- `documentation-and-adrs`
- `doubt-driven-development`
- `frontend-ui-engineering`
- `git-workflow-and-versioning`
- `idea-refine`
- `incremental-implementation`
- `interview-me`
- `planning-and-task-breakdown`
- `using-agent-skills`

Metadata updates:

- `~/.config/opencode/skills/INDEX.md` was updated through `agent.lib.index_md_writer`.
- `~/.config/opencode/skills/skills-graph.mmd` and `skills-graph.png` were updated through `agent.lib.graph_writer`.
- `docs/_src/problem-workflows.json` routes these skills across the local AI automation workflow from idea clarification to release, operation, and retrospective knowledge capture.

## Workflow Routing Summary

| Workflow stage | Addy skills routed there |
|---|---|
| AI automation system | `using-agent-skills`, `context-engineering`, `doubt-driven-development` |
| Idea and product definition | `interview-me`, `idea-refine`, `spec-driven-development`, `planning-and-task-breakdown` |
| Build and architecture | `incremental-implementation`, `test-driven-development`, `source-driven-development`, `api-and-interface-design`, `frontend-ui-engineering` |
| Quality and security | `browser-testing-with-devtools`, `debugging-and-error-recovery`, `code-review-and-quality`, `code-simplification`, `security-and-hardening`, `performance-optimization` |
| Launch and deploy | `git-workflow-and-versioning`, `ci-cd-and-automation`, `documentation-and-adrs`, `observability-and-instrumentation`, `shipping-and-launch` |
| Operations and retro | `deprecation-and-migration`, `documentation-and-adrs`, `observability-and-instrumentation`, `debugging-and-error-recovery` |

## Maintenance Notes

- Do not install the repository root as one skill; the official suite is under `skills/*/SKILL.md`.
- Do not treat article star counts as live metadata. Refresh via GitHub before reporting current popularity.
- If the local taxonomy later adds a separate "engineering lifecycle" domain, this suite should be reviewed as a candidate for finer domain placement. For now, workflow routing carries the lifecycle specificity.
