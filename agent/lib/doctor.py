"""Health-check rules for installed skills.

Five rules per skill:
  R1 — frontmatter parses with required fields (name + description)
  R2 — frontmatter `name` matches directory name
  R3 — present in INDEX.md (under one of the 6 domains)
  R4 — present in skills-graph.mmd (and same domain as INDEX)
  R5 — declared dependencies exist (best-effort, only known deps)

Public API:
    check(name: str) -> CheckReport
    check_all() -> dict[str, CheckReport]

CLI: python -m agent.lib.doctor [name|all]
"""
from __future__ import annotations

import os
import pathlib
import re
import shutil
import sys
from dataclasses import dataclass, field
from typing import Optional

import yaml

from agent.lib.state_audit import audit_state

SKILLS_ROOT = pathlib.Path(os.path.expanduser("~/.config/opencode/skills"))

DEPENDENCY_HINTS = {
    "patent-disclosure-skill": [
        ("playwright", lambda: bool(_find_in_path("playwright")) or _python_module_available("playwright")),
        ("mmdc/mermaid", lambda: bool(shutil.which("mmdc")) or _has_local_mmdc("patent-disclosure-skill")),
    ],
    "software-copyright-materials": [
        (".NET (optional)", lambda: bool(shutil.which("dotnet"))),
    ],
    "native-feel-cross-platform-desktop": [],
    "agent-dev-kit-architecture-designer": [],
    "codex-review": [
        ("codex CLI", lambda: bool(shutil.which("codex"))),
    ],
    "startup-pressure-test": [],
    "guizang-ppt-skill": [
        ("node + npm", lambda: bool(shutil.which("node")) and bool(shutil.which("npm"))),
    ],
}


def _find_in_path(name: str) -> Optional[str]:
    return shutil.which(name)


def _python_module_available(modname: str) -> bool:
    portal_python = pathlib.Path(__file__).resolve().parents[2] / "portal" / "backend" / ".venv" / "bin" / "python"
    if not portal_python.exists():
        return False
    import subprocess
    r = subprocess.run([str(portal_python), "-c", f"import {modname}"],
                       capture_output=True, timeout=5)
    return r.returncode == 0


def _has_local_mmdc(skill_name: str) -> bool:
    candidate = SKILLS_ROOT / skill_name / "tools" / "node_modules" / ".bin" / "mmdc"
    return candidate.exists()


def _as_str_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple, set)):
        return [str(v) for v in value if str(v).strip()]
    return []


def _declared_dependency_hints(fm: dict) -> list[tuple[str, object]]:
    """Build dependency checks from optional frontmatter declarations.

    Supported shapes:
      requires:
        binaries: [node, npm]
        env: [OPENAI_API_KEY]
        python_modules: [yaml]

    Also accepts `commands` as an alias for `binaries`.
    """
    requires = fm.get("requires") or fm.get("dependencies") or {}
    if isinstance(requires, list):
        requires = {"binaries": requires}
    if not isinstance(requires, dict):
        return []

    checks: list[tuple[str, object]] = []
    for binary in _as_str_list(requires.get("binaries")) + _as_str_list(requires.get("commands")):
        checks.append((f"binary:{binary}", lambda binary=binary: bool(shutil.which(binary))))
    for env_name in _as_str_list(requires.get("env")):
        checks.append((f"env:{env_name}", lambda env_name=env_name: bool(os.environ.get(env_name))))
    for module in _as_str_list(requires.get("python_modules")):
        checks.append((f"python:{module}", lambda module=module: _python_module_available(module)))
    return checks


@dataclass
class CheckReport:
    name: str
    passed: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def overall(self) -> str:
        if self.failed:
            return "FAIL"
        if self.warnings:
            return "WARN"
        return "PASS"

    def to_dict(self) -> dict:
        return {"name": self.name, "overall": self.overall,
                "passed": self.passed, "failed": self.failed, "warnings": self.warnings}


def _parse_frontmatter(skill_md: pathlib.Path) -> Optional[dict]:
    try:
        text = skill_md.read_text(encoding="utf-8")
    except OSError:
        return None
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        return None
    try:
        fm = yaml.safe_load(m.group(1))
    except yaml.YAMLError:
        return _parse_minimal_frontmatter(m.group(1))
    if isinstance(fm, dict):
        return fm
    return _parse_minimal_frontmatter(m.group(1))


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


def _parse_minimal_frontmatter(raw: str) -> Optional[dict]:
    lines = raw.splitlines()
    name = _extract_minimal_scalar(lines, "name")
    description = _extract_minimal_scalar(lines, "description")
    if not name or not description:
        return None
    return {"name": name, "description": description}


def check(name: str) -> CheckReport:
    rep = CheckReport(name=name)

    skill_dir = SKILLS_ROOT / name
    skill_md = skill_dir / "SKILL.md"

    fm = _parse_frontmatter(skill_md) if skill_md.exists() else None
    if not fm or "name" not in fm or "description" not in fm:
        rep.failed.append("R1: SKILL.md frontmatter missing or invalid (need name + description)")
        return rep
    rep.passed.append("R1: frontmatter parses (name + description)")

    if fm.get("name") != name:
        rep.failed.append(f"R2: directory name '{name}' != frontmatter name '{fm['name']}'")
    else:
        rep.passed.append("R2: directory name matches frontmatter name")

    from agent.lib.index_md_writer import read_skills_by_domain
    by_domain = read_skills_by_domain()
    index_domain = next((d for d, names in by_domain.items() if name in names), None)
    if index_domain is None:
        rep.failed.append("R3: not present in INDEX.md (run /skill-classify or /skill-install)")
    else:
        rep.passed.append(f"R3: in INDEX.md under domain '{index_domain}'")

    from agent.lib.graph_writer import read_nodes
    nodes = read_nodes()
    graph_entry = next(((sid, info) for sid, info in nodes.items() if info["name"] == name), None)
    if graph_entry is None:
        rep.failed.append("R4: not present in skills-graph.mmd (run /skill-graph-sync)")
    else:
        sid, info = graph_entry
        if index_domain and info["domain"] != index_domain:
            rep.failed.append(
                f"R4: graph domain '{info['domain']}' != INDEX domain '{index_domain}' (run /skill-graph-sync)"
            )
        else:
            rep.passed.append(f"R4: in skills-graph.mmd as {sid} ({info['domain']})")

    deps = DEPENDENCY_HINTS.get(name, []) + _declared_dependency_hints(fm)
    if not deps:
        rep.passed.append("R5: no known external dependencies")
    else:
        for dep_name, check_fn in deps:
            try:
                ok = check_fn()
            except Exception as e:
                rep.warnings.append(f"R5: dependency check '{dep_name}' raised: {e}")
                continue
            if ok:
                rep.passed.append(f"R5: dependency '{dep_name}' present")
            else:
                rep.warnings.append(f"R5: dependency '{dep_name}' not found (skill may still work in degraded mode)")

    return rep


def check_all() -> dict[str, CheckReport]:
    out: dict[str, CheckReport] = {}
    for entry in sorted(SKILLS_ROOT.iterdir()):
        if not entry.is_dir():
            continue
        if not (entry / "SKILL.md").exists():
            continue
        out[entry.name] = check(entry.name)
    return out


def _state_audit_payload() -> dict:
    report = audit_state()
    return {
        "has_drift": report.has_drift,
        "installed_parseable_count": report.installed_parseable_count,
        "index_count": report.index_count,
        "graph_count": report.graph_count,
        "invalid_frontmatter": report.invalid_frontmatter,
        "parseable_not_indexed": report.parseable_not_indexed,
        "indexed_missing_or_invalid": report.indexed_missing_or_invalid,
        "index_missing_graph": report.index_missing_graph,
        "graph_extra": report.graph_extra,
        "graph_domain_mismatch": report.graph_domain_mismatch,
        "mirror_index_in_sync": report.mirror_index_in_sync,
        "mirror_graph_in_sync": report.mirror_graph_in_sync,
        "mirror_png_in_sync": report.mirror_png_in_sync,
        "docs_status_matches_parseable": report.docs_status_matches_parseable,
    }


def build_all_payload(*, include_state_audit: bool = True) -> dict:
    results = check_all()
    payload = {"skills": {n: r.to_dict() for n, r in results.items()}}
    if include_state_audit:
        payload["state_audit"] = _state_audit_payload()
    return payload


def _main(argv: list[str]) -> int:
    import json
    target = argv[0] if argv else "all"
    if target == "all":
        payload = build_all_payload(include_state_audit=True)
    else:
        payload = check(target).to_dict()
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
