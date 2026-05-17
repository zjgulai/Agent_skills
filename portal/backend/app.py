"""FastAPI app: serves skills-data.json + install/uninstall endpoints.

Routes:
  GET    /api/health
  GET    /api/skills                       -> full skills-data.json
  GET    /api/skills/{name}/markdown       -> raw SKILL.md text
  POST   /api/install/github               {url, subdir?}
  POST   /api/install/github/monorepo      {url, subdirs?: [str]}  one clone, many installs
  POST   /api/install/upload               multipart file
  DELETE /api/skills/{name}
  POST   /api/refresh                       -> rerun build_index
"""
from __future__ import annotations

import json
import pathlib
from typing import Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from build_index import DATA_FILE, SKILLS_ROOT, build, parse_frontmatter
from installer import install_from_github, install_from_upload, install_monorepo_from_github, uninstall
from hooks_api import router as hooks_router
from mcps_api import router as mcps_router

app = FastAPI(
    title="Skills Portal API",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.include_router(hooks_router)
app.include_router(mcps_router)


def _ensure_data() -> dict:
    if not DATA_FILE.exists():
        return build()
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def _refresh() -> dict:
    return build()


@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "skills_root": str(SKILLS_ROOT), "skills_root_exists": SKILLS_ROOT.exists()}


@app.get("/api/skills")
def list_skills() -> dict:
    return _ensure_data()


@app.get("/api/skills/{name}/markdown", response_class=PlainTextResponse)
def get_skill_markdown(name: str) -> str:
    skill_md = SKILLS_ROOT / name / "SKILL.md"
    if not skill_md.exists():
        raise HTTPException(status_code=404, detail=f"skill not found: {name}")
    return skill_md.read_text(encoding="utf-8")


@app.get("/api/skills/{name}")
def get_skill_info(name: str) -> dict:
    skill_md = SKILLS_ROOT / name / "SKILL.md"
    if not skill_md.exists():
        raise HTTPException(status_code=404, detail=f"skill not found: {name}")
    fm = parse_frontmatter(skill_md)
    if not fm:
        raise HTTPException(status_code=500, detail=f"frontmatter parse failed for: {name}")
    return {"name": name, "frontmatter": fm, "skill_md_path": str(skill_md)}


class GithubInstallRequest(BaseModel):
    url: str
    subdir: Optional[str] = None


class GithubMonorepoInstallRequest(BaseModel):
    url: str
    subdirs: Optional[list[str]] = None


@app.post("/api/install/github")
def post_install_github(req: GithubInstallRequest) -> dict:
    res = install_from_github(req.url, req.subdir)
    if res.ok:
        _refresh()
    return {
        "ok": res.ok,
        "message": res.message,
        "skill_name": res.skill_name,
        "skill_dir": res.skill_dir,
        "warnings": res.warnings,
    }


@app.post("/api/install/github/monorepo")
def post_install_github_monorepo(req: GithubMonorepoInstallRequest) -> dict:
    res = install_monorepo_from_github(req.url, req.subdirs)
    if res.get("succeeded", 0) > 0:
        _refresh()
    return res


@app.post("/api/install/upload")
async def post_install_upload(file: UploadFile = File(...)) -> dict:
    content = await file.read()
    res = install_from_upload(file.filename or "upload.md", content)
    if res.ok:
        _refresh()
    return {
        "ok": res.ok,
        "message": res.message,
        "skill_name": res.skill_name,
        "skill_dir": res.skill_dir,
        "warnings": res.warnings,
    }


@app.delete("/api/skills/{name}")
def delete_skill(name: str) -> dict:
    res = uninstall(name)
    if res.ok:
        _refresh()
    return {"ok": res.ok, "message": res.message, "skill_name": res.skill_name}


@app.post("/api/refresh")
def refresh_data() -> dict:
    payload = _refresh()
    return {
        "ok": True,
        "skill_count": payload["skill_count"],
        "generated_at": payload["generated_at"],
    }
