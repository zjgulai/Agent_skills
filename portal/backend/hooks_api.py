"""Hooks API: /api/hooks/* — read-only view over Agent_hook/registry/.

Companion repo path is resolved from env var AGENT_HOOK_REPO (preferred) or the
conventional sibling-directory layout ../Agent_hook. If neither exists, all
endpoints return a 503 with a clear diagnostic instead of crashing the app.
"""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

_DEFAULT_HOOK_REPO = Path(__file__).resolve().parents[3] / "Agent_hook"
AGENT_HOOK_REPO = Path(os.environ.get("AGENT_HOOK_REPO", str(_DEFAULT_HOOK_REPO)))

# Lazy-loaded module — None means companion repo is not configured/available.
_manifest = None
iter_registry = None
load_manifest = None


def _try_load_manifest_module() -> bool:
    """Attempt to import Agent_hook's manifest.py. Returns True on success."""
    global _manifest, iter_registry, load_manifest
    if _manifest is not None:
        return True
    manifest_path = AGENT_HOOK_REPO / "agent" / "lib" / "manifest.py"
    if not manifest_path.exists():
        return False
    mod_name = "agent_hook_lib_manifest"
    if mod_name in sys.modules:
        _manifest = sys.modules[mod_name]
    else:
        try:
            spec = importlib.util.spec_from_file_location(mod_name, manifest_path)
            if spec is None or spec.loader is None:
                sys.stderr.write(f"[hooks_api] cannot load spec from {manifest_path}\n")
                return False
            m = importlib.util.module_from_spec(spec)
            sys.modules[mod_name] = m
            spec.loader.exec_module(m)
            _manifest = m
        except Exception as e:
            sys.stderr.write(f"[hooks_api] failed to load manifest module: {e}\n")
            return False
    iter_registry = _manifest.iter_registry
    load_manifest = _manifest.load_manifest
    return True


def _require_companion() -> None:
    """Raise HTTP 503 if companion repo is not available."""
    if not _try_load_manifest_module():
        raise HTTPException(
            status_code=503,
            detail=(
                f"Agent_hook companion repo not found at {AGENT_HOOK_REPO}. "
                f"Set AGENT_HOOK_REPO env var or clone the repo alongside this project."
            ),
        )


router = APIRouter(prefix="/api/hooks", tags=["hooks"])


@router.get("/health")
def hooks_health() -> dict:
    repo_ok = AGENT_HOOK_REPO.exists()
    registry_ok = (AGENT_HOOK_REPO / "registry").exists()
    manifest_ok = _try_load_manifest_module()
    return {
        "ok": repo_ok and registry_ok and manifest_ok,
        "repo": str(AGENT_HOOK_REPO),
        "manifest_loaded": manifest_ok,
        "registered_count": len(list((AGENT_HOOK_REPO / "registry").glob("*/manifest.yaml")))
            if registry_ok else 0,
    }


@router.get("")
def list_hooks() -> dict:
    _require_companion()
    items = []
    for m in iter_registry(AGENT_HOOK_REPO, expected_kind="hook"):
        items.append({
            "name": m.name,
            "version": m.version,
            "description": m.description,
            "domain": m.domain,
            "priority": m.priority,
            "hook_events": m.hook_events,
            "matchers": m.matchers,
            "compatibility": m.compatibility,
            "requires": m.requires,
            "triggers": m.triggers,
            "links": m.links,
        })
    return {
        "kind": "hook",
        "repo": str(AGENT_HOOK_REPO),
        "count": len(items),
        "items": items,
    }


@router.get("/{name}")
def get_hook(name: str) -> dict:
    _require_companion()
    p = AGENT_HOOK_REPO / "registry" / name / "manifest.yaml"
    if not p.exists():
        raise HTTPException(status_code=404, detail=f"hook not found: {name}")
    m = load_manifest(p, expected_kind="hook")
    return {
        "name": m.name,
        "version": m.version,
        "description": m.description,
        "domain": m.domain,
        "priority": m.priority,
        "hook_events": m.hook_events,
        "matchers": m.matchers,
        "compatibility": m.compatibility,
        "requires": m.requires,
        "triggers": m.triggers,
        "links": m.links,
        "raw_manifest": m.raw,
    }


@router.get("/{name}/source", response_class=PlainTextResponse)
def get_hook_source(name: str) -> str:
    _require_companion()
    p = AGENT_HOOK_REPO / "registry" / name / "source" / "hook.py"
    if not p.exists():
        raise HTTPException(status_code=404, detail=f"hook source not found: {name}")
    return p.read_text(encoding="utf-8")
