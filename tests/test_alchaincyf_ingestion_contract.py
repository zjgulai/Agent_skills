from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = REPO_ROOT / "docs" / "_src" / "alchaincyf-skill-manifest.json"


def _data() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_manifest_has_ingestion_summary_counts():
    data = _data()
    items = data["skills"]
    actions = Counter(item["action"] for item in items)
    modes = Counter(item["install_mode"] for item in items)
    summary = data["ingestion_summary"]

    assert summary["runtime_install_count"] == actions["install"] == 43
    assert summary["distill_only_count"] == actions["distill-only"] == 11
    assert summary["skip_count"] == actions["skip"] == 5
    assert summary["direct_root_install_count"] == modes["root"] == 22
    assert summary["subdir_install_count"] == modes["subdir"] == 1
    assert summary["monorepo_install_count"] == modes["monorepo"] == 20
    assert summary["duplicate_skip_count"] == 1


def test_manifest_marks_huashu_skills_as_monorepo():
    items = _data()["skills"]
    monorepo = [
        item
        for item in items
        if item["source_repo"] == "huashu-skills" and item["action"] == "install"
    ]

    assert len(monorepo) >= 20
    assert all(item["install_mode"] == "monorepo" for item in monorepo)
    assert "huashu-skills/huashu-design" not in {item["source_key"] for item in monorepo}


def test_manifest_marks_dukou_as_subdir_install():
    items = _data()["skills"]
    dukou = next(item for item in items if item["runtime_name"] == "dukou")

    assert dukou["install_mode"] == "subdir"
    assert dukou["subdir"] == "skill/dukou"


def test_distill_only_repos_are_not_runtime_installs():
    items = _data()["skills"]
    orange_books = [item for item in items if item["source_repo"].endswith("orange-book")]

    assert orange_books
    assert all(item["action"] == "distill-only" for item in orange_books)
    assert all(item["install_mode"] == "none" for item in orange_books)
