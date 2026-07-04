# Problem Workflow Taxonomy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a machine-readable, problem-solving workflow taxonomy that maps skills to AI automation lifecycle nodes from idea discovery through launch, growth, iteration, compliance, and retrospective learning.

**Architecture:** Keep the existing 6-domain taxonomy as the management/source-of-truth axis for INDEX, graph, registry schema, and install/classify commands. Add a second axis under `docs/_src/problem-workflows.json`; `docs/_src/data-collect.py` validates it, publishes `docs/data/problem-workflows.json`, and annotates each skill in `docs/data/skills.json` with `problem_nodes`. `docs/_src/build.py` renders a handbook section from the generated data.

**Tech Stack:** Python 3.12, JSON, BeautifulSoup static docs builder, pytest.

---

### Task 1: Contract Tests

**Files:**
- Create: `tests/test_problem_workflows.py`

- [ ] **Step 1: Add failing tests for workflow schema, skill references, and docs rendering**

```python
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS_JSON = REPO_ROOT / "docs" / "_src" / "problem-workflows.json"
SKILLS_JSON = REPO_ROOT / "docs" / "data" / "skills.json"
BUILD_PY = REPO_ROOT / "docs" / "_src" / "build.py"


def _load_build_module():
    spec = importlib.util.spec_from_file_location("docs_build", BUILD_PY)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_problem_workflow_taxonomy_contract():
    payload = json.loads(WORKFLOWS_JSON.read_text(encoding="utf-8"))
    assert payload["version"] == "2026-06-16"
    stages = payload["stages"]
    assert len(stages) == 14
    assert [stage["id"] for stage in stages] == [
        "00-agent-system",
        "01-idea-discovery",
        "02-market-validation",
        "03-product-definition",
        "04-design-prototype",
        "05-build-architecture",
        "06-quality-security",
        "07-launch-deploy",
        "08-growth-marketing",
        "09-sales-customer",
        "10-data-feedback",
        "11-ops-iteration",
        "12-ip-compliance",
        "13-retro-knowledge",
    ]
    node_ids = [node["id"] for stage in stages for node in stage["nodes"]]
    assert len(node_ids) == len(set(node_ids))
    assert len(node_ids) >= 40
    for stage in stages:
        assert stage["label_zh"]
        assert stage["automation_principle"]
        assert len(stage["nodes"]) >= 2
        for node in stage["nodes"]:
            assert node["problem_zh"]
            assert node["task_intents"]
            assert node["inputs"]
            assert node["outputs"]
            assert node["acceptance"]
            assert node["primary_skills"] or node["supporting_skills"]


def test_problem_workflow_skill_references_exist():
    payload = json.loads(WORKFLOWS_JSON.read_text(encoding="utf-8"))
    installed = {skill["name"] for skill in json.loads(SKILLS_JSON.read_text(encoding="utf-8"))}
    referenced = {
        skill
        for stage in payload["stages"]
        for node in stage["nodes"]
        for skill in node.get("primary_skills", []) + node.get("supporting_skills", [])
    }
    assert "startup-pressure-test" in referenced
    assert "shipping-and-launch" in referenced
    assert "post-mortem" in referenced
    assert referenced <= installed


def test_problem_workflows_annotate_skills_and_render_handbook():
    skills = json.loads(SKILLS_JSON.read_text(encoding="utf-8"))
    by_name = {skill["name"]: skill for skill in skills}
    assert "market-icp-pressure-test" in by_name["startup-pressure-test"]["problem_nodes"]
    assert "launch-release-gates" in by_name["shipping-and-launch"]["problem_nodes"]
    assert "retro-incident-learning" in by_name["post-mortem"]["problem_nodes"]

    build = _load_build_module()
    payload = json.loads((REPO_ROOT / "docs" / "data" / "problem-workflows.json").read_text(encoding="utf-8"))
    zh = build.render_problem_workflows(payload, "zh")
    en = build.render_problem_workflows(payload, "en")
    assert 'id="problem-workflows"' in zh
    assert "问题解决工作流" in zh
    assert "AI Automation Problem Workflow" in en
    assert "market-icp-pressure-test" in zh
```

- [ ] **Step 2: Run red check**

Run: `portal/backend/.venv/bin/python -m pytest tests/test_problem_workflows.py -q`

Expected: fail because `problem-workflows.json`, generated data, annotations, and renderer do not exist yet.

### Task 2: Source Taxonomy Data

**Files:**
- Create: `docs/_src/problem-workflows.json`
- Create: `agent/docs/problem-workflow-taxonomy.md`

- [ ] **Step 1: Create a 14-stage JSON payload**

Create stable stage IDs `00-agent-system` through `13-retro-knowledge`. Each stage must include `id`, `label_zh`, `label_en`, `automation_principle`, and at least two nodes.

- [ ] **Step 2: Create the human-readable taxonomy doc**

Document the 4-layer classification protocol: Lifecycle Stage → Problem Node → Task Intent → Automation Playbook. Include add-new-skill rules and acceptance requirements.

### Task 3: Data Collector Integration

**Files:**
- Modify: `docs/_src/data-collect.py`
- Modify generated: `docs/data/skills.json`
- Create generated: `docs/data/problem-workflows.json`

- [ ] **Step 1: Load and validate `problem-workflows.json`**

Add functions to read the source JSON, verify unique node IDs, verify required node fields, and verify all referenced skills exist in parsed INDEX data.

- [ ] **Step 2: Annotate skills**

Add a `problem_nodes` array to every skill object. The array is sorted by stage order and node order.

- [ ] **Step 3: Publish generated workflow JSON**

Write `docs/data/problem-workflows.json` with the same source payload plus per-node `skill_count`.

### Task 4: Handbook Rendering

**Files:**
- Modify: `docs/_src/build.py`
- Modify generated: `docs/zh/handbook.html`
- Modify generated: `docs/en/handbook.html`

- [ ] **Step 1: Add `render_problem_workflows(payload, lang)`**

Render a compact stage-by-stage section with stage labels, automation principles, node IDs, problem statements, and primary skill chips.

- [ ] **Step 2: Inject into handbook build**

Replace an existing `#problem-workflows` placeholder if present, otherwise insert the section after `#domains`.

### Task 5: Verification

**Files:**
- Test: `tests/test_problem_workflows.py`
- Test: existing docs/build tests

- [ ] **Step 1: Run focused tests**

Run: `portal/backend/.venv/bin/python -m pytest tests/test_problem_workflows.py tests/test_docs_hot_skills.py tests/test_docs_deploy_contract.py -q`

- [ ] **Step 2: Run docs build**

Run: `portal/backend/.venv/bin/python docs/_src/data-collect.py && portal/backend/.venv/bin/python docs/_src/build.py`

- [ ] **Step 3: Run full suite**

Run: `portal/backend/.venv/bin/python -m pytest tests/ -q`

- [ ] **Step 4: Check workspace**

Run: `git status --short`

Expected: planned source/generated files changed; no untracked `.codegraph/`.
