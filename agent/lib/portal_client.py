"""HTTP client for the local skills portal (FastAPI on 127.0.0.1:5174).

Public API (mirrors portal/backend/app.py routes):
    health()                          -> dict
    list_skills()                     -> dict (full skills-data.json payload)
    get_skill(name)                   -> dict
    get_markdown(name)                -> str
    install_github(url, subdir=None)  -> dict {ok, message, skill_name, skill_dir, warnings}
    install_upload(md_path)           -> dict (same shape)
    scan_monorepo(url)                -> list[str] (subdir paths containing SKILL.md)
    install_monorepo(url, subdirs=None) -> dict {scanned, installed: [...]}
    uninstall(name)                   -> dict {ok, message, skill_name}
    refresh()                         -> dict {ok, skill_count, generated_at}
    ensure_running(timeout=20)        -> bool   (auto-spawns ./portal/bin/start if not up)
    stop()                            -> bool   (kills 5173+5174)
    status()                          -> dict {api_up, pids, ports, skill_count, generated_at}

Constants:
    PORTAL_BASE = "http://127.0.0.1:5174"

CLI: python -m agent.lib.portal_client <command> [args...]
  Commands: health, list, refresh, ensure, stop, status, get <name>,
            install <url> [<subdir>], scan <url>,
            install-monorepo <url> [<subdir>...], uninstall <name>

This module uses httpx for HTTP. All errors raise PortalError with a clear message.
"""
from __future__ import annotations

import json
import os
import pathlib
import socket
import subprocess
import sys
import time
from typing import Optional

import httpx

PORTAL_BASE = "http://127.0.0.1:5174"

_THIS = pathlib.Path(__file__).resolve()
PROJECT_ROOT = _THIS.parents[2]
PORTAL_DIR = PROJECT_ROOT / "portal"
PORTAL_VENV_PYTHON = PORTAL_DIR / "backend" / ".venv" / "bin" / "python"
PORTAL_START_SCRIPT = PORTAL_DIR / "bin" / "start"

# Connect timeout short, read timeout longer (git clone during install can take 60s+).
_TIMEOUT = httpx.Timeout(connect=2.0, read=180.0, write=30.0, pool=5.0)


class PortalError(RuntimeError):
    """Raised when the portal API returns an error or is unreachable."""


def _client() -> httpx.Client:
    return httpx.Client(base_url=PORTAL_BASE, timeout=_TIMEOUT, trust_env=False)


def health() -> dict:
    with _client() as c:
        r = c.get("/api/health")
        r.raise_for_status()
        return r.json()


def list_skills() -> dict:
    with _client() as c:
        r = c.get("/api/skills")
        r.raise_for_status()
        return r.json()


def get_skill(name: str) -> dict:
    with _client() as c:
        r = c.get(f"/api/skills/{name}")
        if r.status_code == 404:
            raise PortalError(f"skill not found: {name}")
        r.raise_for_status()
        return r.json()


def get_markdown(name: str) -> str:
    with _client() as c:
        r = c.get(f"/api/skills/{name}/markdown")
        if r.status_code == 404:
            raise PortalError(f"skill not found: {name}")
        r.raise_for_status()
        return r.text


def install_github(url: str, subdir: Optional[str] = None) -> dict:
    payload = {"url": url}
    if subdir:
        payload["subdir"] = subdir
    with _client() as c:
        r = c.post("/api/install/github", json=payload)
        if r.status_code == 400:
            data = r.json()
            raise PortalError(f"install failed: {data.get('detail', r.text)}")
        r.raise_for_status()
        return r.json()


def install_upload(md_path: str | pathlib.Path) -> dict:
    p = pathlib.Path(md_path)
    if not p.is_file():
        raise PortalError(f"not a file: {p}")
    with _client() as c, p.open("rb") as f:
        files = {"file": (p.name, f, "text/markdown")}
        r = c.post("/api/install/upload", files=files)
        r.raise_for_status()
        data = r.json()
        if not data.get("ok"):
            raise PortalError(f"upload install failed: {data.get('message', 'unknown')}")
        return data


def uninstall(name: str) -> dict:
    with _client() as c:
        r = c.delete(f"/api/skills/{name}")
        r.raise_for_status()
        data = r.json()
        if not data.get("ok"):
            raise PortalError(f"uninstall failed: {data.get('message', 'unknown')}")
        return data


def refresh() -> dict:
    with _client() as c:
        r = c.post("/api/refresh")
        r.raise_for_status()
        return r.json()


SCAN_SKIP_DIRS = {".git", ".github", ".idea", ".vscode", ".cache", ".pytest_cache",
                  "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}


def scan_monorepo(url: str) -> list[str]:
    """List all SKILL.md subpaths in a GitHub repo (one HTTP call to git/trees API).

    Returns list of subdirs (parent of each SKILL.md), e.g.
    ['skills/brainstorming', 'skills/test-driven-development', ...].
    Excludes the repo root itself (which is handled by plain install).
    """
    if not url.startswith(("https://github.com/", "git@github.com:", "http://github.com/")):
        raise PortalError(f"only GitHub URLs supported, got: {url}")
    if url.startswith("git@github.com:"):
        owner_repo = url[len("git@github.com:"):]
    else:
        owner_repo = url.split("github.com/", 1)[1]
    owner_repo = owner_repo.rstrip("/").removesuffix(".git")

    api = f"https://api.github.com/repos/{owner_repo}/git/trees/main?recursive=1"
    with httpx.Client(timeout=httpx.Timeout(30.0)) as c:
        r = c.get(api)
        if r.status_code == 404:
            api = api.replace("/main?", "/master?")
            r = c.get(api)
        r.raise_for_status()
        data = r.json()

    if data.get("truncated"):
        raise PortalError(
            f"repo tree exceeds GitHub API limits (truncated). "
            f"Run install with explicit --subdir for each skill."
        )

    subdirs = []
    for entry in data.get("tree", []):
        if entry.get("type") == "blob" and entry["path"].endswith("/SKILL.md"):
            path = entry["path"]
            parts = path.split("/")[:-1]
            if any(p in SCAN_SKIP_DIRS for p in parts):
                continue
            subdirs.append(path[: -len("/SKILL.md")])
    return sorted(subdirs)


def install_monorepo(url: str, subdirs: Optional[list[str]] = None) -> dict:
    """Install multiple skills from a monorepo (one clone, many installs).

    Calls portal API /api/install/github/monorepo which clones once and
    iterates over subdirs server-side — drastically faster than N round-trips.

    If subdirs is None: server auto-discovers every dir containing a SKILL.md.

    Returns dict {ok, message, total, succeeded, failed, results: [...]}.
    Falls back to per-subdir loop if portal returns 404 (older portal version).
    """
    payload: dict = {"url": url}
    if subdirs is not None:
        payload["subdirs"] = subdirs
    with _client() as c:
        r = c.post(
            "/api/install/github/monorepo",
            json=payload,
            timeout=httpx.Timeout(connect=2.0, read=900.0, write=30.0, pool=5.0),
        )
        if r.status_code == 404:
            return _install_monorepo_fallback(url, subdirs)
        if r.status_code == 400:
            data = r.json()
            raise PortalError(f"monorepo install failed: {data.get('detail', r.text)}")
        r.raise_for_status()
        return r.json()


def _install_monorepo_fallback(url: str, subdirs: Optional[list[str]] = None) -> dict:
    """Legacy per-subdir loop. Used when portal /api/install/github/monorepo is unavailable."""
    if subdirs is None:
        subdirs = scan_monorepo(url)
    results = []
    succeeded = 0
    failed = 0
    for sub in subdirs:
        try:
            res = install_github(url, sub)
            results.append({
                "subdir": sub,
                "ok": True,
                "skill_name": res.get("skill_name"),
            })
            succeeded += 1
        except (PortalError, httpx.HTTPError) as e:
            results.append({"subdir": sub, "ok": False, "error": str(e)[:200]})
            failed += 1
    return {
        "ok": failed == 0,
        "message": f"monorepo install (fallback): {succeeded} ok, {failed} failed",
        "total": len(subdirs),
        "succeeded": succeeded,
        "failed": failed,
        "results": results,
    }


def _port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.2)
        return s.connect_ex(("127.0.0.1", port)) == 0


def _pids_on_ports(ports: list[int]) -> list[int]:
    try:
        out = subprocess.run(
            ["lsof", "-ti:" + ",".join(str(p) for p in ports)],
            capture_output=True, text=True, timeout=5,
        ).stdout.strip()
        return [int(p) for p in out.split() if p.isdigit()]
    except Exception:
        return []


def ensure_running(timeout: float = 20.0) -> bool:
    """Return True if portal API is reachable. Spawn bin/start if needed.

    Raises PortalError if startup fails (venv missing, npm missing, ports stuck).
    """
    try:
        if health().get("ok"):
            return True
    except (httpx.RequestError, PortalError):
        pass

    if not PORTAL_VENV_PYTHON.exists():
        raise PortalError(
            f"portal venv missing: {PORTAL_VENV_PYTHON}\n"
            f"  Run portal install steps first (see {PORTAL_DIR / 'README.md'})"
        )
    if not PORTAL_START_SCRIPT.exists():
        raise PortalError(f"start script missing: {PORTAL_START_SCRIPT}")
    if _port_in_use(5174) or _port_in_use(5173):
        raise PortalError(
            "ports 5173/5174 occupied by another process. "
            "Run /portal-stop or `lsof -ti:5173,5174 | xargs kill -9` first."
        )

    log_path = pathlib.Path("/tmp/portal-uvicorn.log")
    log = log_path.open("ab")
    proc = subprocess.Popen(
        [str(PORTAL_START_SCRIPT)],
        stdout=log,
        stderr=subprocess.STDOUT,
        start_new_session=True,
        cwd=str(PROJECT_ROOT),
    )

    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(0.5)
        try:
            if health().get("ok"):
                return True
        except (httpx.RequestError, PortalError):
            continue
        if proc.poll() is not None:
            log.close()
            tail = log_path.read_text(errors="replace").splitlines()[-20:]
            raise PortalError(
                "bin/start exited before /api/health came up:\n  " + "\n  ".join(tail)
            )

    log.close()
    raise PortalError(f"portal did not become healthy within {timeout}s; see {log_path}")


def stop() -> bool:
    pids = _pids_on_ports([5173, 5174])
    if not pids:
        return False
    for pid in pids:
        try:
            os.kill(pid, 9)
        except ProcessLookupError:
            pass
    time.sleep(1)
    return True


def status() -> dict:
    info = {
        "api_up": False,
        "pids": _pids_on_ports([5173, 5174]),
        "ports": {
            "5173_vite": _port_in_use(5173),
            "5174_api": _port_in_use(5174),
        },
        "skill_count": None,
        "generated_at": None,
    }
    try:
        h = health()
        info["api_up"] = bool(h.get("ok"))
        if info["api_up"]:
            data = list_skills()
            info["skill_count"] = data.get("skill_count")
            info["generated_at"] = data.get("generated_at")
    except Exception:
        pass
    return info

def _print(obj) -> None:
    if isinstance(obj, (dict, list)):
        print(json.dumps(obj, ensure_ascii=False, indent=2))
    else:
        print(obj)


def _main(argv: list[str]) -> int:
    if not argv:
        print(
            "usage: python -m agent.lib.portal_client "
            "<health|list|refresh|ensure|stop|status|get NAME|install URL [SUBDIR]|"
            "scan URL|install-monorepo URL [SUBDIR...]|uninstall NAME>",
            file=sys.stderr,
        )
        return 2

    cmd = argv[0]
    try:
        if cmd == "health":
            _print(health())
        elif cmd == "list":
            data = list_skills()
            _print({"skill_count": data["skill_count"], "names": [s["name"] for s in data["skills"]]})
        elif cmd == "refresh":
            _print(refresh())
        elif cmd == "ensure":
            ok = ensure_running()
            _print({"ensured": ok})
        elif cmd == "stop":
            ok = stop()
            _print({"stopped": ok})
        elif cmd == "status":
            _print(status())
        elif cmd == "get":
            if len(argv) < 2:
                print("usage: get NAME", file=sys.stderr); return 2
            _print(get_skill(argv[1]))
        elif cmd == "install":
            if len(argv) < 2:
                print("usage: install URL [SUBDIR]", file=sys.stderr); return 2
            url = argv[1]
            subdir = argv[2] if len(argv) >= 3 else None
            _print(install_github(url, subdir))
        elif cmd == "scan":
            if len(argv) < 2:
                print("usage: scan URL", file=sys.stderr); return 2
            _print({"subdirs": scan_monorepo(argv[1])})
        elif cmd == "install-monorepo":
            if len(argv) < 2:
                print("usage: install-monorepo URL [SUBDIR...]", file=sys.stderr); return 2
            url = argv[1]
            subs = argv[2:] if len(argv) > 2 else None
            _print(install_monorepo(url, subs))
        elif cmd == "uninstall":
            if len(argv) < 2:
                print("usage: uninstall NAME", file=sys.stderr); return 2
            _print(uninstall(argv[1]))
        else:
            print(f"unknown command: {cmd}", file=sys.stderr)
            return 2
    except PortalError as e:
        print(f"PortalError: {e}", file=sys.stderr)
        return 1
    except httpx.HTTPStatusError as e:
        print(f"HTTP {e.response.status_code}: {e.response.text[:300]}", file=sys.stderr)
        return 1
    except httpx.RequestError as e:
        print(f"network error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
