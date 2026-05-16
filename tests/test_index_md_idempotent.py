"""Idempotency tests for agent/lib/index_md_writer.py.

Critical contract: append(name, domain) -> remove(name) MUST yield byte-identical INDEX.md.
This test runs on the LIVE INDEX.md but always restores from a snapshot at module teardown.
"""
from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agent.lib import index_md_writer  # noqa: E402

INDEX_MD = index_md_writer.INDEX_MD


@pytest.fixture(scope="module")
def baseline_snapshot():
    if not INDEX_MD.exists():
        pytest.skip(f"INDEX.md missing: {INDEX_MD}")
    snapshot = Path(tempfile.mkdtemp()) / "INDEX-baseline.md"
    shutil.copy2(INDEX_MD, snapshot)
    yield snapshot
    shutil.copy2(snapshot, INDEX_MD)
    for p in INDEX_MD.parent.glob("INDEX.md.bak.*"):
        p.unlink()


def _hash(path: Path) -> bytes:
    import hashlib
    return hashlib.md5(path.read_bytes()).digest()


def _restore(snapshot: Path):
    tmp = INDEX_MD.with_suffix(".md.tmp")
    shutil.copy2(snapshot, tmp)
    tmp.replace(INDEX_MD)


def test_append_then_remove_byte_identical_for_empty_domain(baseline_snapshot):
    _restore(baseline_snapshot)
    before = _hash(INDEX_MD)

    r = index_md_writer.append("test-skill-tooling-xyz", "tooling",
                                "test role", "test, trigger, list")
    assert r.ok, r.message

    r2 = index_md_writer.remove("test-skill-tooling-xyz")
    assert r2.ok, r2.message

    after = _hash(INDEX_MD)
    assert before == after, (
        f"INDEX.md not byte-identical after append+remove on empty domain"
    )


def test_append_then_remove_byte_identical_for_non_empty_domain(baseline_snapshot):
    _restore(baseline_snapshot)
    before = _hash(INDEX_MD)

    r = index_md_writer.append("test-skill-meta-xyz", "meta",
                                "test role", "test, trigger")
    assert r.ok, r.message

    r2 = index_md_writer.remove("test-skill-meta-xyz")
    assert r2.ok, r2.message

    after = _hash(INDEX_MD)
    assert before == after


def test_move_then_back_byte_identical(baseline_snapshot):
    _restore(baseline_snapshot)
    before = _hash(INDEX_MD)

    index_md_writer.append("mover-test-x", "tooling", "test role", "kw1, kw2")
    r1 = index_md_writer.move("mover-test-x", "meta")
    assert r1.ok, r1.message
    r2 = index_md_writer.move("mover-test-x", "tooling")
    assert r2.ok, r2.message
    r3 = index_md_writer.remove("mover-test-x")
    assert r3.ok, r3.message

    after = _hash(INDEX_MD)
    assert before == after


def test_read_returns_known_baseline_skills(baseline_snapshot):
    _restore(baseline_snapshot)
    by_domain = index_md_writer.read_skills_by_domain()
    assert "agent-dev-kit-architecture-designer" in by_domain.get("meta", [])
    assert "codex-review" in by_domain.get("closeout", [])
    assert "patent-disclosure-skill" in by_domain.get("ip", [])
    assert "software-copyright-materials" in by_domain.get("ip", [])


def test_append_rejects_unknown_domain(baseline_snapshot):
    _restore(baseline_snapshot)
    r = index_md_writer.append("test-skill", "nonsense-domain", "x", "y")
    assert not r.ok
    assert "unknown domain" in r.message


def test_remove_rejects_unknown_skill(baseline_snapshot):
    _restore(baseline_snapshot)
    r = index_md_writer.remove("nonexistent-skill-xyzzy")
    assert not r.ok
