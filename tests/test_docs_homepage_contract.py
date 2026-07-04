"""Contracts for the public static homepage and localized docs routing."""
from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup


REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS = REPO_ROOT / "docs"


def _soup(path: Path) -> BeautifulSoup:
    return BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")


def test_homepage_is_data_driven_skills_navigator():
    zh = _soup(DOCS / "zh" / "index.html")

    for required_id in [
        "operating-console",
        "capability-map",
        "alchaincyf-source-collection",
        "source-ledger",
        "skill-explorer",
        "workflow-explorer",
        "domain-overview",
        "graph-overview",
        "publish-readiness",
        "tencent-deploy",
    ]:
        assert zh.find(id=required_id), f"missing #{required_id}"

    html = str(zh)
    assert "../data/skills.json" in html
    assert "../data/domains.json" in html
    assert "../data/problem-workflows.json" in html
    assert "../data/alchaincyf-skill-manifest.json" in html
    assert "../assets/skills-graph.png" in html
    assert "Alchaincyf" in html
    assert "43" in html
    assert "task(load_skills=[" in html
    assert "data-skill-search" in html
    assert "data-domain-filter" in html
    assert "data-stage-filter" in html


def test_homepage_exposes_operating_console_product_shape():
    zh = _soup(DOCS / "zh" / "index.html")
    html = str(zh)

    assert "Skills 运营控制台" in html or "Skills Operating Console" in html
    assert "227" in html
    assert "50" in html
    assert "43" in html
    assert "source.alchaincyf-intake" in html
    assert "agentops.skill-generation-optimization" in html
    assert "design.html-native-production" in html
    assert "root / subdir / monorepo" in html
    assert "distill-only" in html
    assert "data-stat=\"source-runtime\"" in html
    assert "data-source-filter" in html


def test_localized_pages_link_to_localized_siblings_not_stale_root_pages():
    zh = _soup(DOCS / "zh" / "index.html")
    hrefs = {a.get("href") for a in zh.find_all("a", href=True)}

    assert "./handbook.html" in hrefs
    assert "./architecture.html" in hrefs
    assert "./getting-started.html" in hrefs
    assert "../handbook.html" not in hrefs
    assert "../architecture.html" not in hrefs
    assert "../getting-started.html" not in hrefs


def test_legacy_root_pages_redirect_to_localized_pages():
    for page in [
        "handbook.html",
        "getting-started.html",
        "architecture.html",
        "domains.html",
        "commands.html",
        "case-study.html",
    ]:
        html = (DOCS / page).read_text(encoding="utf-8")
        assert "window.location.replace" in html
        assert f"./en/{page}" in html
        assert f"./zh/{page}" in html
        assert "Skills Manager AI Agent" in html
