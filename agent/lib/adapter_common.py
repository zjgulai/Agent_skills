from __future__ import annotations

import datetime as _dt
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def expand(p: str | Path) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(str(p))))


def resolve_source(manifest_raw: dict, repo_root: Path = REPO_ROOT) -> Path:
    src = manifest_raw.get("source") or {}
    t = src.get("type")
    if t in {"local"}:
        return repo_root / src["path"]
    if t == "external":
        return expand(src["path"])
    if t == "git":
        cache = expand("~/.cache/agent-skills") / src["ref"].replace("/", "_").replace("@", "-at-")
        sub = src.get("subpath") or ""
        return cache / sub if sub else cache
    raise ValueError(f"unknown source.type {t!r}")


def fetch_git_source(manifest_raw: dict, *, force: bool = False) -> Path:
    src = manifest_raw["source"]
    if src.get("type") != "git":
        return resolve_source(manifest_raw)
    ref = src["ref"]
    repo, _, branch = ref.partition("@")
    branch = branch or "main"
    cache_root = expand("~/.cache/agent-skills") / ref.replace("/", "_").replace("@", "-at-")
    if cache_root.exists() and not force:
        return cache_root / (src.get("subpath") or "")
    cache_root.parent.mkdir(parents=True, exist_ok=True)
    if cache_root.exists():
        shutil.rmtree(cache_root)
    url = f"https://github.com/{repo}.git"
    proc = subprocess.run(
        ["git", "clone", "--depth", "1", "--branch", branch, url, str(cache_root)],
        capture_output=True, text=True, timeout=60,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"git clone failed for {ref}: {proc.stderr.strip()}")
    return cache_root / (src.get("subpath") or "")


def make_symlink(target: Path, link: Path, *, force: bool = False) -> dict:
    if not target.exists():
        return {"linked": False, "reason": f"target missing: {target}"}
    link.parent.mkdir(parents=True, exist_ok=True)
    if link.exists() or link.is_symlink():
        if not force:
            if link.is_symlink() and link.resolve() == target.resolve():
                return {"linked": True, "noop": True, "link": str(link), "target": str(target)}
            return {"linked": False, "reason": f"link exists at {link} (use force)"}
        if link.is_symlink() or link.is_file():
            link.unlink()
        else:
            shutil.rmtree(link)
    link.symlink_to(target.resolve(), target_is_directory=target.is_dir())
    return {"linked": True, "link": str(link), "target": str(target.resolve())}


def remove_symlink_if_managed(link: Path, expected_target: Path) -> dict:
    if not link.exists() and not link.is_symlink():
        return {"removed": False, "reason": "not-found"}
    if not link.is_symlink():
        return {"removed": False, "reason": "not-a-symlink (refusing to delete real dir/file)"}
    actual = link.resolve()
    expected = expected_target.resolve() if expected_target.exists() else expected_target
    if actual != expected:
        return {"removed": False, "reason": f"symlink points to {actual}, not {expected}"}
    link.unlink()
    return {"removed": True, "link": str(link)}
