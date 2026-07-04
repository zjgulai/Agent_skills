"""Security boundaries for GitHub skill installation."""
from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "portal" / "backend"))

import installer  # noqa: E402


def _write_repo_skill(root: Path, name: str, description: str = "A test skill") -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {description}\n---\n\nBody\n",
        encoding="utf-8",
    )


def test_install_from_github_rejects_insecure_http_before_clone(tmp_path, monkeypatch):
    clone_called = False

    def fake_clone(url: str, dest: Path):
        nonlocal clone_called
        clone_called = True
        dest.mkdir(parents=True)
        return None

    monkeypatch.setattr(installer, "_clone_repo", fake_clone)

    result = installer.install_from_github("http://github.com/example/skill")

    assert not result.ok
    assert clone_called is False
    assert "https://github.com" in result.message


def test_install_monorepo_rejects_insecure_http_before_clone(tmp_path, monkeypatch):
    clone_called = False

    def fake_clone(url: str, dest: Path):
        nonlocal clone_called
        clone_called = True
        dest.mkdir(parents=True)
        return None

    monkeypatch.setattr(installer, "_clone_repo", fake_clone)

    result = installer.install_monorepo_from_github("http://github.com/example/skill")

    assert result["ok"] is False
    assert clone_called is False
    assert "https://github.com" in result["message"]


def test_install_one_rejects_existing_skill_without_explicit_overwrite(tmp_path, monkeypatch):
    skills_root = tmp_path / "skills"
    existing = skills_root / "existing-skill"
    _write_repo_skill(existing, "existing-skill", "Old description")

    repo = tmp_path / "repo"
    _write_repo_skill(repo, "existing-skill", "New description")

    monkeypatch.setattr(installer, "SKILLS_ROOT", skills_root)

    result = installer._install_one_from_clone(repo, "https://github.com/example/skill", None)

    assert result.ok is False
    assert "already exists" in result.message
    assert "Old description" in (existing / "SKILL.md").read_text(encoding="utf-8")


def test_install_one_allows_existing_skill_with_explicit_overwrite(tmp_path, monkeypatch):
    skills_root = tmp_path / "skills"
    existing = skills_root / "existing-skill"
    _write_repo_skill(existing, "existing-skill", "Old description")

    repo = tmp_path / "repo"
    _write_repo_skill(repo, "existing-skill", "New description")

    monkeypatch.setattr(installer, "SKILLS_ROOT", skills_root)

    result = installer._install_one_from_clone(
        repo,
        "https://github.com/example/skill",
        None,
        overwrite=True,
    )

    assert result.ok is True
    assert any("overwrote existing skill" in warning for warning in result.warnings)
    assert "New description" in (existing / "SKILL.md").read_text(encoding="utf-8")


def test_install_one_accepts_hook_heavy_frontmatter_when_minimal_fields_parse(tmp_path, monkeypatch):
    skills_root = tmp_path / "skills"
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)
    (repo / "SKILL.md").write_text(
        """---
name: hook-heavy-skill
description: Use when installing real-world skills whose hooks include shell strings.
hooks:
  PreToolUse:
    - command: "echo \\q"
---

Body
""",
        encoding="utf-8",
    )

    monkeypatch.setattr(installer, "SKILLS_ROOT", skills_root)

    result = installer._install_one_from_clone(repo, "https://github.com/example/skill", None)

    assert result.ok is True
    assert result.skill_name == "hook-heavy-skill"
    assert (skills_root / "hook-heavy-skill" / "SKILL.md").exists()
