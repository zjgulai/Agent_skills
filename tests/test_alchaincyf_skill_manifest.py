from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = REPO_ROOT / "docs" / "_src" / "alchaincyf-skill-manifest.json"


def _manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_alchaincyf_manifest_snapshot_counts_are_explicit():
    data = _manifest()

    assert data["source_owner"] == "alchaincyf"
    assert data["snapshot_date"] == "2026-07-04"
    assert data["repo_count"] == 70
    assert data["non_fork_count"] == 46
    assert data["fork_count"] == 24


def test_alchaincyf_manifest_has_unique_runtime_names():
    data = _manifest()
    names = [item["runtime_name"] for item in data["skills"] if item["action"] == "install"]

    assert names
    assert len(names) == len(set(names))


def test_alchaincyf_manifest_records_source_and_install_mode():
    data = _manifest()
    allowed_actions = {"install", "distill-only", "skip"}
    allowed_modes = {"root", "subdir", "monorepo", "none"}
    allowed_domains = {"meta", "closeout", "desktop", "founder", "ip", "tooling"}

    for item in data["skills"]:
        assert item["repo"].startswith("https://github.com/alchaincyf/")
        assert item["action"] in allowed_actions
        assert item["install_mode"] in allowed_modes
        assert item["domain"] in allowed_domains
        assert item["workflow_stage"]
        assert item["problem_node"]
