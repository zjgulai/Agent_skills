"""Hooks API: /api/hooks/* — read-only view over Agent_hook/registry/."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

AGENT_HOOK_REPO = Path("/Users/lute/project/Agent/Agent_hook")


def _load_manifest_module():
    mod_name = "agent_hook_lib_manifest"
    if mod_name in sys.modules:
        return sys.modules[mod_name]
    spec = importlib.util.spec_from_file_location(
        mod_name, AGENT_HOOK_REPO / "agent" / "lib" / "manifest.py"
    )
    m = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = m
    spec.loader.exec_module(m)
    return m


_manifest = _load_manifest_module()
iter_registry = _manifest.iter_registry
load_manifest = _manifest.load_manifest


router = APIRouter(prefix="/api/hooks", tags=["hooks"])


@router.get("/health")
def hooks_health() -> dict:
    repo_ok = AGENT_HOOK_REPO.exists()
    registry_ok = (AGENT_HOOK_REPO / "registry").exists()
    return {
        "ok": repo_ok and registry_ok,
        "repo": str(AGENT_HOOK_REPO),
        "registered_count": len(list((AGENT_HOOK_REPO / "registry").glob("*/manifest.yaml")))
            if registry_ok else 0,
    }


@router.get("")
def list_hooks() -> dict:
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
    p = AGENT_HOOK_REPO / "registry" / name / "source" / "hook.py"
    if not p.exists():
        raise HTTPException(status_code=404, detail=f"hook source not found: {name}")
    return p.read_text(encoding="utf-8")
