"""Skill installation utilities: from GitHub URL or local upload.

Discovery contract (depth ≤ 2):
  1. <repo>/SKILL.md
  2. <repo>/<subdir>/SKILL.md
"""
from __future__ import annotations

import pathlib
import re
import shutil
import subprocess
import tempfile
import uuid
from dataclasses import dataclass, field
from typing import Optional

from build_index import SKILLS_ROOT, parse_frontmatter

SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MAX_NAME_LEN = 64
MAX_DESC_LEN = 1024
SKIP_TOP_LEVEL = {".git", "LICENSE", "README.md", ".gitignore", "package.json"}


@dataclass
class InstallResult:
    ok: bool
    message: str
    skill_name: Optional[str] = None
    skill_dir: Optional[str] = None
    warnings: list[str] = field(default_factory=list)


def _validate_frontmatter(skill_md: pathlib.Path) -> tuple[Optional[dict], list[str]]:
    fm = parse_frontmatter(skill_md)
    errors: list[str] = []
    if not fm:
        return None, ["SKILL.md missing or has invalid YAML frontmatter (need name + description)"]
    name = str(fm.get("name", "")).strip()
    desc = str(fm.get("description", "")).strip()
    if not SKILL_NAME_RE.fullmatch(name):
        errors.append(f"name '{name}' does not match ^[a-z0-9]+(-[a-z0-9]+)*$")
    if not (1 <= len(name) <= MAX_NAME_LEN):
        errors.append(f"name length {len(name)} out of [1, {MAX_NAME_LEN}]")
    if not (1 <= len(desc) <= MAX_DESC_LEN):
        errors.append(f"description length {len(desc)} out of [1, {MAX_DESC_LEN}]")
    return fm, errors


def _find_skill_md(root: pathlib.Path) -> list[pathlib.Path]:
    candidates: list[pathlib.Path] = []
    direct = root / "SKILL.md"
    if direct.exists():
        candidates.append(direct)
    for child in sorted(root.iterdir()):
        if not child.is_dir() or child.name.startswith("."):
            continue
        nested = child / "SKILL.md"
        if nested.exists():
            candidates.append(nested)
    return candidates


def _copy_skill_content(src_dir: pathlib.Path, dest_dir: pathlib.Path) -> None:
    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    dest_dir.mkdir(parents=True)
    for entry in src_dir.iterdir():
        if entry.name in SKIP_TOP_LEVEL:
            continue
        if entry.name.startswith("."):
            continue
        target = dest_dir / entry.name
        if entry.is_dir():
            shutil.copytree(entry, target)
        else:
            shutil.copy2(entry, target)


def _strip_fence(text: str) -> str:
    text = text.lstrip()
    text = re.sub(r"^```[a-zA-Z]*\s*\n", "", text, count=1)
    text = text.rstrip()
    if text.endswith("```"):
        text = text[:-3].rstrip()
    return text + "\n"


def _clone_repo(url: str, dest: pathlib.Path) -> Optional[str]:
    """git clone --depth 1. Returns None on success, error message on failure."""
    env = {"GIT_TERMINAL_PROMPT": "0", "GIT_PAGER": "cat", "PATH": "/usr/bin:/usr/local/bin:/opt/homebrew/bin"}
    res = subprocess.run(
        ["git", "clone", "--depth", "1", url, str(dest)],
        capture_output=True, text=True, timeout=120, env=env,
    )
    if res.returncode != 0:
        return f"git clone failed: {res.stderr.strip()[:500]}"
    return None


def _install_one_from_clone(tmp_repo: pathlib.Path, url: str, subdir: Optional[str]) -> InstallResult:
    """Install one skill from an already-cloned repo. Pure local FS work, no network."""
    if subdir:
        search_root = tmp_repo / subdir
        if not search_root.is_dir():
            return InstallResult(False, f"subdir not found in repo: {subdir}")
    else:
        search_root = tmp_repo

    candidates = _find_skill_md(search_root)
    if not candidates:
        return InstallResult(False, "no SKILL.md found at depth ≤ 2")
    if len(candidates) > 1 and not subdir:
        relpaths = [str(c.parent.relative_to(tmp_repo)) for c in candidates]
        return InstallResult(
            False,
            f"multiple SKILL.md candidates: {relpaths}. Re-submit with 'subdir' to pick one.",
        )

    skill_md = candidates[0]
    skill_src_dir = skill_md.parent

    fm, errors = _validate_frontmatter(skill_md)
    if errors:
        return InstallResult(False, f"frontmatter validation failed: {'; '.join(errors)}")
    assert fm is not None
    name = fm["name"]
    dest = SKILLS_ROOT / name

    warnings = []
    if dest.exists():
        warnings.append(f"overwriting existing skill at {dest}")

    _copy_skill_content(skill_src_dir, dest)

    return InstallResult(
        ok=True,
        message=f"installed '{name}' from {url}" + (f" ({subdir})" if subdir else ""),
        skill_name=name,
        skill_dir=str(dest),
        warnings=warnings,
    )


def install_from_github(url: str, subdir: Optional[str] = None) -> InstallResult:
    if not url.startswith(("https://github.com/", "git@github.com:", "http://github.com/")):
        return InstallResult(False, f"only GitHub URLs supported, got: {url}")

    tmp_parent = pathlib.Path(tempfile.gettempdir()) / "skills-portal-clone"
    tmp_parent.mkdir(exist_ok=True)
    tmp_repo = tmp_parent / uuid.uuid4().hex[:8]

    try:
        err = _clone_repo(url, tmp_repo)
        if err:
            return InstallResult(False, err)
        return _install_one_from_clone(tmp_repo, url, subdir)
    finally:
        shutil.rmtree(tmp_repo, ignore_errors=True)


def install_monorepo_from_github(url: str, subdirs: Optional[list[str]] = None) -> dict:
    """Clone once, install many subdirs.

    If subdirs is None: auto-discover every directory containing a SKILL.md
    (one level under repo root, OR the root itself, OR <skills/*>/SKILL.md style).

    Returns {ok, message, total, succeeded, failed, results: [InstallResult-as-dict, ...]}.
    Failure of one subdir does NOT abort the rest.
    """
    if not url.startswith(("https://github.com/", "git@github.com:", "http://github.com/")):
        return {"ok": False, "message": f"only GitHub URLs supported, got: {url}",
                "total": 0, "succeeded": 0, "failed": 0, "results": []}

    tmp_parent = pathlib.Path(tempfile.gettempdir()) / "skills-portal-clone"
    tmp_parent.mkdir(exist_ok=True)
    tmp_repo = tmp_parent / uuid.uuid4().hex[:8]

    try:
        err = _clone_repo(url, tmp_repo)
        if err:
            return {"ok": False, "message": err,
                    "total": 0, "succeeded": 0, "failed": 0, "results": []}

        if subdirs is None:
            discovered: list[str] = []
            for skill_md in tmp_repo.rglob("SKILL.md"):
                if any(p.startswith(".") for p in skill_md.relative_to(tmp_repo).parts):
                    continue
                rel = skill_md.parent.relative_to(tmp_repo).as_posix()
                discovered.append(rel if rel != "." else "")
            subdirs = sorted(set(discovered))
            if not subdirs:
                return {"ok": False, "message": "no SKILL.md found in repo",
                        "total": 0, "succeeded": 0, "failed": 0, "results": []}

        results: list[dict] = []
        succeeded = 0
        failed = 0
        for sub in subdirs:
            sub_arg = sub if sub else None
            r = _install_one_from_clone(tmp_repo, url, sub_arg)
            entry = {
                "subdir": sub or "(root)",
                "ok": r.ok,
                "message": r.message,
                "skill_name": r.skill_name,
                "skill_dir": r.skill_dir,
                "warnings": r.warnings,
            }
            results.append(entry)
            if r.ok:
                succeeded += 1
            else:
                failed += 1

        return {
            "ok": failed == 0,
            "message": f"monorepo install: {succeeded} ok, {failed} failed (out of {len(subdirs)})",
            "total": len(subdirs),
            "succeeded": succeeded,
            "failed": failed,
            "results": results,
        }
    finally:
        shutil.rmtree(tmp_repo, ignore_errors=True)





def install_from_upload(filename: str, content: bytes) -> InstallResult:
    if not filename.lower().endswith(".md"):
        return InstallResult(False, f"upload must be a .md file, got: {filename}")

    raw = content.decode("utf-8", errors="replace")
    text = _strip_fence(raw)

    tmp = pathlib.Path(tempfile.mkdtemp(prefix="skills-portal-upload-"))
    try:
        tmp_md = tmp / "SKILL.md"
        tmp_md.write_text(text, encoding="utf-8")
        fm, errors = _validate_frontmatter(tmp_md)
        if errors:
            return InstallResult(False, f"frontmatter validation failed: {'; '.join(errors)}")
        assert fm is not None
        name = fm["name"]
        dest = SKILLS_ROOT / name

        warnings = []
        if dest.exists():
            warnings.append(f"overwriting existing skill at {dest}")

        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True)
        shutil.copy2(tmp_md, dest / "SKILL.md")

        return InstallResult(
            ok=True,
            message=f"installed '{name}' from upload {filename}",
            skill_name=name,
            skill_dir=str(dest),
            warnings=warnings,
        )
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def uninstall(name: str) -> InstallResult:
    if not SKILL_NAME_RE.fullmatch(name):
        return InstallResult(False, f"invalid name: {name}")
    target = SKILLS_ROOT / name
    if not target.exists() or not (target / "SKILL.md").exists():
        return InstallResult(False, f"skill not found: {name}")
    shutil.rmtree(target)
    return InstallResult(ok=True, message=f"uninstalled '{name}'", skill_name=name)
