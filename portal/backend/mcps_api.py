"""MCPs API: /api/mcps/* — read-only view over Agent_mcp/registry/.

Companion repo path resolves from env var AGENT_MCP_REPO or sibling-dir convention.
Missing repo degrades to HTTP 503 instead of crashing app startup.
"""
from __future__ import annotations

import importlib.util
import os
import shutil
import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException

_DEFAULT_MCP_REPO = Path(__file__).resolve().parents[4] / "Agent_mcp"
AGENT_MCP_REPO = Path(os.environ.get("AGENT_MCP_REPO", str(_DEFAULT_MCP_REPO)))

_manifest = None
iter_registry = None
load_manifest = None


def _try_load_manifest_module() -> bool:
    """Attempt to import Agent_mcp's manifest.py. Returns True on success."""
    global _manifest, iter_registry, load_manifest
    if _manifest is not None:
        return True
    manifest_path = AGENT_MCP_REPO / "agent" / "lib" / "manifest.py"
    if not manifest_path.exists():
        return False
    mod_name = "agent_mcp_lib_manifest"
    if mod_name in sys.modules:
        _manifest = sys.modules[mod_name]
    else:
        try:
            spec = importlib.util.spec_from_file_location(mod_name, manifest_path)
            m = importlib.util.module_from_spec(spec)
            sys.modules[mod_name] = m
            spec.loader.exec_module(m)
            _manifest = m
        except Exception as e:
            sys.stderr.write(f"[mcps_api] failed to load manifest module: {e}\n")
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
                f"Agent_mcp companion repo not found at {AGENT_MCP_REPO}. "
                f"Set AGENT_MCP_REPO env var or clone the repo alongside this project."
            ),
        )


def _env_status(env_names) -> dict:
    return {name: bool(os.environ.get(name)) for name in env_names}


def _binary_status(binaries) -> dict:
    return {b: bool(shutil.which(b)) for b in binaries}


router = APIRouter(prefix="/api/mcps", tags=["mcps"])


@router.get("/health")
def mcps_health() -> dict:
    repo_ok = AGENT_MCP_REPO.exists()
    registry_ok = (AGENT_MCP_REPO / "registry").exists()
    manifest_ok = _try_load_manifest_module()
    return {
        "ok": repo_ok and registry_ok and manifest_ok,
        "repo": str(AGENT_MCP_REPO),
        "manifest_loaded": manifest_ok,
        "registered_count": len(list((AGENT_MCP_REPO / "registry").glob("*/manifest.yaml")))
            if registry_ok else 0,
    }


@router.get("")
def list_mcps() -> dict:
    _require_companion()
    items = []
    for m in iter_registry(AGENT_MCP_REPO, expected_kind="mcp"):
        env_names = m.requires.get("env", [])
        bins = m.requires.get("binaries", [])
        items.append({
            "name": m.name,
            "version": m.version,
            "description": m.description,
            "domain": m.domain,
            "priority": m.priority,
            "mcp_command": m.mcp_command,
            "compatibility": m.compatibility,
            "requires": m.requires,
            "triggers": m.triggers,
            "links": m.links,
            "env_satisfied": _env_status(env_names),
            "binaries_satisfied": _binary_status(bins),
        })
    return {
        "kind": "mcp",
        "repo": str(AGENT_MCP_REPO),
        "count": len(items),
        "items": items,
    }


@router.get("/{name}")
def get_mcp(name: str) -> dict:
    _require_companion()
    p = AGENT_MCP_REPO / "registry" / name / "manifest.yaml"
    if not p.exists():
        raise HTTPException(status_code=404, detail=f"mcp not found: {name}")
    m = load_manifest(p, expected_kind="mcp")
    env_names = m.requires.get("env", [])
    bins = m.requires.get("binaries", [])
    return {
        "name": m.name,
        "version": m.version,
        "description": m.description,
        "domain": m.domain,
        "priority": m.priority,
        "mcp_command": m.mcp_command,
        "compatibility": m.compatibility,
        "requires": m.requires,
        "triggers": m.triggers,
        "links": m.links,
        "raw_manifest": m.raw,
        "env_satisfied": _env_status(env_names),
        "binaries_satisfied": _binary_status(bins),
    }
