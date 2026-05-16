"""Infer the most likely domain for a skill, given its frontmatter name + description.

Mirror of agent/docs/domain-taxonomy.md. When the taxonomy spec changes, edit
KEYWORDS + DOMAIN_PRIORITY below to match, then run tests/test_domain_inference.py.

Public API:
    infer(name: str, description: str) -> InferenceResult
    InferenceResult(.domain, .scores, .evidence)

CLI: python -m agent.lib.domain_inference <name> <description>
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import Optional


KEYWORDS: dict[str, list[str]] = {
    "meta": [
        "agent", "subagent", "hook", "plugin", "mcp server", "prompt template",
        "agents.md", "claude.md", ".opencode/", "~/.config/opencode/", "opencode.json",
        "agent directory structure", "agent guardrails", "team-wide agent distribution",
        "agent self-improvement", "ai engineer",
    ],
    "closeout": [
        "review", "code review", "commit", "pull request", " pr ", "merge", "release",
        "ship", "lint", "audit", "codex review", "git rebase", "cherry-pick",
        "changelog", "semver", "pre-commit", "pre-push", "pre-merge",
        "before ship", "before release", "二次审查", "提交前审查",
    ],
    "desktop": [
        "tauri", "electron", "webview", "webview2", "wkwebview", "webkit",
        "native macos", "windows native", "launcher app", "system tray app",
        "global hotkey", "window manager", "raycast", "spotlight", "native feel",
        "cold start", "instant launch", "liquid glass", "vibrancy", "mica material",
        "cross-platform desktop",
    ],
    "founder": [
        "mvp", " icp ", "pressure-test", "pressure test", "validate problem",
        "market fit", "founder-market fit", "pmf", "first 10 customers", "pivot",
        "launch plan", "landing page test", "cold outreach", "pre-seed",
        "idea stage", "pre-revenue", "2-week launch", "startup",
    ],
    "ip": [
        "专利", "软著", "软件著作权", "技术交底书", "国知局", "知识产权",
        "patent", "patent disclosure", "copyright", "software copyright",
        "prior art search", "prior-art", "claim drafting", "申请表",
    ],
    "tooling": [
        "ppt", "slide deck", "slide decks", "presentation", "magazine", "swiss style",
        "swiss layout", "cover", "social cover", "image prompt", "image prompts",
        "image generation", "screenshot", "cover art", "editorial layout",
        "editorial magazine", "docx", "pdf", "markdown", "xlsx", "pptx", " html ",
        "git workflow", "i18n", "markdown lint", "font management",
    ],
}

DOMAIN_PRIORITY = ["ip", "desktop", "founder", "meta", "closeout", "tooling"]


@dataclass
class InferenceResult:
    domain: str
    scores: dict[str, int]
    evidence: dict[str, list[str]] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"domain": self.domain, "scores": self.scores, "evidence": self.evidence}


def infer(name: str, description: str) -> InferenceResult:
    haystack = f" {name.lower()} {description.lower()} "

    scores: dict[str, int] = {}
    evidence: dict[str, list[str]] = {}
    for domain, kws in KEYWORDS.items():
        hits = [kw for kw in kws if kw in haystack]
        if hits:
            scores[domain] = len(hits)
            evidence[domain] = hits

    if not scores:
        return InferenceResult(domain="uncategorized", scores={}, evidence={})

    top = max(scores.values())
    contenders = [d for d, s in scores.items() if s == top]

    if len(contenders) == 1:
        winner = contenders[0]
    else:
        winner = next(d for d in DOMAIN_PRIORITY if d in contenders)

    return InferenceResult(domain=winner, scores=scores, evidence=evidence)


def _main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: python -m agent.lib.domain_inference <name> <description>", file=sys.stderr)
        return 2
    name = argv[0]
    description = " ".join(argv[1:])
    result = infer(name, description)
    import json
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
