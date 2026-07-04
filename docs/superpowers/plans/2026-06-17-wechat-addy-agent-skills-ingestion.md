# WeChat Addy Agent Skills Ingestion Plan

> **For agentic workers:** execute task-by-task. Skill content must be installed only through the portal API. INDEX and graph metadata must be updated through `agent/lib/index_md_writer.py` and `agent/lib/graph_writer.py`.

**Goal:** Trace the WeChat article `https://mp.weixin.qq.com/s/eYWF7ro6h9t2yD1dFJy30g` to its primary source, distill the complete Addy Osmani `agent-skills` suite, ingest missing skills into the local OpenCode skill library, and route them through the existing domain and problem-workflow taxonomy.

**Primary Source:** `https://github.com/addyosmani/agent-skills`

**Local Scope:**
- Install only missing skills from the 24-skill suite; do not overwrite already installed skills.
- Add source digest documentation under `agent/docs/source-digests/`.
- Add INDEX and graph rows for newly installed skills.
- Extend `docs/_src/problem-workflows.json` so the suite is discoverable by AI automation lifecycle nodes.
- Regenerate docs/data mirrors and run tests/state audit.

---

### Task 1: Source Trace and Digest

- [ ] Parse the WeChat article for cited project name, lifecycle framing, slash commands, and source URL.
- [ ] Confirm source repository metadata through GitHub: owner, description, license, default branch, updated time, star count.
- [ ] Create `agent/docs/source-digests/addy-agent-skills.md` with the 24-skill suite map, article claims, official repo facts, command-to-skill mapping, and local ingestion decisions.

### Task 2: Portal Install

- [ ] Check `lsof -ti:5173,5174` before startup.
- [ ] Ensure portal backend is running with `portal/backend/.venv/bin/python -m agent.lib.portal_client ensure`.
- [ ] Install the 15 locally missing Addy skills using `install-monorepo` with explicit subdirs.
- [ ] Refresh portal data and confirm the 24 Addy skills are present locally.

### Task 3: Metadata

- [ ] Append missing skills to `~/.config/opencode/skills/INDEX.md` through `index_md_writer`.
- [ ] Add graph nodes through `graph_writer`, then render `skills-graph.png`.
- [ ] Refresh portal data after metadata changes.

### Task 4: Workflow Routing

- [ ] Extend `docs/_src/problem-workflows.json` with Addy skills across product definition, implementation, quality, deployment, operations, and retrospective nodes.
- [ ] Add regression assertions in `tests/test_problem_workflows.py` for key Addy skill problem-node mappings.

### Task 5: Generate and Verify

- [ ] Run `bin/sync-data`.
- [ ] Run docs deploy build.
- [ ] Run focused and full pytest.
- [ ] Run `git diff --check`.
- [ ] Run `state_audit --check --metadata-only`.
- [ ] Run `codegraph sync` and `codegraph status`.
