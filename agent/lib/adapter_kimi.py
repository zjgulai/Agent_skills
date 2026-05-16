from __future__ import annotations

import datetime as _dt
import json
import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib as _toml_r
else:
    import tomli as _toml_r
import tomli_w

from .adapter_common import fetch_git_source, resolve_source
from .manifest import Manifest

CLIENT_NAME = "kimi"
CONFIG_PATH = Path.home() / ".kimi" / "config.toml"
MANAGED_REGISTRY = Path.home() / ".kimi" / ".agent-skill-managed.json"


def _load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    with CONFIG_PATH.open("rb") as f:
        return _toml_r.load(f)


def _save_config(data: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CONFIG_PATH.open("wb") as f:
        tomli_w.dump(data, f)


def _load_registry() -> dict:
    if not MANAGED_REGISTRY.exists():
        return {}
    with MANAGED_REGISTRY.open("r", encoding="utf-8") as f:
        return json.load(f)


def _save_registry(data: dict) -> None:
    MANAGED_REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    with MANAGED_REGISTRY.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def _resolve_target(m: Manifest) -> Path:
    return fetch_git_source(m.raw) if m.source.get("type") == "git" else resolve_source(m.raw)


def install(m: Manifest) -> dict:
    if m.compatibility.get("kimi") == "unsupported":
        return {"client": CLIENT_NAME, "name": m.name, "skipped": True, "reason": "kimi=unsupported"}
    target = _resolve_target(m)
    if not target.exists():
        return {"client": CLIENT_NAME, "name": m.name, "added": False, "reason": f"source missing: {target}"}

    data = _load_config()
    dirs = data.get("extra_skill_dirs") or []
    if not isinstance(dirs, list):
        dirs = []
    parent = str(target.parent.resolve())
    if parent not in dirs:
        dirs.append(parent)
        data["extra_skill_dirs"] = dirs
        _save_config(data)
        added = True
    else:
        added = False

    reg = _load_registry()
    parent_users = reg.setdefault(parent, [])
    if m.name not in parent_users:
        parent_users.append(m.name)
    reg[parent] = parent_users
    _save_registry(reg)

    return {
        "client": CLIENT_NAME, "name": m.name,
        "added": added,
        "extra_skill_dir": parent,
        "skill_target": str(target.resolve()),
    }


def uninstall(m, name=None) -> dict:
    if m is None:
        return {"client": CLIENT_NAME, "name": name, "removed": False,
                "reason": "kimi uninstall needs manifest to know parent dir"}
    target = _resolve_target(m)
    parent = str(target.parent.resolve())

    reg = _load_registry()
    users = reg.get(parent, [])
    if m.name in users:
        users.remove(m.name)
    if users:
        reg[parent] = users
        _save_registry(reg)
        return {"client": CLIENT_NAME, "name": m.name, "removed": False,
                "reason": f"extra_skill_dir still has other agent-skill-managed skills: {users}"}
    reg.pop(parent, None)
    _save_registry(reg)

    data = _load_config()
    dirs = data.get("extra_skill_dirs") or []
    if parent in dirs:
        dirs = [d for d in dirs if d != parent]
        data["extra_skill_dirs"] = dirs
        _save_config(data)
        return {"client": CLIENT_NAME, "name": m.name, "removed": True, "extra_skill_dir": parent}
    return {"client": CLIENT_NAME, "name": m.name, "removed": False, "reason": "extra_skill_dir not present"}


def list_installed() -> list[dict]:
    data = _load_config()
    dirs = data.get("extra_skill_dirs") or []
    reg = _load_registry()
    out = []
    for d in dirs:
        p = Path(d)
        if not p.exists():
            continue
        managed_in_this_dir = set(reg.get(d, []))
        for sub in sorted(p.iterdir()):
            if (sub / "SKILL.md").exists():
                out.append({
                    "name": sub.name,
                    "managed": sub.name in managed_in_this_dir,
                    "is_symlink": False,
                    "skill_dir": str(sub),
                })
    return out


def status_for(name: str) -> str:
    for row in list_installed():
        if row["name"] == name:
            return "managed" if row["managed"] else "external"
    return "absent"
