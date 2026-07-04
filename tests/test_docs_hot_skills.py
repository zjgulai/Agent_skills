"""Regression checks for the weekly hot skills homepage section."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
WEEKLY_JSON = REPO_ROOT / "docs" / "_src" / "weekly-hot-skills.json"
BUILD_PY = REPO_ROOT / "docs" / "_src" / "build.py"


def _load_build_module():
    spec = importlib.util.spec_from_file_location("docs_build", BUILD_PY)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_weekly_hot_skills_data_contract():
    payload = json.loads(WEEKLY_JSON.read_text(encoding="utf-8"))

    assert payload["window"] == {
        "start": "2026-06-09",
        "end": "2026-06-16",
        "timezone": "America/Los_Angeles",
    }
    assert len(payload["groups"]) == 5
    assert len(payload["radar"]) == 8

    installed = [skill for group in payload["groups"] for skill in group["skills"]]
    assert len(installed) == 5
    assert len(installed) == len(set(installed))
    assert {
        "last30days",
        "planning-with-files",
        "md2wechat",
        "agnix",
        "anydesign",
    } <= set(installed)


def test_weekly_hot_skills_renders_bilingual_homepage_section():
    build = _load_build_module()
    payload = json.loads(WEEKLY_JSON.read_text(encoding="utf-8"))

    zh = build.render_weekly_hot_skills(payload, "zh")
    en = build.render_weekly_hot_skills(payload, "en")

    assert 'id="weekly-hot-skills"' in zh
    assert "本周热门 Skills Radar" in zh
    assert "Hot Skills Radar This Week" in en
    assert "weekly-hot-skills.json" in zh
    assert "last30days" in zh
    assert "anydesign" in en
