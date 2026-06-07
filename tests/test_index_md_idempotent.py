"""Idempotency tests for agent/lib/index_md_writer.py.

Critical contract: append(name, domain) -> remove(name) MUST yield byte-identical INDEX.md.
These tests use an isolated fixture INDEX.md so test runs never mutate the live
~/.config/opencode/skills/INDEX.md truth source.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agent.lib import index_md_writer  # noqa: E402

SAMPLE_INDEX = f"""# Skills Index

### 域 1 · AI 工程基础设施

| Skill | 定位 | 主要触发词 |
|---|---|---|
| [agent-dev-kit-architecture-designer](file:///tmp/skills/agent-dev-kit-architecture-designer/SKILL.md) | agent architecture | agent |

### 域 2 · 代码质量与交付闭环

| Skill | 定位 | 主要触发词 |
|---|---|---|
| [codex-review](file:///tmp/skills/codex-review/SKILL.md) | review | review |

### 域 3 · 桌面应用工程

{index_md_writer.EMPTY_PLACEHOLDER_GENERIC}

### 域 4 · 创业与产品验证

{index_md_writer.EMPTY_PLACEHOLDER_GENERIC}

### 域 5 · 知识产权交付

| Skill | 定位 | 主要触发词 |
|---|---|---|
| [patent-disclosure-skill](file:///tmp/skills/patent-disclosure-skill/SKILL.md) | patent | patent |
| [software-copyright-materials](file:///tmp/skills/software-copyright-materials/SKILL.md) | copyright | copyright |

### 域 6 · 工具增强

{index_md_writer.EMPTY_PLACEHOLDER_TOOLING}
"""


@pytest.fixture()
def isolated_index(tmp_path, monkeypatch):
    skills_root = tmp_path / "skills"
    skills_root.mkdir()
    index_md = skills_root / "INDEX.md"
    index_md.write_text(SAMPLE_INDEX, encoding="utf-8")
    snapshot = tmp_path / "INDEX-baseline.md"
    shutil.copy2(index_md, snapshot)

    monkeypatch.setattr(index_md_writer, "SKILLS_ROOT", skills_root)
    monkeypatch.setattr(index_md_writer, "INDEX_MD", index_md)

    yield snapshot, index_md

    for p in skills_root.glob("INDEX.md.bak.*"):
        p.unlink()


def _hash(path: Path) -> bytes:
    import hashlib
    return hashlib.md5(path.read_bytes()).digest()


def _restore(snapshot: Path, index_md: Path):
    tmp = index_md.with_suffix(".md.tmp")
    shutil.copy2(snapshot, tmp)
    tmp.replace(index_md)


def test_append_then_remove_byte_identical_for_empty_domain(isolated_index):
    baseline_snapshot, index_md = isolated_index
    _restore(baseline_snapshot, index_md)
    before = _hash(index_md)

    r = index_md_writer.append("test-skill-tooling-xyz", "tooling",
                                "test role", "test, trigger, list")
    assert r.ok, r.message

    r2 = index_md_writer.remove("test-skill-tooling-xyz")
    assert r2.ok, r2.message

    after = _hash(index_md)
    assert before == after, (
        f"INDEX.md not byte-identical after append+remove on empty domain"
    )


def test_append_then_remove_byte_identical_for_non_empty_domain(isolated_index):
    baseline_snapshot, index_md = isolated_index
    _restore(baseline_snapshot, index_md)
    before = _hash(index_md)

    r = index_md_writer.append("test-skill-meta-xyz", "meta",
                                "test role", "test, trigger")
    assert r.ok, r.message

    r2 = index_md_writer.remove("test-skill-meta-xyz")
    assert r2.ok, r2.message

    after = _hash(index_md)
    assert before == after


def test_move_then_back_byte_identical(isolated_index):
    baseline_snapshot, index_md = isolated_index
    _restore(baseline_snapshot, index_md)
    before = _hash(index_md)

    index_md_writer.append("mover-test-x", "tooling", "test role", "kw1, kw2")
    r1 = index_md_writer.move("mover-test-x", "meta")
    assert r1.ok, r1.message
    r2 = index_md_writer.move("mover-test-x", "tooling")
    assert r2.ok, r2.message
    r3 = index_md_writer.remove("mover-test-x")
    assert r3.ok, r3.message

    after = _hash(index_md)
    assert before == after


def test_read_returns_known_baseline_skills(isolated_index):
    baseline_snapshot, index_md = isolated_index
    _restore(baseline_snapshot, index_md)
    by_domain = index_md_writer.read_skills_by_domain()
    assert "agent-dev-kit-architecture-designer" in by_domain.get("meta", [])
    assert "codex-review" in by_domain.get("closeout", [])
    assert "patent-disclosure-skill" in by_domain.get("ip", [])
    assert "software-copyright-materials" in by_domain.get("ip", [])


def test_append_rejects_unknown_domain(isolated_index):
    baseline_snapshot, index_md = isolated_index
    _restore(baseline_snapshot, index_md)
    r = index_md_writer.append("test-skill", "nonsense-domain", "x", "y")
    assert not r.ok
    assert "unknown domain" in r.message


def test_remove_rejects_unknown_skill(isolated_index):
    baseline_snapshot, index_md = isolated_index
    _restore(baseline_snapshot, index_md)
    r = index_md_writer.remove("nonexistent-skill-xyzzy")
    assert not r.ok
