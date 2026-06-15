"""Static contract checks for the GitHub Pages deploy path."""
from __future__ import annotations

import os
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "deploy-docs.yml"
DEPLOY_SCRIPT = REPO_ROOT / "bin" / "deploy-docs"


def test_pages_workflow_uses_node24_compatible_action_versions():
    data = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    build_steps = data["jobs"]["build"]["steps"]

    assert build_steps[0]["uses"] == "actions/checkout@v6"
    assert build_steps[1]["uses"] == "actions/setup-python@v6"
    assert build_steps[-1]["uses"] == "actions/upload-pages-artifact@v5"
    assert data["jobs"]["deploy"]["steps"][0]["uses"] == "actions/deploy-pages@v5"


def test_deploy_docs_script_includes_workflow_in_push_batch():
    source = DEPLOY_SCRIPT.read_text(encoding="utf-8")

    assert os.access(DEPLOY_SCRIPT, os.X_OK)
    assert ".github/workflows/deploy-docs.yml" in source
    assert "git diff --check -- data-mirror docs bin/deploy-docs README.md CHANGELOG.md .github/workflows/deploy-docs.yml" in source
    assert "git add data-mirror docs bin/deploy-docs README.md CHANGELOG.md .github/workflows/deploy-docs.yml" in source
