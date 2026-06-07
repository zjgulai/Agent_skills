"""Read-only state audit for installed skills and metadata mirrors."""
from __future__ import annotations

import json
from pathlib import Path


SAMPLE_INDEX = """# Skills Index

### 域 1 · AI 工程基础设施

| Skill | 定位 | 主要触发词 |
|---|---|---|
| [indexed-a](file:///tmp/skills/indexed-a/SKILL.md) | indexed | indexed |
| [ghost-index](file:///tmp/skills/ghost-index/SKILL.md) | missing | missing |

### 域 2 · 代码质量与交付闭环

> 暂为空。新装相关 skill 后会自动出现在这里。

### 域 3 · 桌面应用工程

> 暂为空。新装相关 skill 后会自动出现在这里。

### 域 4 · 创业与产品验证

> 暂为空。新装相关 skill 后会自动出现在这里。

### 域 5 · 知识产权交付

> 暂为空。新装相关 skill 后会自动出现在这里。

### 域 6 · 工具增强

> 暂为空。新装相关 skill 后会自动出现在这里。
"""


def _write_skill(root: Path, name: str) -> None:
    skill_dir = root / name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: Skill {name}\n---\n\nBody\n",
        encoding="utf-8",
    )


def test_state_audit_reports_truth_source_drift(tmp_path):
    from agent.lib.state_audit import audit_state

    skills_root = tmp_path / "skills"
    skills_root.mkdir()
    _write_skill(skills_root, "indexed-a")
    _write_skill(skills_root, "missing-index")

    broken = skills_root / "broken-skill"
    broken.mkdir()
    (broken / "SKILL.md").write_text(
        "---\nname: broken-skill\ndescription: invalid: yaml\n---\n\nBody\n",
        encoding="utf-8",
    )

    index_md = skills_root / "INDEX.md"
    index_md.write_text(SAMPLE_INDEX, encoding="utf-8")

    graph_mmd = skills_root / "skills-graph.mmd"
    graph_mmd.write_text(
        "graph TD\n"
        "    IA[indexed-a]:::metaDomain\n"
        "    OG[orphan-graph]:::toolingDomain\n",
        encoding="utf-8",
    )

    mirror_dir = tmp_path / "data-mirror"
    mirror_dir.mkdir()
    (mirror_dir / "INDEX.md").write_text("# stale mirror\n", encoding="utf-8")

    docs_status_json = tmp_path / "docs" / "data" / "portal-status.json"
    docs_status_json.parent.mkdir(parents=True)
    docs_status_json.write_text(json.dumps({"skill_count": 99}), encoding="utf-8")

    report = audit_state(
        skills_root=skills_root,
        index_md=index_md,
        graph_mmd=graph_mmd,
        mirror_dir=mirror_dir,
        docs_status_json=docs_status_json,
    )

    assert report.installed_parseable_count == 2
    assert report.index_count == 2
    assert report.graph_count == 2
    assert "missing-index" in report.parseable_not_indexed
    assert "ghost-index" in report.indexed_missing_or_invalid
    assert "ghost-index" in report.index_missing_graph
    assert "orphan-graph" in report.graph_extra
    assert "broken-skill" in report.invalid_frontmatter
    assert report.mirror_index_in_sync is False
    assert report.docs_status_skill_count == 99
    assert report.docs_status_matches_parseable is False
    assert report.has_drift is True


def test_state_audit_metadata_only_ignores_missing_skill_dirs(tmp_path):
    from agent.lib.state_audit import audit_state

    root = tmp_path / "metadata"
    root.mkdir()
    index_md = root / "INDEX.md"
    index_md.write_text(SAMPLE_INDEX, encoding="utf-8")
    graph_mmd = root / "skills-graph.mmd"
    graph_mmd.write_text(
        "graph TD\n"
        "    IA[indexed-a]:::metaDomain\n"
        "    GI[ghost-index]:::metaDomain\n",
        encoding="utf-8",
    )
    graph_png = root / "skills-graph.png"
    graph_png.write_bytes(b"png")

    docs_status_json = tmp_path / "docs" / "data" / "portal-status.json"
    docs_status_json.parent.mkdir(parents=True)
    docs_status_json.write_text(json.dumps({"skill_count": 2}), encoding="utf-8")

    report = audit_state(
        skills_root=root,
        index_md=index_md,
        graph_mmd=graph_mmd,
        graph_png=graph_png,
        mirror_dir=root,
        docs_status_json=docs_status_json,
        metadata_only=True,
    )

    assert report.installed_parseable_count == 0
    assert report.index_count == 2
    assert report.graph_count == 2
    assert report.indexed_missing_or_invalid == []
    assert report.docs_status_matches_parseable is True
    assert report.has_drift is False
