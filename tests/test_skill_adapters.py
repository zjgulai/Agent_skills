import json
import shutil
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO))

from agent.lib import (
    adapter_codex,
    adapter_common,
    adapter_cursor,
    adapter_dispatch,
    adapter_kimi,
    adapter_opencode,
)
from agent.lib.manifest import load_manifest


@pytest.fixture
def make_manifest(tmp_path):
    import yaml

    def _factory(name, kind, source_path=None, **overrides):
        base = {
            "kind": "skill",
            "name": name,
            "version": "0.1.0",
            "description": "Test skill description for adapter unit tests, must be 20+ chars to pass schema validation.",
            "domain": "meta",
            "priority": "P0",
            "compatibility": {"opencode": "native", "codex": "native", "cursor": "native", "kimi": "native"},
            "source": {"type": kind, "path": source_path or str(tmp_path / "registry" / name / "source")},
        }
        if kind == "external":
            base["source"] = {"type": "external", "path": source_path or "/no/such/external"}
        if kind == "git":
            base["source"] = {"type": "git", "ref": source_path or "test/fake@main"}
        base.update(overrides)
        p = tmp_path / "registry" / name / "manifest.yaml"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(yaml.safe_dump(base), encoding="utf-8")
        return load_manifest(p, expected_kind="skill")
    return _factory


@pytest.fixture
def isolated_paths(monkeypatch, tmp_path):
    op = tmp_path / "opencode-skills"
    co = tmp_path / "codex-skills"
    cu = tmp_path / "cursor-skills"
    ki_cfg = tmp_path / "kimi-config.toml"
    ki_reg = tmp_path / "kimi-managed.json"
    monkeypatch.setattr(adapter_opencode, "SKILLS_DIR", op)
    monkeypatch.setattr(adapter_codex, "SKILLS_DIR", co)
    monkeypatch.setattr(adapter_cursor, "SKILLS_DIR", cu)
    monkeypatch.setattr(adapter_kimi, "CONFIG_PATH", ki_cfg)
    monkeypatch.setattr(adapter_kimi, "MANAGED_REGISTRY", ki_reg)
    return {"opencode": op, "codex": co, "cursor": cu, "kimi": ki_cfg, "kimi_reg": ki_reg}


def _make_local_source(tmp_path: Path, name: str = "test-skill") -> Path:
    src = tmp_path / "registry" / name / "source"
    src.mkdir(parents=True, exist_ok=True)
    (src / "SKILL.md").write_text(f"---\nname: {name}\ndescription: x\n---\n")
    return src.parent


def test_resolve_local_source(tmp_path, make_manifest):
    src = _make_local_source(tmp_path, "test-skill")
    m = make_manifest("test-skill", "local", source_path=str(src))
    p = adapter_common.resolve_source(m.raw)
    assert "test-skill" in str(p)


def test_resolve_external_source_expands_user():
    raw = {"source": {"type": "external", "path": "~/some/path"}}
    p = adapter_common.resolve_source(raw)
    assert str(p).startswith(str(Path.home()))


def test_make_symlink_creates(tmp_path):
    target = tmp_path / "target-dir"
    target.mkdir()
    link = tmp_path / "linkpoint"
    res = adapter_common.make_symlink(target, link)
    assert res["linked"] is True
    assert link.is_symlink()


def test_make_symlink_noop_on_existing_correct_link(tmp_path):
    target = tmp_path / "target-dir"
    target.mkdir()
    link = tmp_path / "linkpoint"
    link.symlink_to(target.resolve())
    res = adapter_common.make_symlink(target, link)
    assert res.get("noop") is True


def test_make_symlink_refuses_overwriting_existing(tmp_path):
    target = tmp_path / "target-dir"
    target.mkdir()
    link = tmp_path / "linkpoint"
    other = tmp_path / "other"
    other.mkdir()
    link.symlink_to(other)
    res = adapter_common.make_symlink(target, link)
    assert res["linked"] is False
    assert "exists" in res["reason"]


def test_remove_symlink_refuses_real_dir(tmp_path):
    real_dir = tmp_path / "skill-real"
    real_dir.mkdir()
    expected = tmp_path / "expected"
    res = adapter_common.remove_symlink_if_managed(real_dir, expected)
    assert res["removed"] is False
    assert "not-a-symlink" in res["reason"]


def test_opencode_install_local(tmp_path, make_manifest, isolated_paths):
    src = _make_local_source(tmp_path, "demo")
    m = make_manifest("demo", "local", source_path=str(src))
    res = adapter_opencode.install(m)
    assert res["linked"] is True, f"got {res}"
    link = isolated_paths["opencode"] / "demo"
    assert link.is_symlink()


def test_opencode_install_external_target_missing(tmp_path, make_manifest, isolated_paths):
    m = make_manifest("demo", "external", source_path="/no/such/path")
    res = adapter_opencode.install(m)
    assert res["linked"] is False
    assert "missing" in res["reason"]


def test_opencode_external_when_link_path_is_real_dir(tmp_path, make_manifest, isolated_paths):
    isolated_paths["opencode"].mkdir(parents=True, exist_ok=True)
    real_link_path = isolated_paths["opencode"] / "demo"
    real_link_path.mkdir()
    (real_link_path / "SKILL.md").write_text("# I am the source itself\n")

    m = make_manifest("demo", "external", source_path=str(real_link_path))
    res = adapter_opencode.install(m)
    assert res.get("noop") is True


def test_opencode_uninstall_managed_link(tmp_path, make_manifest, isolated_paths):
    src = _make_local_source(tmp_path, "demo")
    m = make_manifest("demo", "local", source_path=str(src))
    adapter_opencode.install(m)
    res = adapter_opencode.uninstall(m)
    assert res["removed"] is True


def test_codex_refuses_system_dir(tmp_path, make_manifest, isolated_paths, monkeypatch):
    monkeypatch.setattr(adapter_codex, "SKILLS_DIR", isolated_paths["codex"] / ".system")
    src = _make_local_source(tmp_path, "demo")
    m = make_manifest("demo", "local", source_path=str(src))
    res = adapter_codex.install(m)
    assert res["linked"] is False
    assert ".system" in res["reason"]


def test_cursor_install_then_uninstall(tmp_path, make_manifest, isolated_paths):
    src = _make_local_source(tmp_path, "demo")
    m = make_manifest("demo", "local", source_path=str(src))
    res = adapter_cursor.install(m)
    assert res["linked"] is True
    res2 = adapter_cursor.uninstall(m)
    assert res2["removed"] is True


def test_kimi_install_writes_extra_skill_dirs(tmp_path, make_manifest, isolated_paths):
    src = _make_local_source(tmp_path, "demo")
    m = make_manifest("demo", "local", source_path=str(src))
    res = adapter_kimi.install(m)
    assert res["added"] is True
    import tomli
    with isolated_paths["kimi"].open("rb") as f:
        data = tomli.load(f)
    assert any(str(src.parent.resolve()) == d for d in data.get("extra_skill_dirs", []))


def test_kimi_install_idempotent(tmp_path, make_manifest, isolated_paths):
    src = _make_local_source(tmp_path, "demo")
    m = make_manifest("demo", "local", source_path=str(src))
    adapter_kimi.install(m)
    res2 = adapter_kimi.install(m)
    assert res2["added"] is False


def test_kimi_uninstall_protects_siblings(tmp_path, make_manifest, isolated_paths):
    parent = tmp_path / "registry"
    for sib in ("demo", "sibling-skill"):
        d = parent / sib / "source"
        d.mkdir(parents=True, exist_ok=True)
        (d / "SKILL.md").write_text("---\nname: s\ndescription: x\n---\n")
    sib_demo_dir = parent / "demo"
    (sib_demo_dir / "SKILL.md").write_text("---\nname: demo\ndescription: x\n---\n")
    sib_other = parent / "sibling-skill"
    (sib_other / "SKILL.md").write_text("---\nname: sibling-skill\ndescription: x\n---\n")
    m_a = make_manifest("demo", "local", source_path=str(sib_demo_dir))
    m_b = make_manifest("sibling-skill", "local", source_path=str(sib_other))
    adapter_kimi.install(m_a)
    adapter_kimi.install(m_b)

    res = adapter_kimi.uninstall(m_a)
    assert res["removed"] is False
    assert "other agent-skill-managed" in res.get("reason", "")

    res2 = adapter_kimi.uninstall(m_b)
    assert res2["removed"] is True


def test_dispatch_install_all_codex_unsupported_skipped(tmp_path, make_manifest, isolated_paths):
    src = _make_local_source(tmp_path, "demo")
    m = make_manifest("demo", "local", source_path=str(src),
                       compatibility={"opencode": "native", "codex": "unsupported",
                                      "cursor": "native", "kimi": "native"})
    results = adapter_dispatch.install_all_clients(m)
    by_client = {r["client"]: r for r in results}
    assert by_client["codex"].get("skipped") is True


def test_real_registry_loads_all_registered_skills():
    from agent.lib.manifest import iter_registry
    repo = Path(__file__).parent.parent
    skills = list(iter_registry(repo, expected_kind="skill"))
    names = {s.name for s in skills}
    expected_p0 = {"code-review", "create-pr", "frontend-design", "skill-creator", "superpowers"}
    expected_p1 = {
        "agent-dev-kit-architecture-designer", "codex-review", "composition-patterns",
        "document-skills", "native-feel-cross-platform-desktop", "react-best-practices",
        "startup-pressure-test", "web-design-guidelines",
    }
    assert expected_p0.issubset(names), f"missing P0 skills: {expected_p0 - names}"
    assert expected_p1.issubset(names), f"missing P1 skills: {expected_p1 - names}"
    assert len(names) >= 13, f"expected at least 13 skills, got {len(names)}: {sorted(names)}"
