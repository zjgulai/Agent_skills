"""Regression checks for graph metadata writer block discovery."""
from __future__ import annotations

from agent.lib import graph_writer


def test_find_domain_block_accepts_legacy_tooling_heading():
    lines = [
        "flowchart LR",
        "    %% Tooling domain",
        "",
        "    GPS[guizang-ppt-skill]:::toolingDomain",
        "    JC[json-canvas]:::toolingDomain",
        "",
        "    %% Domain 6 - Builtin (referenced for context)",
        "    GM(git-master · builtin):::builtin",
    ]

    assert graph_writer._find_domain_block(lines, "tooling") == (1, 6)
