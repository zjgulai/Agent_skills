"""Read-only consistency audit for the Skills Manager state.

Compares five state surfaces without mutating any of them:
  - installed parseable skills under ~/.config/opencode/skills
  - INDEX.md domain rows
  - skills-graph.mmd nodes
  - data-mirror/ metadata files
  - docs/data/portal-status.json

CLI:
    python -m agent.lib.state_audit [--json] [--check]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import sys
from dataclasses import asdict, dataclass
from typing import Any, Optional

import yaml


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
SKILLS_ROOT = pathlib.Path(os.path.expanduser("~/.config/opencode/skills"))
INDEX_MD = SKILLS_ROOT / "INDEX.md"
GRAPH_MMD = SKILLS_ROOT / "skills-graph.mmd"
GRAPH_PNG = SKILLS_ROOT / "skills-graph.png"
DATA_MIRROR = PROJECT_ROOT / "data-mirror"
DOCS_STATUS_JSON = PROJECT_ROOT / "docs" / "data" / "portal-status.json"

DOMAIN_LABEL_TO_ID = {
    "AI 工程基础设施": "meta",
    "代码质量与交付闭环": "closeout",
    "代码质量": "closeout",
    "桌面应用工程": "desktop",
    "创业与产品验证": "founder",
    "知识产权交付": "ip",
    "工具增强": "tooling",
}

SKILL_LINK_RE = re.compile(r"\[([a-z0-9]+(?:-[a-z0-9]+)*)\]\(file://[^)]+SKILL\.md\)")
GRAPH_NODE_RE = re.compile(
    r"^\s*([A-Z][A-Z0-9_]*)\[([a-z0-9][a-z0-9-]*)\]:::([a-z]+)Domain\s*$"
)
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


@dataclass(frozen=True)
class StateAuditReport:
    generated_at: str
    skills_root: str
    index_md: str
    graph_mmd: str
    mirror_dir: str
    docs_status_json: str
    installed_parseable_count: int
    index_count: int
    graph_count: int
    invalid_frontmatter: list[str]
    parseable_not_indexed: list[str]
    indexed_missing_or_invalid: list[str]
    index_missing_graph: list[str]
    graph_extra: list[str]
    graph_domain_mismatch: list[dict[str, str]]
    mirror_index_in_sync: Optional[bool]
    mirror_graph_in_sync: Optional[bool]
    mirror_png_in_sync: Optional[bool]
    docs_status_skill_count: Optional[int]
    docs_status_generated_at: Optional[str]
    docs_status_matches_parseable: Optional[bool]
    has_drift: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _parse_skill_frontmatter(skill_md: pathlib.Path) -> tuple[Optional[str], Optional[str]]:
    try:
        text = skill_md.read_text(encoding="utf-8")
    except OSError as exc:
        return None, f"read failed: {exc}"

    match = FRONTMATTER_RE.match(text)
    if not match:
        return None, "missing YAML frontmatter"
    raw = match.group(1)
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        fallback = _parse_minimal_frontmatter(raw)
        if fallback:
            return fallback["name"], None
        return None, f"invalid YAML frontmatter: {exc.__class__.__name__}"
    if not isinstance(data, dict):
        fallback = _parse_minimal_frontmatter(raw)
        if fallback:
            return fallback["name"], None
        return None, "frontmatter is not a mapping"
    name = str(data.get("name", "")).strip()
    description = str(data.get("description", "")).strip()
    if not name or not description:
        return None, "frontmatter must include name and description"
    return name, None


def _strip_scalar_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1]
    return value.strip()


def _extract_minimal_scalar(lines: list[str], key: str) -> Optional[str]:
    for idx, line in enumerate(lines):
        match = re.match(rf"^{re.escape(key)}:\s*(.*)$", line)
        if not match:
            continue
        value = match.group(1).strip()
        if value in {">", ">-", ">|", "|", "|-"}:
            block: list[str] = []
            for next_line in lines[idx + 1:]:
                if re.match(r"^[A-Za-z_][A-Za-z0-9_-]*:\s*", next_line):
                    break
                if next_line.startswith((" ", "\t")):
                    block.append(next_line.strip())
            return " ".join(part for part in block if part).strip()
        return _strip_scalar_quotes(value)
    return None


def _parse_minimal_frontmatter(raw: str) -> Optional[dict[str, str]]:
    lines = raw.splitlines()
    name = _extract_minimal_scalar(lines, "name")
    description = _extract_minimal_scalar(lines, "description")
    if not name or not description:
        return None
    return {"name": name, "description": description}


def _read_installed(skills_root: pathlib.Path) -> tuple[dict[str, pathlib.Path], dict[str, str]]:
    installed: dict[str, pathlib.Path] = {}
    invalid: dict[str, str] = {}
    try:
        entries = sorted(skills_root.iterdir())
    except OSError:
        return installed, invalid

    for entry in entries:
        if not entry.is_dir():
            continue
        skill_md = entry / "SKILL.md"
        if not skill_md.exists():
            continue
        name, error = _parse_skill_frontmatter(skill_md)
        if error or not name:
            invalid[entry.name] = error or "unknown frontmatter error"
            continue
        installed[name] = entry
    return installed, invalid


def _parse_index(index_md: pathlib.Path) -> dict[str, str]:
    if not index_md.exists():
        return {}
    text = index_md.read_text(encoding="utf-8")
    sections = re.split(r"^### ", text, flags=re.MULTILINE)
    mapping: dict[str, str] = {}

    for section in sections:
        first_line = section.split("\n", 1)[0]
        match = re.match(r"域\s*\d+\s*[·•]\s*([^（(]+)", first_line)
        if not match:
            continue
        label = match.group(1).strip()
        domain_id = next((v for k, v in DOMAIN_LABEL_TO_ID.items() if k in label), None)
        if not domain_id:
            continue
        for skill_name in SKILL_LINK_RE.findall(section):
            mapping[skill_name] = domain_id
    return mapping


def _parse_graph(graph_mmd: pathlib.Path) -> dict[str, str]:
    if not graph_mmd.exists():
        return {}
    nodes: dict[str, str] = {}
    for line in graph_mmd.read_text(encoding="utf-8").splitlines():
        match = GRAPH_NODE_RE.match(line)
        if match:
            _short_id, name, domain = match.groups()
            nodes[name] = domain
    return nodes


def _same_bytes(left: pathlib.Path, right: pathlib.Path) -> Optional[bool]:
    if not left.exists() and not right.exists():
        return None
    if not left.exists() or not right.exists():
        return False
    return left.read_bytes() == right.read_bytes()


def _read_docs_status(docs_status_json: pathlib.Path) -> tuple[Optional[int], Optional[str]]:
    if not docs_status_json.exists():
        return None, None
    try:
        data = json.loads(docs_status_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None, None
    count = data.get("skill_count")
    generated_at = data.get("generated_at")
    return count if isinstance(count, int) else None, (
        generated_at if isinstance(generated_at, str) else None
    )


def audit_state(
    *,
    skills_root: pathlib.Path = SKILLS_ROOT,
    index_md: pathlib.Path | None = None,
    graph_mmd: pathlib.Path | None = None,
    graph_png: pathlib.Path | None = None,
    mirror_dir: pathlib.Path = DATA_MIRROR,
    docs_status_json: pathlib.Path = DOCS_STATUS_JSON,
    metadata_only: bool = False,
) -> StateAuditReport:
    index_md = index_md or skills_root / "INDEX.md"
    graph_mmd = graph_mmd or skills_root / "skills-graph.mmd"
    graph_png = graph_png or skills_root / "skills-graph.png"

    installed, invalid = ({}, {}) if metadata_only else _read_installed(skills_root)
    index_map = _parse_index(index_md)
    graph_map = _parse_graph(graph_mmd)

    installed_names = set(installed)
    index_names = set(index_map)
    graph_names = set(graph_map)

    parseable_not_indexed = [] if metadata_only else sorted(installed_names - index_names)
    indexed_missing_or_invalid = [] if metadata_only else sorted(index_names - installed_names)
    index_missing_graph = sorted(index_names - graph_names)
    graph_extra = sorted(graph_names - index_names)
    graph_domain_mismatch = sorted(
        (
            {"name": name, "index_domain": index_map[name], "graph_domain": graph_map[name]}
            for name in index_names & graph_names
            if index_map[name] != graph_map[name]
        ),
        key=lambda item: item["name"],
    )

    mirror_index_in_sync = _same_bytes(index_md, mirror_dir / "INDEX.md")
    mirror_graph_in_sync = _same_bytes(graph_mmd, mirror_dir / "skills-graph.mmd")
    mirror_png_in_sync = _same_bytes(graph_png, mirror_dir / "skills-graph.png")
    docs_skill_count, docs_generated_at = _read_docs_status(docs_status_json)
    expected_docs_count = len(index_map) if metadata_only else len(installed)
    docs_matches = None if docs_skill_count is None else docs_skill_count == expected_docs_count

    drift_flags = [
        bool(invalid),
        bool(parseable_not_indexed),
        bool(indexed_missing_or_invalid),
        bool(index_missing_graph),
        bool(graph_extra),
        bool(graph_domain_mismatch),
        mirror_index_in_sync is False,
        mirror_graph_in_sync is False,
        mirror_png_in_sync is False,
        docs_matches is False,
    ]

    return StateAuditReport(
        generated_at=dt.datetime.now(tz=dt.timezone.utc).isoformat(),
        skills_root=str(skills_root),
        index_md=str(index_md),
        graph_mmd=str(graph_mmd),
        mirror_dir=str(mirror_dir),
        docs_status_json=str(docs_status_json),
        installed_parseable_count=len(installed),
        index_count=len(index_map),
        graph_count=len(graph_map),
        invalid_frontmatter=sorted(invalid),
        parseable_not_indexed=parseable_not_indexed,
        indexed_missing_or_invalid=indexed_missing_or_invalid,
        index_missing_graph=index_missing_graph,
        graph_extra=graph_extra,
        graph_domain_mismatch=graph_domain_mismatch,
        mirror_index_in_sync=mirror_index_in_sync,
        mirror_graph_in_sync=mirror_graph_in_sync,
        mirror_png_in_sync=mirror_png_in_sync,
        docs_status_skill_count=docs_skill_count,
        docs_status_generated_at=docs_generated_at,
        docs_status_matches_parseable=docs_matches,
        has_drift=any(drift_flags),
    )


def _print_summary(report: StateAuditReport) -> None:
    print(f"state audit drift={str(report.has_drift).lower()}")
    print(f"  installed parseable: {report.installed_parseable_count}")
    print(f"  INDEX.md rows:       {report.index_count}")
    print(f"  graph nodes:         {report.graph_count}")
    print(f"  invalid frontmatter: {len(report.invalid_frontmatter)}")
    print(f"  parseable not INDEX: {len(report.parseable_not_indexed)}")
    print(f"  INDEX missing skill: {len(report.indexed_missing_or_invalid)}")
    print(f"  INDEX missing graph: {len(report.index_missing_graph)}")
    print(f"  graph extra:         {len(report.graph_extra)}")
    print(f"  domain mismatch:     {len(report.graph_domain_mismatch)}")
    print(f"  mirror INDEX sync:   {report.mirror_index_in_sync}")
    print(f"  mirror graph sync:   {report.mirror_graph_in_sync}")
    print(f"  mirror PNG sync:     {report.mirror_png_in_sync}")
    print(f"  docs skill count:    {report.docs_status_skill_count}")

    for label, values in [
        ("parseable_not_indexed", report.parseable_not_indexed),
        ("indexed_missing_or_invalid", report.indexed_missing_or_invalid),
        ("index_missing_graph", report.index_missing_graph),
        ("graph_extra", report.graph_extra),
        ("invalid_frontmatter", report.invalid_frontmatter),
    ]:
        if values:
            preview = ", ".join(values[:20])
            suffix = "" if len(values) <= 20 else f", ... (+{len(values) - 20})"
            print(f"  {label}: {preview}{suffix}")


def _main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    parser.add_argument("--check", action="store_true", help="exit 1 when drift is detected")
    parser.add_argument("--metadata-only", action="store_true",
                        help="skip installed skill directory checks; validate INDEX/graph/mirror/docs only")
    parser.add_argument("--skills-root", type=pathlib.Path, default=SKILLS_ROOT)
    parser.add_argument("--index-md", type=pathlib.Path, default=None)
    parser.add_argument("--graph-mmd", type=pathlib.Path, default=None)
    parser.add_argument("--graph-png", type=pathlib.Path, default=None)
    parser.add_argument("--mirror-dir", type=pathlib.Path, default=DATA_MIRROR)
    parser.add_argument("--docs-status-json", type=pathlib.Path, default=DOCS_STATUS_JSON)
    args = parser.parse_args(argv)

    report = audit_state(
        skills_root=args.skills_root,
        index_md=args.index_md,
        graph_mmd=args.graph_mmd,
        graph_png=args.graph_png,
        mirror_dir=args.mirror_dir,
        docs_status_json=args.docs_status_json,
        metadata_only=args.metadata_only,
    )
    if args.json:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    else:
        _print_summary(report)
    return 1 if args.check and report.has_drift else 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
