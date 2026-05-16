"""Tests for agent/lib/portal_client.py.

These tests EXERCISE the live portal:
- Stop any running portal
- Use ensure_running() to start it (verifies the spawn path)
- Verify health, list, status, stop

Skipped when the portal venv or start script is missing (e.g., CI without setup).
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agent.lib import portal_client  # noqa: E402


@pytest.fixture(scope="module", autouse=True)
def ensure_clean_state():
    portal_client.stop()
    yield
    portal_client.stop()


@pytest.mark.skipif(not portal_client.PORTAL_VENV_PYTHON.exists(),
                    reason="portal venv missing")
def test_status_when_down():
    info = portal_client.status()
    assert info["api_up"] is False
    assert info["ports"]["5174_api"] is False


@pytest.mark.skipif(not portal_client.PORTAL_START_SCRIPT.exists(),
                    reason="portal start script missing")
def test_ensure_running_brings_api_up():
    assert portal_client.ensure_running(timeout=20) is True
    h = portal_client.health()
    assert h["ok"] is True
    assert "skills_root" in h


def test_list_skills_returns_payload():
    portal_client.ensure_running(timeout=20)
    data = portal_client.list_skills()
    assert "skill_count" in data
    assert "domains" in data
    assert "skills" in data
    assert isinstance(data["skills"], list)
    assert data["skill_count"] == len(data["skills"])


def test_status_when_up_reports_skill_count():
    portal_client.ensure_running(timeout=20)
    info = portal_client.status()
    assert info["api_up"] is True
    assert info["skill_count"] is not None
    assert info["skill_count"] >= 0


def test_stop_clears_ports():
    portal_client.ensure_running(timeout=20)
    assert portal_client.status()["api_up"] is True
    assert portal_client.stop() is True
    time.sleep(1)
    info = portal_client.status()
    assert info["api_up"] is False
