"""MCPs API: /api/mcps/* — read-only view over Agent_mcp/registry/."""
from __future__ import annotations

import importlib.util
import os
import shutil
import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException

AGENT_MCP_REPO = Path("/Users/lute/project/Agent/Agent_mcp")


def _load_manifest_module():
    mod_name = "agent_mcp_lib_manifest"
    if mod_name in sys.modules:
        return sys.modules[mod_name]
    spec = importlib.util.spec_from_file_location(
        mod_name, AGENT_MCP_REPO / "agent" / "lib" / "manifest.py"
    )
    m = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = m
    spec.loader.exec_module(m)
    return m


_manifest = _load_manifest_module()
iter_registry = _manifest.iter_registry
load_manifest = _manifest.load_manifest


router = APIRouter(prefix="/api/mcps", tags=["mcps"])


@router.get("/health")
def mcps_health() -> dict:
    repo_ok = AGENT_MCP_REPO.exists()
    registry_ok = (AGENT_MCP_REPO / "registry").exists()
    return {
        "ok": repo_ok and registry_ok,
        "repo": str(AGENT_MCP_REPO),
        "registered_count": len(list((AGENT_MCP_REPO / "registry").glob("*/manifest.yaml")))
            if registry_ok else 0,
    }


def _env_status(env_names) -> dict:
    return {name: bool(os.environ.get(name)) for name in env_names}


def _binary_status(binaries) -> dict:
    return {b: bool(shutil.which(b)) for b in binaries}


@router.get("")
def list_mcps() -> dict:
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
