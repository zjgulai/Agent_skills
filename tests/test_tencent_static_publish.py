"""Contracts for Tencent Light Server static publishing."""
from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup


REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS = REPO_ROOT / "docs"
DEPLOY_SCRIPT = REPO_ROOT / "bin" / "deploy-tencent-static"
DEPLOY_DOC = DOCS / "tencent-light-server-deploy.md"

BLOCKED_ASSET_HOSTS = {
    "cdn.tailwindcss.com",
    "cdn.jsdelivr.net",
    "cdnjs.cloudflare.com",
    "unpkg.com",
}


def _asset_urls(path: Path) -> list[str]:
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    urls: list[str] = []
    for tag_name, attr in [("script", "src"), ("link", "href")]:
        for tag in soup.find_all(tag_name):
            value = tag.get(attr)
            if value:
                urls.append(value)
    return urls


def test_public_docs_do_not_depend_on_external_cdn_assets():
    offenders: list[str] = []
    for path in sorted(DOCS.rglob("*.html")):
        for url in _asset_urls(path):
            host = urlparse(url).netloc
            if host in BLOCKED_ASSET_HOSTS:
                offenders.append(f"{path.relative_to(REPO_ROOT)} -> {url}")

    assert offenders == []


def test_tencent_static_deploy_script_has_safe_dry_run_contract():
    source = DEPLOY_SCRIPT.read_text(encoding="utf-8")

    assert os.access(DEPLOY_SCRIPT, os.X_OK)
    assert "bin/deploy-docs" in source
    assert "--target" in source
    assert "--dry-run" in source
    assert "rsync" in source
    assert "--delete" in source
    assert "--exclude=_src/" in source
    assert "--exclude=superpowers/" in source
    assert "--exclude=**/__pycache__/" in source
    assert "--exclude=*.pyc" in source
    assert "docs/" in source
    assert "portal/" not in source


def test_tencent_deploy_doc_points_to_script_and_keeps_portal_private():
    text = DEPLOY_DOC.read_text(encoding="utf-8")

    assert "bin/deploy-tencent-static" in text
    assert "5173" in text and "5174" in text
    assert "127.0.0.1" in text
    assert "docs/" in text
