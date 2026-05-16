"""Tests for agent/lib/domain_inference.py.

Regression suite: 7 cases pulled from agent/docs/domain-taxonomy.md.
Accuracy threshold: ≥ 6/7 (planned 5/6 in main plan; we have 7 cases now).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agent.lib.domain_inference import infer  # noqa: E402


CASES = [
    ("agent-dev-kit-architecture-designer",
     "CLAUDE.md, skills, hooks, subagents, plugins, agent directory structure, "
     "agent guardrails, team-wide agent distribution",
     "meta"),

    ("codex-review",
     "codex review, autoreview, 二次审查, 提交前审查, ship/commit/PR 前的最后检查",
     "closeout"),

    ("native-feel-cross-platform-desktop",
     "cross-platform desktop, Electron alternative, Tauri vs native, WebView wrapper, "
     "near-native performance, Raycast architecture, WebKit/WebView2 quirks, WKWebView, "
     "system tray app, global hotkey app, launcher app",
     "desktop"),

    ("startup-pressure-test",
     "pressure-test startup idea, validate problem, ICP, first 10 customers, MVP, "
     "2-week launch plan, founder-market fit, strong/weak/pivot verdict",
     "founder"),

    ("patent-disclosure-skill",
     "通用中国专利挖掘发现与交底书生成全流程：扫描项目文档挖掘专利点、讨论融合、"
     "基于脱敏模版生成技术交底书、联网查新、生成后自检含逻辑闭环与公式参数一致性",
     "ip"),

    ("software-copyright-materials",
     "Generate guided Chinese software copyright application materials. "
     "Use this skill when the user asks for 软件著作权, 软著申请资料, 软著代码材料",
     "ip"),

    ("guizang-ppt-skill",
     "AI-agent Skill for generating polished HTML slide decks: editorial magazine and "
     "Swiss layouts, image prompts, social covers, and a WebGL/low-power presentation runtime",
     "tooling"),
]


@pytest.mark.parametrize("name,desc,expected", CASES)
def test_inference_per_case(name, desc, expected):
    result = infer(name, desc)
    assert result.domain == expected, (
        f"\n  name: {name}\n"
        f"  expected: {expected}\n"
        f"  got: {result.domain}\n"
        f"  scores: {result.scores}\n"
        f"  evidence: {result.evidence}"
    )


def test_overall_accuracy_at_least_6_of_7():
    correct = 0
    for name, desc, expected in CASES:
        if infer(name, desc).domain == expected:
            correct += 1
    assert correct >= 6, f"only {correct}/7 correct (threshold: 6)"


def test_uncategorized_when_no_keywords():
    result = infer("random-skill", "this skill has no domain-related keywords whatsoever")
    assert result.domain == "uncategorized"
    assert result.scores == {}
