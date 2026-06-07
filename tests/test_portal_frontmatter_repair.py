"""Portal API coverage for controlled SKILL.md frontmatter repair."""
from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "portal" / "backend"))

import app as portal_app  # noqa: E402


def test_patch_frontmatter_repairs_invalid_yaml_and_preserves_body(tmp_path, monkeypatch):
    skills_root = tmp_path / "skills"
    skill_dir = skills_root / "broken-skill"
    skill_dir.mkdir(parents=True)
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text(
        "---\n"
        "name: broken-skill\n"
        "description: invalid: yaml\n"
        "---\n\n"
        "# Broken Skill\n\n"
        "Keep this body.\n",
        encoding="utf-8",
    )

    refresh_called = False

    def fake_refresh():
        nonlocal refresh_called
        refresh_called = True
        return {"skill_count": 1, "generated_at": "now"}

    monkeypatch.setattr(portal_app, "SKILLS_ROOT", skills_root)
    monkeypatch.setattr(portal_app, "_refresh", fake_refresh)

    client = TestClient(portal_app.app)
    res = client.patch(
        "/api/skills/broken-skill/frontmatter",
        json={"description": "Fixed description: safe and quoted by YAML writer."},
    )

    assert res.status_code == 200
    payload = res.json()
    assert payload["ok"] is True
    assert payload["skill_name"] == "broken-skill"
    assert refresh_called is True
    assert list(skill_dir.glob("SKILL.md.bak.*"))

    text = skill_md.read_text(encoding="utf-8")
    assert "# Broken Skill" in text
    assert "Keep this body." in text
    assert "Fixed description" in text

    info = client.get("/api/skills/broken-skill")
    assert info.status_code == 200
    assert info.json()["frontmatter"]["description"].startswith("Fixed description")
