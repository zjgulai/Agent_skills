"""Guardrails for INDEX.md writer parsing strategy."""
from __future__ import annotations

import inspect

from agent.lib import index_md_writer


def test_index_writer_uses_markdown_ast_for_domain_heading_scan():
    source = inspect.getsource(index_md_writer)

    assert "mistune.create_markdown(renderer=\"ast\")" in source
    assert "re.split(r\"^### \"" not in source
