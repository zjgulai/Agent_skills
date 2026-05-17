"""
data-collect.py — 从 data-mirror/INDEX.md 解析出 skills 结构化数据

输入:  data-mirror/INDEX.md
输出:
  docs/data/skills.json     — 完整 skill 列表（含 domain, role, triggers, refs）
  docs/data/domains.json    — 6 个 domain 的定义 + 各域 skill 计数
  docs/data/portal-status.json — 总数 + 生成时间戳

模式选择:
  - 不依赖 portal 在跑（CI runner 上 portal 不会启动）
  - 完全基于 data-mirror/ 静态文件，git 是真相源

INDEX.md 的解析约定:
  - h3 标题 `### 域 N · 域名（英文/key 提示）` → 一个 domain
  - h3 后跟一个或多个 markdown 表格 → 该 domain 的 skill 列表
  - 表格第一列必须是 `[skill-name](file:///...)` 形式 → 拿出 skill 名
  - 表格第二列 = 定位/role
  - 表格第三列 = triggers/输出物等
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
MIRROR = REPO_ROOT / "data-mirror"
DATA_OUT = REPO_ROOT / "docs" / "data"

# 6 个域的元信息（与 INDEX.md / skills-graph 配色对齐）
DOMAIN_META = {
    "meta": {
        "key": "meta",
        "label_zh": "AI 工程基础设施",
        "label_en": "Meta-Engineering",
        "color": "#e3f2fd",
        "stroke": "#1976d2",
        "order": 1,
        "desc_zh": "你不是在写业务代码，而是在设计/审计 AI agent 自身的工作环境 —— 仓库结构、agent 记忆、skill 库、hook、subagent、plugin。",
        "desc_en": "You're not writing business code — you're designing/auditing the AI agent's own working environment.",
    },
    "closeout": {
        "key": "closeout",
        "label_zh": "代码质量与交付闭环",
        "label_en": "Code Closeout",
        "color": "#c8e6c9",
        "stroke": "#2e7d32",
        "order": 2,
        "desc_zh": "代码已经写完，进入「提交 / PR / 发布」前的最后一公里。",
        "desc_en": "Code is done; last-mile before commit / PR / release.",
    },
    "desktop": {
        "key": "desktop",
        "label_zh": "桌面应用工程",
        "label_en": "Desktop Native Feel",
        "color": "#fff3e0",
        "stroke": "#e65100",
        "order": 3,
        "desc_zh": "在做跨平台桌面应用，并且用户体感必须像原生。",
        "desc_en": "Cross-platform desktop apps that must feel native.",
    },
    "founder": {
        "key": "founder",
        "label_zh": "创业与产品验证",
        "label_en": "Founder / Product",
        "color": "#f3e5f5",
        "stroke": "#6a1b9a",
        "order": 4,
        "desc_zh": "手上有一个点子，需要在写一行代码之前判断「这事儿值不值得做」。",
        "desc_en": "Validate an idea before writing a single line of code.",
    },
    "ip": {
        "key": "ip",
        "label_zh": "知识产权交付",
        "label_en": "IP Deliverables",
        "color": "#e0f2f1",
        "stroke": "#00695c",
        "order": 5,
        "desc_zh": "项目进入商业化保护阶段，要把代码资产变成可申报的法律文件。",
        "desc_en": "Commercialization stage — turn code assets into legal deliverables.",
    },
    "tooling": {
        "key": "tooling",
        "label_zh": "工具增强 (横切层)",
        "label_en": "Tooling (cross-cutting)",
        "color": "#f5f5f5",
        "stroke": "#616161",
        "order": 6,
        "desc_zh": "不绑定特定项目类型，但任何项目都可能需要的能力。",
        "desc_en": "Not bound to any project type — capabilities any project may need.",
    },
}

# 中文 h3 域标题 → key 的映射
DOMAIN_TITLE_TO_KEY = {
    "AI 工程基础设施": "meta",
    "代码质量与交付闭环": "closeout",
    "桌面应用工程": "desktop",
    "创业与产品验证": "founder",
    "知识产权交付": "ip",
    "工具增强": "tooling",
}


# ── 解析 INDEX.md ────────────────────────────────────────────────────────────

SKILL_LINK_PATTERN = re.compile(
    r"\[(?P<name>[a-z0-9][a-z0-9-]+?)\]\(file:///[^)]+SKILL\.md\)"
)
H3_PATTERN = re.compile(r"^###\s+域\s*\d+\s*·\s*(?P<title>[^（(]+?)(?:\s*[（(].*?[）)])?\s*$")


def parse_index_md(text: str) -> list[dict[str, Any]]:
    """从 INDEX.md 抽出所有 skill。返回 [{name, domain, role, extra}]"""
    skills: list[dict[str, Any]] = []
    current_domain: str | None = None

    for line in text.splitlines():
        # 检测域标题
        m_h3 = H3_PATTERN.match(line.strip())
        if m_h3:
            raw_title = m_h3.group("title").strip()
            # 容错：标题可能是 "AI 工程基础设施（Meta-Engineering）"
            for prefix, key in DOMAIN_TITLE_TO_KEY.items():
                if raw_title.startswith(prefix):
                    current_domain = key
                    break
            continue

        # 检测 skill 表格行
        if current_domain and line.startswith("|") and SKILL_LINK_PATTERN.search(line):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 2:
                continue
            m_skill = SKILL_LINK_PATTERN.search(cells[0])
            if not m_skill:
                continue
            skill_name = m_skill.group("name")
            role = cells[1] if len(cells) > 1 else ""
            extra = cells[2] if len(cells) > 2 else ""

            # 跳过重复（同一 skill 在 INDEX 多次出现的话取第一次）
            if any(s["name"] == skill_name for s in skills):
                continue

            skills.append({
                "name": skill_name,
                "domain": current_domain,
                "role": role,
                "extra": extra,
                "skill_url": f"https://github.com/zjgulai/Agent_skills/blob/main/registry/{skill_name}/manifest.yaml",
                "local_path": f"~/.config/opencode/skills/{skill_name}/SKILL.md",
            })

    return skills


# ── 构造输出 JSON ────────────────────────────────────────────────────────────

def build_domains_summary(skills: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """按 domain 分组，返回 [{key, label_zh, label_en, ..., count, skills: [name...]}]"""
    summary = []
    for key, meta in sorted(DOMAIN_META.items(), key=lambda kv: kv[1]["order"]):
        skill_names = [s["name"] for s in skills if s["domain"] == key]
        summary.append({
            **meta,
            "count": len(skill_names),
            "skill_names": skill_names,
        })
    return summary


def build_portal_status(skills: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "skill_count": len(skills),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "data-mirror/INDEX.md",
    }


# ── 主入口 ───────────────────────────────────────────────────────────────────

def main() -> None:
    index_md_path = MIRROR / "INDEX.md"
    if not index_md_path.exists():
        raise SystemExit(f"❌ 缺真相源: {index_md_path}\n请先在仓库根跑 bin/sync-data")

    text = index_md_path.read_text(encoding="utf-8")
    skills = parse_index_md(text)
    domains = build_domains_summary(skills)
    status = build_portal_status(skills)

    DATA_OUT.mkdir(parents=True, exist_ok=True)

    (DATA_OUT / "skills.json").write_text(
        json.dumps(skills, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (DATA_OUT / "domains.json").write_text(
        json.dumps(domains, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (DATA_OUT / "portal-status.json").write_text(
        json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(f"✅ docs/data/skills.json       — {len(skills)} skills")
    print(f"✅ docs/data/domains.json      — {len(domains)} domains")
    print(f"✅ docs/data/portal-status.json — count={status['skill_count']}, generated_at={status['generated_at']}")
    for d in domains:
        marker = "(empty)" if d["count"] == 0 else ", ".join(d["skill_names"])
        print(f"   · {d['key']:9} {d['count']:>2}  {marker}")


if __name__ == "__main__":
    main()
