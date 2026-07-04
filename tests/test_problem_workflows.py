"""Contract checks for the problem-solving workflow taxonomy."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS_JSON = REPO_ROOT / "docs" / "_src" / "problem-workflows.json"
SKILLS_JSON = REPO_ROOT / "docs" / "data" / "skills.json"
BUILD_PY = REPO_ROOT / "docs" / "_src" / "build.py"


EXPECTED_STAGE_IDS = [
    "00-agent-system",
    "01-idea-discovery",
    "02-market-validation",
    "03-product-definition",
    "04-design-prototype",
    "05-build-architecture",
    "06-quality-security",
    "07-launch-deploy",
    "08-growth-marketing",
    "09-sales-customer",
    "10-data-feedback",
    "11-ops-iteration",
    "12-ip-compliance",
    "13-retro-knowledge",
]

EXPECTED_ALCHAINCYF_NODE_IDS = {
    "source.alchaincyf-intake",
    "sensemaking.research-intake",
    "strategy.persona-judgment",
    "content.topic-to-platform",
    "design.html-native-production",
    "quality.anti-ai-slop-review",
    "distribution.article-bridge",
    "agentops.skill-generation-optimization",
}


def _load_build_module():
    spec = importlib.util.spec_from_file_location("docs_build", BUILD_PY)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_problem_workflow_taxonomy_contract():
    payload = json.loads(WORKFLOWS_JSON.read_text(encoding="utf-8"))

    assert payload["version"] == "2026-06-16"
    stages = payload["stages"]
    assert [stage["id"] for stage in stages] == EXPECTED_STAGE_IDS

    node_ids = [node["id"] for stage in stages for node in stage["nodes"]]
    assert len(node_ids) == len(set(node_ids))
    assert len(node_ids) >= 48
    assert EXPECTED_ALCHAINCYF_NODE_IDS <= set(node_ids)

    for stage in stages:
        assert stage["label_zh"]
        assert stage["label_en"]
        assert stage["automation_principle"]
        assert len(stage["nodes"]) >= 2
        for node in stage["nodes"]:
            assert node["problem_zh"]
            assert node["problem_en"]
            assert node["task_intents"]
            assert node["inputs"]
            assert node["outputs"]
            assert node["acceptance"]
            assert node["primary_skills"] or node["supporting_skills"]


def test_problem_workflow_skill_references_exist():
    payload = json.loads(WORKFLOWS_JSON.read_text(encoding="utf-8"))
    installed = {skill["name"] for skill in json.loads(SKILLS_JSON.read_text(encoding="utf-8"))}
    referenced = {
        skill
        for stage in payload["stages"]
        for node in stage["nodes"]
        for skill in node.get("primary_skills", []) + node.get("supporting_skills", [])
    }

    assert "startup-pressure-test" in referenced
    assert "shipping-and-launch" in referenced
    assert "post-mortem" in referenced
    assert referenced <= installed


def test_problem_workflows_annotate_skills_and_render_handbook():
    skills = json.loads(SKILLS_JSON.read_text(encoding="utf-8"))
    by_name = {skill["name"]: skill for skill in skills}

    assert "market-icp-pressure-test" in by_name["startup-pressure-test"]["problem_nodes"]
    assert "launch-release-gates" in by_name["shipping-and-launch"]["problem_nodes"]
    assert "retro-incident-learning" in by_name["post-mortem"]["problem_nodes"]
    assert "idea-trend-research" in by_name["last30days"]["problem_nodes"]
    assert "agent-session-continuity" in by_name["planning-with-files"]["problem_nodes"]
    assert "agent-workflow-governance" in by_name["agnix"]["problem_nodes"]
    assert "growth-seo-content" in by_name["md2wechat"]["problem_nodes"]
    assert "agentops.skill-generation-optimization" in by_name["huashu-nuwa"]["problem_nodes"]
    assert "source.alchaincyf-intake" in by_name["huashu-info-search"]["problem_nodes"]
    assert "sensemaking.research-intake" in by_name["huashu-weread-advisor"]["problem_nodes"]
    assert "strategy.persona-judgment" in by_name["munger-perspective"]["problem_nodes"]
    assert "content.topic-to-platform" in by_name["x-mastery-mentor"]["problem_nodes"]
    assert "design.html-native-production" in by_name["huashu-design"]["problem_nodes"]
    assert "quality.anti-ai-slop-review" in by_name["freud-skill"]["problem_nodes"]
    assert "distribution.article-bridge" in by_name["dukou"]["problem_nodes"]
    assert "design-visual-system" in by_name["anydesign"]["problem_nodes"]
    assert "agent-workflow-governance" in by_name["using-agent-skills"]["problem_nodes"]
    assert "market-icp-pressure-test" in by_name["idea-refine"]["problem_nodes"]
    assert "product-prd-scope" in by_name["interview-me"]["problem_nodes"]
    assert "product-issue-slicing" in by_name["planning-and-task-breakdown"]["problem_nodes"]
    assert "build-tdd-implementation" in by_name["incremental-implementation"]["problem_nodes"]
    assert "quality-review-testing" in by_name["browser-testing-with-devtools"]["problem_nodes"]
    assert "quality-review-testing" in by_name["code-review-and-quality"]["problem_nodes"]
    assert "launch-release-gates" in by_name["ci-cd-and-automation"]["problem_nodes"]
    assert "launch-git-governance" in by_name["git-workflow-and-versioning"]["problem_nodes"]
    assert "ops-roadmap-refresh" in by_name["deprecation-and-migration"]["problem_nodes"]
    assert "retro-knowledge-base" in by_name["documentation-and-adrs"]["problem_nodes"]

    build = _load_build_module()
    payload = json.loads((REPO_ROOT / "docs" / "data" / "problem-workflows.json").read_text(encoding="utf-8"))
    zh = build.render_problem_workflows(payload, "zh")
    en = build.render_problem_workflows(payload, "en")

    assert 'id="problem-workflows"' in zh
    assert "问题解决工作流" in zh
    assert "AI Automation Problem Workflow" in en
    assert "market-icp-pressure-test" in zh


def test_generated_handbook_uses_existing_graph_asset_paths():
    zh = (REPO_ROOT / "docs" / "zh" / "handbook.html").read_text(encoding="utf-8")

    assert "../assets/skills-graph.png" in zh
    assert "../assets/screenshots/skills-graph.png" not in zh
