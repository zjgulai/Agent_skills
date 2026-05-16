"""Surgically read/write ~/.config/opencode/skills/INDEX.md.

Defense-in-depth contract:
  1. cp INDEX.md INDEX.md.bak.{timestamp_us} BEFORE any write (microsecond precision avoids same-second collision).
  2. Locate the right domain section by anchored regex on H3 heading.
  3. Locate the skills table by header pattern '| Skill |' inside the section.
  4. Use line-level splice to INSERT/REMOVE rows (preserves exact formatting).
  5. Post-write VALIDATION: re-parse must still find the change; revert from backup if not.
  6. Idempotent: append(name, domain) -> remove(name) returns INDEX.md byte-identical (test enforced).

Public API:
    read_skills_by_domain() -> dict[str, list[str]]
    append(name, domain, role, triggers) -> AppendResult
    remove(name) -> RemoveResult
    move(name, new_domain) -> MoveResult

CLI: python -m agent.lib.index_md_writer <command> [args...]
"""
from __future__ import annotations

import datetime as dt
import os
import pathlib
import re
import shutil
import sys
from dataclasses import dataclass
from typing import Optional

SKILLS_ROOT = pathlib.Path(os.path.expanduser("~/.config/opencode/skills"))
INDEX_MD = SKILLS_ROOT / "INDEX.md"

DOMAIN_LABEL_TO_ID = {
    "AI 工程基础设施": "meta",
    "代码质量与交付闭环": "closeout",
    "桌面应用工程": "desktop",
    "创业与产品验证": "founder",
    "知识产权交付": "ip",
    "工具增强": "tooling",
}
DOMAIN_ID_TO_LABEL = {v: k for k, v in DOMAIN_LABEL_TO_ID.items()}

EMPTY_PLACEHOLDER_TOOLING = (
    '> 暂为空。后续装的"通用 git 工作流"、"通用 release notes"、'
    '"通用 ai-slop 清理"等会归入此域（OpenCode 内置 skill 已经覆盖了 '
    '`git-master`、`review-work`、`ai-slop-remover`，所以你不需要重复装）。'
)
EMPTY_PLACEHOLDER_GENERIC = "> 暂为空。新装相关 skill 后会自动出现在这里。"

SKILL_LINK_RE = re.compile(r"\[([a-z0-9]+(?:-[a-z0-9]+)*)\]\(file://[^)]+SKILL\.md\)")
TABLE_DATA_ROW_RE = re.compile(r"^\|.*\|.*\|.*\|\s*$")
TABLE_HEADER_RE = re.compile(r"^\|\s*Skill\s*\|")
TABLE_SEP_RE = re.compile(r"^\|[\s|:-]+\|\s*$")
EMPTY_PLACEHOLDER_RE = re.compile(r"^>\s*暂为空")


@dataclass
class AppendResult:
    ok: bool
    message: str
    backup_path: Optional[str] = None
    inserted_at_line: Optional[int] = None


@dataclass
class RemoveResult:
    ok: bool
    message: str
    backup_path: Optional[str] = None
    removed_at_line: Optional[int] = None


@dataclass
class MoveResult:
    ok: bool
    message: str
    backup_path: Optional[str] = None


def _backup() -> pathlib.Path:
    ts = dt.datetime.now().strftime("%Y%m%dT%H%M%S%f")
    dst = INDEX_MD.with_suffix(f".md.bak.{ts}")
    shutil.copy2(INDEX_MD, dst)
    return dst


def _atomic_write(path: pathlib.Path, content: str) -> None:
    """Write content atomically via temp file + os.replace.

    Plain Path.write_text leaves dead bytes past logical EOF on macOS APFS,
    breaking byte-level comparisons (cmp/md5/shasum). Atomic replace fixes this.
    """
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)


def read_skills_by_domain() -> dict[str, list[str]]:
    text = INDEX_MD.read_text(encoding="utf-8")
    sections = re.split(r"^### ", text, flags=re.MULTILINE)
    out: dict[str, list[str]] = {d: [] for d in DOMAIN_LABEL_TO_ID.values()}
    for sec in sections:
        first_line = sec.split("\n", 1)[0]
        m = re.match(r"域\s*\d+\s*[·•]\s*([^（(]+)", first_line)
        if not m:
            continue
        label = m.group(1).strip()
        domain_id = next((v for k, v in DOMAIN_LABEL_TO_ID.items() if k in label), None)
        if not domain_id:
            continue
        for sn in SKILL_LINK_RE.findall(sec):
            if sn not in out[domain_id]:
                out[domain_id].append(sn)
    return out


def _find_domain_section_range(lines: list[str], domain_id: str) -> Optional[tuple[int, int]]:
    """Return (heading_line_idx, end_line_idx_exclusive) for the H3 section of domain_id.

    end_line is exclusive: it's the index of the next '### '/'## ' line, or len(lines).
    Returns None if domain heading not found.
    """
    label = DOMAIN_ID_TO_LABEL[domain_id]
    start = None
    for i, line in enumerate(lines):
        if line.startswith("### "):
            m = re.match(r"###\s*域\s*\d+\s*[·•]\s*(.+?)\s*$", line)
            if m and label in m.group(1):
                start = i
                break
    if start is None:
        return None
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("### ") or lines[j].startswith("## "):
            end = j
            break
    return (start, end)


def _find_table_in_section(lines: list[str], start: int, end: int) -> Optional[tuple[int, int, int]]:
    """Return (header_idx, sep_idx, last_data_or_sep_idx) for the skills table in [start, end).

    last_data_or_sep == sep_idx when the table has zero data rows.
    Returns None if no skills table found (e.g., '> 暂为空' placeholder).
    """
    i = start
    while i < end:
        if TABLE_HEADER_RE.match(lines[i]) and i + 1 < end and TABLE_SEP_RE.match(lines[i + 1]):
            header_idx = i
            sep_idx = i + 1
            j = sep_idx + 1
            last_data = sep_idx
            while j < end and TABLE_DATA_ROW_RE.match(lines[j]):
                last_data = j
                j += 1
            return (header_idx, sep_idx, last_data)
        i += 1
    return None


def _find_placeholder_in_section(lines: list[str], start: int, end: int) -> Optional[int]:
    for i in range(start, end):
        if EMPTY_PLACEHOLDER_RE.match(lines[i]):
            return i
    return None


def _build_row(name: str, role: str, triggers: str) -> str:
    skill_md = SKILLS_ROOT / name / "SKILL.md"
    link = f"[{name}](file://{skill_md})"
    return f"| {link} | {role} | {triggers} |"


def append(name: str, domain: str, role: str = "", triggers: str = "") -> AppendResult:
    if domain not in DOMAIN_ID_TO_LABEL:
        return AppendResult(False, f"unknown domain: {domain}")
    if not INDEX_MD.exists():
        return AppendResult(False, f"INDEX.md not found: {INDEX_MD}")

    existing = read_skills_by_domain()
    for d, names in existing.items():
        if name in names:
            return AppendResult(False, f"skill '{name}' already in domain '{d}'")

    backup = _backup()
    text = INDEX_MD.read_text(encoding="utf-8")
    lines = text.split("\n")

    rng = _find_domain_section_range(lines, domain)
    if not rng:
        return AppendResult(False, f"domain section not found in INDEX.md: {domain}",
                            backup_path=str(backup))
    sec_start, sec_end = rng

    new_row = _build_row(name, role, triggers)
    tbl = _find_table_in_section(lines, sec_start, sec_end)

    if tbl:
        _header, _sep, last_row = tbl
        lines.insert(last_row + 1, new_row)
        insert_at = last_row + 1
    else:
        ph_idx = _find_placeholder_in_section(lines, sec_start, sec_end)
        block = ["| Skill | 定位 | 主要触发词 |", "|---|---|---|", new_row]
        if ph_idx is not None:
            lines[ph_idx:ph_idx + 1] = block
            insert_at = ph_idx + 2
        else:
            insert_at = sec_start + 1
            for k in range(sec_start + 1, sec_end):
                if lines[k].strip().startswith("**何时进入"):
                    insert_at = k + 2
                    break
            lines[insert_at:insert_at] = [""] + block + [""]
            insert_at = insert_at + 3

    new_text = "\n".join(lines)
    _atomic_write(INDEX_MD, new_text)

    verify = read_skills_by_domain()
    if name not in verify.get(domain, []):
        shutil.copy2(backup, INDEX_MD)
        return AppendResult(False, f"post-write verification failed; reverted from {backup}",
                            backup_path=str(backup))

    return AppendResult(True, f"appended {name} to domain {domain}",
                        backup_path=str(backup), inserted_at_line=insert_at + 1)


def remove(name: str) -> RemoveResult:
    if not INDEX_MD.exists():
        return RemoveResult(False, f"INDEX.md not found: {INDEX_MD}")

    existing = read_skills_by_domain()
    target_domain = None
    for d, names in existing.items():
        if name in names:
            target_domain = d
            break
    if target_domain is None:
        return RemoveResult(False, f"skill '{name}' not present in any domain")

    backup = _backup()
    text = INDEX_MD.read_text(encoding="utf-8")
    lines = text.split("\n")

    target_idx = None
    for i, line in enumerate(lines):
        if TABLE_DATA_ROW_RE.match(line):
            m = SKILL_LINK_RE.search(line)
            if m and m.group(1) == name:
                target_idx = i
                break

    if target_idx is None:
        return RemoveResult(False, f"skill '{name}' not found in any INDEX.md table row",
                            backup_path=str(backup))

    rng = _find_domain_section_range(lines, target_domain)
    if not rng:
        return RemoveResult(False, f"domain section disappeared mid-op: {target_domain}",
                            backup_path=str(backup))
    sec_start, sec_end = rng

    del lines[target_idx]
    sec_end -= 1

    tbl = _find_table_in_section(lines, sec_start, sec_end)
    if tbl:
        header_idx, sep_idx, last_data = tbl
        if last_data == sep_idx:
            placeholder = (
                EMPTY_PLACEHOLDER_TOOLING if target_domain == "tooling"
                else EMPTY_PLACEHOLDER_GENERIC
            )
            del lines[header_idx:sep_idx + 1]
            lines.insert(header_idx, placeholder)

    new_text = "\n".join(lines)
    _atomic_write(INDEX_MD, new_text)

    verify = read_skills_by_domain()
    for d, names in verify.items():
        if name in names:
            shutil.copy2(backup, INDEX_MD)
            return RemoveResult(False, f"post-write verification: still present in {d}; reverted",
                                backup_path=str(backup))

    return RemoveResult(True, f"removed {name} from INDEX.md",
                        backup_path=str(backup), removed_at_line=target_idx + 1)


def move(name: str, new_domain: str) -> MoveResult:
    if new_domain not in DOMAIN_ID_TO_LABEL:
        return MoveResult(False, f"unknown domain: {new_domain}")
    existing = read_skills_by_domain()
    current_domain = None
    for d, names in existing.items():
        if name in names:
            current_domain = d
            break
    if not current_domain:
        return MoveResult(False, f"skill '{name}' not currently in INDEX.md")
    if current_domain == new_domain:
        return MoveResult(True, f"already in {new_domain}; no change")

    text = INDEX_MD.read_text(encoding="utf-8")
    lines = text.split("\n")
    row = None
    for line in lines:
        if TABLE_DATA_ROW_RE.match(line):
            m = SKILL_LINK_RE.search(line)
            if m and m.group(1) == name:
                row = line
                break
    if not row:
        return MoveResult(False, "row not located despite name match")

    parts = [p.strip() for p in row.strip("|").split("|")]
    role = parts[1] if len(parts) > 1 else ""
    triggers = parts[2] if len(parts) > 2 else ""

    rm_result = remove(name)
    if not rm_result.ok:
        return MoveResult(False, f"move failed at remove step: {rm_result.message}",
                          backup_path=rm_result.backup_path)
    ap_result = append(name, new_domain, role, triggers)
    if not ap_result.ok:
        return MoveResult(False, f"move failed at append step: {ap_result.message}",
                          backup_path=ap_result.backup_path)
    return MoveResult(True, f"moved {name}: {current_domain} → {new_domain}",
                      backup_path=ap_result.backup_path)


def _main(argv: list[str]) -> int:
    if not argv:
        print("usage: python -m agent.lib.index_md_writer "
              "<read | append NAME DOMAIN ROLE TRIGGERS | remove NAME | move NAME NEW_DOMAIN>",
              file=sys.stderr)
        return 2
    import json
    cmd = argv[0]
    if cmd == "read":
        print(json.dumps(read_skills_by_domain(), ensure_ascii=False, indent=2))
        return 0
    if cmd == "append":
        if len(argv) < 3:
            print("usage: append NAME DOMAIN [ROLE] [TRIGGERS]", file=sys.stderr); return 2
        r = append(argv[1], argv[2], argv[3] if len(argv) >= 4 else "", argv[4] if len(argv) >= 5 else "")
    elif cmd == "remove":
        if len(argv) < 2:
            print("usage: remove NAME", file=sys.stderr); return 2
        r = remove(argv[1])
    elif cmd == "move":
        if len(argv) < 3:
            print("usage: move NAME NEW_DOMAIN", file=sys.stderr); return 2
        r = move(argv[1], argv[2])
    else:
        print(f"unknown command: {cmd}", file=sys.stderr); return 2
    print(json.dumps({"ok": r.ok, "message": r.message,
                      "backup_path": getattr(r, "backup_path", None)},
                     ensure_ascii=False, indent=2))
    return 0 if r.ok else 1


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
