"""Scan ~/.config/opencode/skills/ and emit data/skills-data.json.

Run as script: `python build_index.py`
Call as lib:   `from build_index import build`
"""
from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import re
from typing import Any, Optional

import yaml

SKILLS_ROOT = pathlib.Path(os.path.expanduser("~/.config/opencode/skills"))
DATA_FILE = pathlib.Path(__file__).parent / "data" / "skills-data.json"

DOMAIN_DEFAULTS = {
    "meta":     {"label": "AI 工程基础设施",    "color": "#e3f2fd", "stroke": "#1976d2"},
    "closeout": {"label": "代码质量与交付闭环",  "color": "#c8e6c9", "stroke": "#2e7d32"},
    "desktop":  {"label": "桌面应用工程",       "color": "#fff3e0", "stroke": "#e65100"},
    "founder":  {"label": "创业与产品验证",     "color": "#f3e5f5", "stroke": "#6a1b9a"},
    "ip":       {"label": "知识产权交付",       "color": "#e0f2f1", "stroke": "#00695c"},
    "tooling":  {"label": "工具增强 (横切层)",  "color": "#f5f5f5", "stroke": "#616161"},
    "uncategorized": {"label": "未分类", "color": "#fafafa", "stroke": "#9e9e9e"},
}

DOMAIN_LABEL_TO_ID = {
    "AI 工程基础设施": "meta",
    "代码质量与交付闭环": "closeout",
    "代码质量": "closeout",
    "桌面应用工程": "desktop",
    "创业与产品验证": "founder",
    "知识产权交付": "ip",
    "工具增强": "tooling",
}


def parse_frontmatter(skill_md: pathlib.Path) -> Optional[dict[str, Any]]:
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
        return None
    if not isinstance(fm, dict) or "name" not in fm or "description" not in fm:
        return None
    return fm


def extract_triggers(description: str) -> list[str]:
    candidates: list[str] = []
    candidates += re.findall(r"`([^`]{1,40})`", description)
    candidates += re.findall(r'"([^"]{2,40})"', description)
    candidates += re.findall(r"『([^』]{2,40})』", description)
    seen: set[str] = set()
    out: list[str] = []
    for t in candidates:
        t = t.strip()
        if t and t.lower() not in seen:
            out.append(t)
            seen.add(t.lower())
    return out[:12]


def parse_index_md(index_md: pathlib.Path) -> dict[str, dict[str, Any]]:
    """Map skill name -> domain by scanning INDEX.md '### 域 N · XXX' sections.

    Contract: each domain section uses '### 域 N · 名字' as header.
    Each skill is referenced by markdown link `[name](file://...SKILL.md)`.
    """
    if not index_md.exists():
        return {}
    text = index_md.read_text(encoding="utf-8")

    sections = re.split(r"^### ", text, flags=re.MULTILINE)
    mapping: dict[str, dict[str, Any]] = {}

    for sec in sections:
        first_line = sec.split("\n", 1)[0]
        m = re.match(r"域\s*\d+\s*[·•]\s*([^（(]+)", first_line)
        if not m:
            continue
        label = m.group(1).strip()
        domain_id = next((v for k, v in DOMAIN_LABEL_TO_ID.items() if k in label), None)
        if not domain_id:
            continue
        skill_links = re.findall(
            r"\[([a-z0-9]+(?:-[a-z0-9]+)*)\]\(file://[^)]+SKILL\.md\)",
            sec,
        )
        for sn in skill_links:
            mapping[sn] = {"domain_id": domain_id, "domain_label": label}

    return mapping


def collect_resources(skill_dir: pathlib.Path) -> list[dict[str, str]]:
    out = []
    for entry in sorted(skill_dir.iterdir()):
        if entry.name == "SKILL.md" or entry.name.startswith("."):
            continue
        kind = "dir" if entry.is_dir() else "file"
        out.append({"kind": kind, "name": entry.name, "path": str(entry)})
    return out


def collect_skill(skill_dir: pathlib.Path, idx_map: dict) -> Optional[dict[str, Any]]:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return None
    fm = parse_frontmatter(skill_md)
    if not fm:
        return None
    name = fm["name"]
    description = str(fm.get("description", "")).strip()
    info = idx_map.get(name, {})
    warnings = []
    if name != skill_dir.name:
        warnings.append(
            f"directory name '{skill_dir.name}' does not match frontmatter name '{name}'"
        )
    return {
        "name": name,
        "domain": info.get("domain_id") or "uncategorized",
        "description": description,
        "triggers": extract_triggers(description),
        "skill_md_path": str(skill_md),
        "skill_dir": str(skill_dir),
        "resources": collect_resources(skill_dir),
        "installed_at": dt.datetime.fromtimestamp(skill_dir.stat().st_mtime).isoformat(),
        "warnings": warnings,
    }


def read_graph_source() -> str:
    src = SKILLS_ROOT / "skills-graph.mmd"
    if src.exists():
        return src.read_text(encoding="utf-8")
    idx = SKILLS_ROOT / "INDEX.md"
    if idx.exists():
        text = idx.read_text(encoding="utf-8")
        m = re.search(r"```mermaid\n(.*?)\n```", text, re.DOTALL)
        if m:
            return m.group(1)
    return ""


def build() -> dict[str, Any]:
    idx_map = parse_index_md(SKILLS_ROOT / "INDEX.md")

    skills: list[dict[str, Any]] = []
    for entry in sorted(SKILLS_ROOT.iterdir()):
        if not entry.is_dir():
            continue
        info = collect_skill(entry, idx_map)
        if info:
            skills.append(info)

    domain_order = ["meta", "closeout", "desktop", "founder", "ip", "tooling", "uncategorized"]
    domains_payload = []
    for d_id in domain_order:
        names = [s["name"] for s in skills if s["domain"] == d_id]
        if not names and d_id == "uncategorized":
            continue
        defaults = DOMAIN_DEFAULTS[d_id]
        domains_payload.append({
            "id": d_id,
            "label": defaults["label"],
            "color": defaults["color"],
            "stroke": defaults["stroke"],
            "skill_names": names,
        })

    payload = {
        "generated_at": dt.datetime.now().isoformat(),
        "skills_root": str(SKILLS_ROOT),
        "skill_count": len(skills),
        "domains": domains_payload,
        "skills": skills,
        "graph": {
            "mermaid_source": read_graph_source(),
            "png_path": str(SKILLS_ROOT / "skills-graph.png"),
        },
    }

    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


if __name__ == "__main__":
    p = build()
    print(f"wrote {DATA_FILE}")
    print(f"  skills: {p['skill_count']}")
    print(f"  domains: {[d['id'] for d in p['domains']]}")
    print(f"  graph: {len(p['graph']['mermaid_source'])} chars")
