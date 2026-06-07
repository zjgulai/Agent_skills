"""Static checks for frontend graph bundle boundaries."""
from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
GRAPH_VIEW = REPO_ROOT / "portal" / "frontend" / "src" / "components" / "GraphView.vue"


def test_graph_view_lazy_loads_mermaid_instead_of_static_import():
    source = GRAPH_VIEW.read_text(encoding="utf-8")

    assert "import mermaid from 'mermaid'" not in source
    assert "await import('mermaid')" in source
