from __future__ import annotations

from pathlib import Path

from .adapter_common import fetch_git_source, make_symlink, remove_symlink_if_managed, resolve_source
from .manifest import Manifest

CLIENT_NAME = "opencode"
SKILLS_DIR = Path.home() / ".config" / "opencode" / "skills"


def _link_path(name: str) -> Path:
    return SKILLS_DIR / name


def install(m: Manifest) -> dict:
    if m.source.get("type") == "external":
        target = resolve_source(m.raw)
        if not target.exists():
            return {"client": CLIENT_NAME, "name": m.name, "linked": False,
                    "reason": f"external source missing: {target}"}
        link = _link_path(m.name)
        if link.exists() and not link.is_symlink():
            return {"client": CLIENT_NAME, "name": m.name, "linked": True, "noop": True,
                    "reason": "skill is the source itself (already in opencode skills dir)"}
        result = make_symlink(target, link)
        return {"client": CLIENT_NAME, "name": m.name, **result}

    if m.source.get("type") == "local":
        target = resolve_source(m.raw)
        result = make_symlink(target, _link_path(m.name))
        return {"client": CLIENT_NAME, "name": m.name, **result}

    if m.source.get("type") == "git":
        target = fetch_git_source(m.raw)
        result = make_symlink(target, _link_path(m.name))
        return {"client": CLIENT_NAME, "name": m.name, **result}

    return {"client": CLIENT_NAME, "name": m.name, "linked": False,
            "reason": f"unsupported source type {m.source.get('type')!r}"}


def uninstall(m: Manifest | None, name: str | None = None) -> dict:
    if m is None and name is None:
        raise ValueError("must provide manifest or name")
    n = m.name if m else name
    link = _link_path(n)
    if m and m.source.get("type") == "external":
        target = resolve_source(m.raw)
        if link.exists() and not link.is_symlink():
            return {"client": CLIENT_NAME, "name": n, "removed": False,
                    "reason": "skill IS the source — refusing to delete (external type)"}
        result = remove_symlink_if_managed(link, target)
    elif m:
        target = resolve_source(m.raw) if m.source.get("type") == "local" else fetch_git_source(m.raw)
        result = remove_symlink_if_managed(link, target)
    else:
        if link.is_symlink():
            link.unlink()
            result = {"removed": True}
        else:
            result = {"removed": False, "reason": "not-a-symlink or not-found"}
    return {"client": CLIENT_NAME, "name": n, **result}


def list_installed() -> list[dict]:
    if not SKILLS_DIR.exists():
        return []
    out = []
    for p in sorted(SKILLS_DIR.iterdir()):
        if not p.is_dir() and not p.is_symlink():
            continue
        is_link = p.is_symlink()
        target = p.resolve() if is_link else None
        out.append({
            "name": p.name,
            "managed": is_link,
            "is_symlink": is_link,
            "target": str(target) if target else None,
        })
    return out


def status_for(name: str) -> str:
    p = _link_path(name)
    if p.is_symlink():
        return "managed"
    if p.exists() and p.is_dir():
        return "external"
    return "absent"
