"""Surgically read/write ~/.config/opencode/skills/skills-graph.mmd and re-render PNG.

Defense-in-depth (mirrors index_md_writer):
  1. cp skills-graph.mmd .bak.{ts_us} BEFORE any write.
  2. Locate the right '%% Domain N - X' comment block.
  3. Line-level splice for node + edge insertions.
  4. Atomic write via os.replace (avoids macOS APFS dead-bytes-past-EOF).
  5. Idempotent: add_node(name, domain) -> remove_node(name) restores byte-identical mmd.

Public API:
    read_nodes() -> dict[short_id, dict(name, domain)]
    add_node(name, domain) -> AddResult
    remove_node(name) -> RemoveResult
    render() -> RenderResult           # writes skills-graph.png

CLI: python -m agent.lib.graph_writer <command> [args...]
"""
from __future__ import annotations

import datetime as dt
import os
import pathlib
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Optional

SKILLS_ROOT = pathlib.Path(os.path.expanduser("~/.config/opencode/skills"))
GRAPH_MMD = SKILLS_ROOT / "skills-graph.mmd"
GRAPH_PNG = SKILLS_ROOT / "skills-graph.png"
RENDER_PY = SKILLS_ROOT / "render-mermaid.py"

DOMAIN_TO_NUMBER = {
    "meta": 1, "closeout": 2, "desktop": 3, "founder": 4, "ip": 5, "tooling": 6,
}
DOMAIN_TO_LABEL = {
    "meta": "Meta", "closeout": "Closeout", "desktop": "Desktop",
    "founder": "Founder", "ip": "IP", "tooling": "Tooling",
}

DOMAIN_COLORS = {
    "meta":     {"fill": "#e3f2fd", "stroke": "#1976d2"},
    "closeout": {"fill": "#c8e6c9", "stroke": "#2e7d32"},
    "desktop":  {"fill": "#fff3e0", "stroke": "#e65100"},
    "founder":  {"fill": "#f3e5f5", "stroke": "#6a1b9a"},
    "ip":       {"fill": "#e0f2f1", "stroke": "#00695c"},
    "tooling":  {"fill": "#f5f5f5", "stroke": "#616161"},
}

NODE_LINE_RE = re.compile(r"^\s*([A-Z][A-Z0-9_]*)\[([a-z0-9][a-z0-9-]*)\]:::([a-z]+)Domain\s*$")
EDGE_LINE_RE = re.compile(r"^\s*([A-Z][A-Z0-9_]*)\s*[-=].*?\s*([A-Z][A-Z0-9_]*)\s*$")


@dataclass
class AddResult:
    ok: bool
    message: str
    backup_path: Optional[str] = None
    short_id: Optional[str] = None


@dataclass
class RemoveResult:
    ok: bool
    message: str
    backup_path: Optional[str] = None
    removed_short_id: Optional[str] = None


@dataclass
class RenderResult:
    ok: bool
    message: str
    png_bytes: Optional[int] = None


def _backup() -> pathlib.Path:
    ts = dt.datetime.now().strftime("%Y%m%dT%H%M%S%f")
    dst = GRAPH_MMD.with_suffix(f".mmd.bak.{ts}")
    shutil.copy2(GRAPH_MMD, dst)
    return dst


def _atomic_write(path: pathlib.Path, content: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)


def _short_id_from_name(name: str, taken: set[str]) -> str:
    """Derive a SHORT_ID from a skill name, avoiding collisions in `taken`.

    Strategy: first letter of each hyphen segment, uppercase.
    Fallback: append digits if collision.
    """
    base = "".join(seg[0].upper() for seg in name.split("-") if seg) or "X"
    base = re.sub(r"[^A-Z0-9_]", "", base) or "X"
    if base not in taken:
        return base
    for i in range(2, 100):
        candidate = f"{base}{i}"
        if candidate not in taken:
            return candidate
    raise RuntimeError(f"could not derive unique short_id for {name}")


def read_nodes() -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    if not GRAPH_MMD.exists():
        return out
    for line in GRAPH_MMD.read_text(encoding="utf-8").splitlines():
        m = NODE_LINE_RE.match(line)
        if m:
            short_id, name, domain = m.group(1), m.group(2), m.group(3)
            out[short_id] = {"name": name, "domain": domain}
    return out


def _find_domain_block(lines: list[str], domain: str) -> Optional[tuple[int, int]]:
    """Return (block_start, block_end_exclusive) for the '%% Domain N - X' comment block.

    Block ends at: blank line followed by another block, OR a '%% ---' divider, OR EOF.
    """
    label = DOMAIN_TO_LABEL[domain]
    num = DOMAIN_TO_NUMBER[domain]
    header_patterns = [
        re.compile(rf"^\s*%%\s*Domain\s+{num}\s*-\s*{label}\s*$"),
        re.compile(rf"^\s*%%\s*Domain\s*{num}\s*[-:]\s*{label}", re.IGNORECASE),
    ]
    start = None
    for i, line in enumerate(lines):
        for pat in header_patterns:
            if pat.match(line):
                start = i
                break
        if start is not None:
            break
    if start is None:
        return None
    end = len(lines)
    for j in range(start + 1, len(lines)):
        s = lines[j].strip()
        if s.startswith("%% Domain ") or s.startswith("%% ---") or s.startswith("%% ----"):
            end = j
            break
    return (start, end)


def _find_lifecycle_section(lines: list[str]) -> Optional[int]:
    for i, line in enumerate(lines):
        if "Lifecycle" in line and "%%" in line and "---" in line:
            return i
    return None


def _ensure_classdef(lines: list[str], domain: str) -> bool:
    """Insert classDef line for `domain` if missing. Returns True if a line was added."""
    needle = f"classDef {domain}Domain"
    for line in lines:
        if needle in line:
            return False
    color = DOMAIN_COLORS[domain]
    new_classdef = f"    classDef {domain}Domain fill:{color['fill']},stroke:{color['stroke']},color:#000"
    last_classdef = -1
    for i, line in enumerate(lines):
        if "classDef" in line:
            last_classdef = i
    insert_at = last_classdef + 1 if last_classdef >= 0 else 1
    lines.insert(insert_at, new_classdef)
    return True


def _create_domain_block(lines: list[str], domain: str) -> tuple[int, int]:
    """Create a new '%% Domain - Label' block in `lines`. Returns the new (start, end_exclusive).

    Insertion point: just before '%% Domain 6 - Builtin' if exists, else before '%% --- Lifecycle',
    else at end of node-definitions area.
    """
    label = DOMAIN_TO_LABEL[domain]
    insert_at = None
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith("%% Domain") and "Builtin" in s:
            insert_at = i
            break
    if insert_at is None:
        for i, line in enumerate(lines):
            if "%% --- Lifecycle" in line or "%% --- Cross-domain" in line:
                insert_at = i
                break
    if insert_at is None:
        insert_at = len(lines)

    while insert_at > 0 and lines[insert_at - 1].strip() == "":
        insert_at -= 1

    block = ["", f"    %% {label} domain", ""]
    lines[insert_at:insert_at] = block
    return (insert_at + 1, insert_at + 3)


def add_node(name: str, domain: str) -> AddResult:
    if domain not in DOMAIN_TO_NUMBER:
        return AddResult(False, f"unknown domain: {domain}")
    if not GRAPH_MMD.exists():
        return AddResult(False, f"graph mmd not found: {GRAPH_MMD}")

    existing = read_nodes()
    for sid, info in existing.items():
        if info["name"] == name:
            return AddResult(False, f"node for '{name}' already exists ({sid})", short_id=sid)

    short_id = _short_id_from_name(name, taken=set(existing.keys()))

    backup = _backup()
    text = GRAPH_MMD.read_text(encoding="utf-8")
    lines = text.split("\n")

    _ensure_classdef(lines, domain)

    blk = _find_domain_block(lines, domain)
    if not blk:
        blk = _create_domain_block(lines, domain)
    blk_start, blk_end = blk

    insert_at = blk_end
    for k in range(blk_end - 1, blk_start, -1):
        if lines[k].strip() != "":
            insert_at = k + 1
            break

    new_node_line = f"    {short_id}[{name}]:::{domain}Domain"
    lines.insert(insert_at, new_node_line)

    same_domain_nodes = [sid for sid, info in existing.items() if info["domain"] == domain]
    if same_domain_nodes:
        peer = same_domain_nodes[0]
        edge_line = f"    {short_id} -. \"同域\" .-> {peer}"
    else:
        edge_line = f"    {short_id} -. \"独立节点\" .-> {short_id}"

    edge_insert = len(lines)
    for k in range(insert_at + 1, len(lines)):
        if "%% --- Cross-domain" in lines[k] or "%% --- Lifecycle" in lines[k]:
            edge_insert = k
            break
    while edge_insert > 0 and lines[edge_insert - 1].strip() == "":
        edge_insert -= 1
    lines.insert(edge_insert, edge_line)

    new_text = "\n".join(lines)
    _atomic_write(GRAPH_MMD, new_text)

    verify = read_nodes()
    if short_id not in verify or verify[short_id]["name"] != name:
        shutil.copy2(backup, GRAPH_MMD)
        return AddResult(False, f"post-write verification failed; reverted from {backup}",
                         backup_path=str(backup))

    return AddResult(True, f"added node {short_id}={name} in domain {domain}",
                     backup_path=str(backup), short_id=short_id)


def _cleanup_empty_block(lines: list[str], domain: str) -> None:
    """If no nodes for `domain` remain, drop its block comment + classDef + adjacent blank lines."""
    domain_pattern = re.compile(rf":::{domain}Domain\b")
    for line in lines:
        if domain_pattern.search(line):
            return

    block_comment_re = re.compile(rf"^\s*%%.*\b{DOMAIN_TO_LABEL[domain]}\s*(domain)?\b", re.IGNORECASE)
    block_idx = next((i for i, l in enumerate(lines) if block_comment_re.match(l)
                      and "Builtin" not in l), None)
    if block_idx is not None:
        start = block_idx
        end = block_idx + 1
        while start > 0 and lines[start - 1].strip() == "":
            start -= 1
        while end < len(lines) and lines[end].strip() == "":
            end += 1
        del lines[start:end]
        lines.insert(start, "")

    cd_re = re.compile(rf"^\s*classDef\s+{domain}Domain\b")
    classdef_idx = next((i for i, l in enumerate(lines) if cd_re.match(l)), None)
    if classdef_idx is not None:
        del lines[classdef_idx]


def remove_node(name: str) -> RemoveResult:
    if not GRAPH_MMD.exists():
        return RemoveResult(False, f"graph mmd not found: {GRAPH_MMD}")

    existing = read_nodes()
    target_sid = None
    target_domain = None
    for sid, info in existing.items():
        if info["name"] == name:
            target_sid = sid
            target_domain = info["domain"]
            break
    if not target_sid:
        return RemoveResult(False, f"no node for '{name}' in mmd")

    backup = _backup()
    text = GRAPH_MMD.read_text(encoding="utf-8")
    lines = text.split("\n")

    sid_word_re = re.compile(rf"\b{re.escape(target_sid)}\b")
    keep: list[str] = []
    for line in lines:
        m = NODE_LINE_RE.match(line)
        if m and m.group(1) == target_sid:
            continue
        if sid_word_re.search(line):
            continue
        keep.append(line)

    _cleanup_empty_block(keep, target_domain)

    new_text = "\n".join(keep)
    _atomic_write(GRAPH_MMD, new_text)

    verify = read_nodes()
    if target_sid in verify:
        shutil.copy2(backup, GRAPH_MMD)
        return RemoveResult(False, "post-write verification: node still present; reverted",
                            backup_path=str(backup))

    return RemoveResult(True, f"removed node {target_sid}={name}",
                        backup_path=str(backup), removed_short_id=target_sid)


def render() -> RenderResult:
    if not GRAPH_MMD.exists():
        return RenderResult(False, f"mmd missing: {GRAPH_MMD}")
    if not RENDER_PY.exists():
        return RenderResult(False, f"render script missing: {RENDER_PY}")

    portal_python = pathlib.Path(__file__).resolve().parents[2] / "portal" / "backend" / ".venv" / "bin" / "python"
    if not portal_python.exists():
        return RenderResult(False, f"portal venv python missing: {portal_python}")

    proc = subprocess.run(
        [str(portal_python), str(RENDER_PY), str(GRAPH_MMD), str(GRAPH_PNG)],
        capture_output=True, text=True, timeout=120,
    )
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout)[-500:]
        return RenderResult(False, f"render failed (rc={proc.returncode}):\n{tail}")
    if not GRAPH_PNG.exists():
        return RenderResult(False, f"render claimed success but PNG not at {GRAPH_PNG}")
    size = GRAPH_PNG.stat().st_size
    return RenderResult(True, f"rendered {GRAPH_PNG} ({size} bytes)", png_bytes=size)


def _main(argv: list[str]) -> int:
    if not argv:
        print("usage: python -m agent.lib.graph_writer "
              "<read | add NAME DOMAIN | remove NAME | render>", file=sys.stderr)
        return 2
    import json
    cmd = argv[0]
    if cmd == "read":
        print(json.dumps(read_nodes(), ensure_ascii=False, indent=2)); return 0
    if cmd == "add":
        if len(argv) < 3: print("usage: add NAME DOMAIN", file=sys.stderr); return 2
        r = add_node(argv[1], argv[2])
    elif cmd == "remove":
        if len(argv) < 2: print("usage: remove NAME", file=sys.stderr); return 2
        r = remove_node(argv[1])
    elif cmd == "render":
        r = render()
    else:
        print(f"unknown: {cmd}", file=sys.stderr); return 2
    out = {"ok": r.ok, "message": r.message}
    for attr in ("backup_path", "short_id", "removed_short_id", "png_bytes"):
        v = getattr(r, attr, None)
        if v is not None: out[attr] = v
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if r.ok else 1


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
