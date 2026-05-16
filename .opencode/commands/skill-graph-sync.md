---
description: Reconstruct skills-graph.mmd from INDEX.md (truth source) and re-render PNG. Idempotent.
agent: build
---

# /skill-graph-sync

Force-sync the graph (mmd + png) to match INDEX.md. Use when the two sources have drifted (e.g., manual INDEX edit, partial install failure).

## Execute

### Step 1 — Read current state

```bash
portal/backend/.venv/bin/python -m agent.lib.index_md_writer read
portal/backend/.venv/bin/python -m agent.lib.graph_writer read
```

Compare:
- skills in INDEX but not in graph → MISSING (will be added)
- skills in graph but not in INDEX → EXTRA (will be removed)
- skills in both with different domain → MISMATCH (graph will be moved)

### Step 2 — Show plan

```
=== Sync plan ===

MISSING (will be added to graph):
  • <skill> in domain <X>

EXTRA (will be removed from graph):
  • <skill>

MISMATCH (will be moved in graph):
  • <skill>: graph says <X>, INDEX says <Y> → graph wins gets <Y>

Apply? (y/N)
```

If no changes needed, print "graph is in sync; no changes needed" and skip rendering.

### Step 3 — User confirms; apply

For each MISSING:
```bash
portal/backend/.venv/bin/python -m agent.lib.graph_writer add <name> <domain>
```

For each EXTRA:
```bash
portal/backend/.venv/bin/python -m agent.lib.graph_writer remove <name>
```

For each MISMATCH (remove + add):
```bash
portal/backend/.venv/bin/python -m agent.lib.graph_writer remove <name>
portal/backend/.venv/bin/python -m agent.lib.graph_writer add <name> <correct_domain>
```

### Step 4 — Re-render

```bash
portal/backend/.venv/bin/python -m agent.lib.graph_writer render
```

### Step 5 — Final verify

```bash
portal/backend/.venv/bin/python -m agent.lib.graph_writer read
```

Compare against INDEX.md again. If still drifted, report which skills are still misaligned with backup paths so user can investigate.

## Idempotency

Running this command twice in a row should be a no-op the second time.
