from __future__ import annotations

from pathlib import Path

from .adapter_common import fetch_git_source, make_symlink, remove_symlink_if_managed, resolve_source
from .manifest import Manifest

CLIENT_NAME = "codex"
SKILLS_DIR = Path.home() / ".codex" / "skills"


def _link_path(name: str) -> Path:
    return SKILLS_DIR / name


def install(m: Manifest) -> dict:
    if m.compatibility.get("codex") == "unsupported":
        return {"client": CLIENT_NAME, "name": m.name, "skipped": True, "reason": "codex=unsupported"}
    if m.source.get("type") == "git":
        target = fetch_git_source(m.raw)
    else:
        target = resolve_source(m.raw)
    if not target.exists():
        return {"client": CLIENT_NAME, "name": m.name, "linked": False,
                "reason": f"source missing: {target}"}
    link = _link_path(m.name)
    if ".system" in link.parts:
        return {"client": CLIENT_NAME, "name": m.name, "linked": False,
                "reason": "refusing to write into codex .system/ (reserved for codex builtins)"}
    return {"client": CLIENT_NAME, "name": m.name, **make_symlink(target, link)}


def uninstall(m, name=None) -> dict:
    n = m.name if m else name
    link = _link_path(n)
    if not link.is_symlink():
        return {"client": CLIENT_NAME, "name": n, "removed": False,
                "reason": "not-a-symlink-or-not-found"}
    if m:
        target = fetch_git_source(m.raw) if m.source.get("type") == "git" else resolve_source(m.raw)
        return {"client": CLIENT_NAME, "name": n, **remove_symlink_if_managed(link, target)}
    link.unlink()
    return {"client": CLIENT_NAME, "name": n, "removed": True}


def list_installed() -> list[dict]:
    if not SKILLS_DIR.exists():
        return []
    out = []
    for p in sorted(SKILLS_DIR.iterdir()):
        if p.name == ".system":
            continue
        is_link = p.is_symlink()
        out.append({
            "name": p.name,
            "managed": is_link,
            "is_symlink": is_link,
            "target": str(p.resolve()) if is_link else None,
        })
    return out


def status_for(name: str) -> str:
    p = _link_path(name)
    if p.is_symlink():
        return "managed"
    if p.exists() and p.is_dir():
        return "external"
    return "absent"
