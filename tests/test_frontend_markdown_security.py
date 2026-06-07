"""Static safety checks for Markdown rendering in the portal UI."""
from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_DETAIL = REPO_ROOT / "portal" / "frontend" / "src" / "components" / "SkillDetail.vue"


def test_skill_detail_sanitizes_marked_html_before_v_html():
    source = SKILL_DETAIL.read_text(encoding="utf-8")

    assert "DOMPurify" in source
    assert "DOMPurify.sanitize" in source
    assert "v-html=\"renderedHtml\"" in source
    assert "renderedHtml.value = await marked.parse" not in source
