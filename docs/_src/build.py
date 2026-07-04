"""build.py — 构建 docs/zh/ 与 docs/en/ 双语静态站。

策略:
  - 不写 Jinja2 模板。直接以原 docs/*.html 为基底，用 BeautifulSoup
    做 DOM 替换:
    1. 删除原页面顶部 <script>window.I18N_ZH...</script> 字典（不再需要运行时切换）
    2. 删除原页面 <script src="./assets/i18n.js"> （运行时切换器）
    3. 英文版：保留 data-i18n 节点的原始 innerText（HTML 默认是英文）
    4. 中文版：用 docs/_src/i18n/zh.json 字典替换 data-i18n 节点
    5. 动态注入区块（占位 div id 形式）：skill 表格、计数、域分组、case study 演化

  - 占位 div 在原 HTML 里**还不存在**，需要先注入到指定页面的指定 anchor 后；
    本 build.py 第一阶段只跑 i18n 替换，动态区块在第二阶段叠加。

输出:
  docs/index.html       → 顶层重定向（按浏览器语言跳 /zh/ 或 /en/）
  docs/zh/<page>.html   → 中文版
  docs/en/<page>.html   → 英文版
  docs/data/*.json      → 由 data-collect.py 生成（本脚本只读不改）
  docs/assets/...       → 保留原状

CI 用法:
  python docs/_src/data-collect.py    # 先生成 JSON 数据
  python docs/_src/build.py           # 再构建静态站
"""

from __future__ import annotations

import json
import re
import shutil
from html import escape
from pathlib import Path

from bs4 import BeautifulSoup

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS = REPO_ROOT / "docs"
SRC = DOCS / "_src"
ORIGINALS = SRC / "originals"
DATA = DOCS / "data"
I18N = SRC / "i18n"
CASE_STUDIES = SRC / "case-studies.json"
WEEKLY_HOT_SKILLS = SRC / "weekly-hot-skills.json"
PROBLEM_WORKFLOWS_DATA = DATA / "problem-workflows.json"
ALCHAINCYF_MANIFEST = SRC / "alchaincyf-skill-manifest.json"

PAGES_TO_BUILD = [
    "index.html",
    "handbook.html",
    "architecture.html",
    "getting-started.html",
]

PASSTHROUGH_PAGES = [
    "domains.html",
    "commands.html",
    "case-study.html",
]


def load_zh_dict() -> dict[str, dict[str, str]]:
    return json.loads((I18N / "zh.json").read_text(encoding="utf-8"))


def page_key_from_filename(filename: str) -> str:
    return filename.replace(".html", "")


def remove_runtime_i18n(soup: BeautifulSoup) -> None:
    """移除原页面的运行时 i18n 设施（构建期渲染后不再需要）。"""
    for script in soup.find_all("script"):
        text = script.string or ""
        src = script.get("src") or ""
        if "window.I18N_ZH" in text:
            script.decompose()
        elif "i18n.js" in src:
            script.decompose()
    for btn in soup.find_all(id="lang-toggle"):
        btn.decompose()


def apply_zh_translations(soup: BeautifulSoup, page_zh: dict[str, str]) -> int:
    """用 zh.json 字典替换 data-i18n / data-i18n-html / data-i18n-attr 节点。"""
    replaced = 0
    for el in soup.find_all(attrs={"data-i18n": True}):
        key = el["data-i18n"]
        if key in page_zh:
            el.string = page_zh[key]
            replaced += 1
        del el["data-i18n"]
    for el in soup.find_all(attrs={"data-i18n-html": True}):
        key = el["data-i18n-html"]
        if key in page_zh:
            new_soup = BeautifulSoup(page_zh[key], "html.parser")
            el.clear()
            for child in list(new_soup.children):
                el.append(child)
            replaced += 1
        del el["data-i18n-html"]
    for el in soup.find_all(attrs={"data-i18n-attr": True}):
        spec = el["data-i18n-attr"]
        if ":" in spec:
            attr_name, key = spec.split(":", 1)
            if key in page_zh:
                el[attr_name] = page_zh[key]
                replaced += 1
        del el["data-i18n-attr"]
    return replaced


def add_lang_switcher(soup: BeautifulSoup, current_lang: str) -> None:
    """在 nav 里加一个静态语言切换链接（构建期已分流，运行时不再切）。"""
    nav = soup.find("nav")
    if not nav:
        return
    container = nav.find("div", class_=lambda c: c and "md:flex" in c)
    if not container:
        return
    other_lang = "en" if current_lang == "zh" else "zh"
    label = "EN" if other_lang == "en" else "中文"
    link = soup.new_tag(
        "a",
        href=f"../{other_lang}/index.html",
        attrs={"class": "px-3 py-1.5 bg-zinc-900 hover:bg-zinc-800 rounded-md text-sm text-zinc-300 transition-colors border border-zinc-700"},
    )
    link.string = label
    container.append(link)


def fix_lang_attr(soup: BeautifulSoup, lang: str) -> None:
    html_tag = soup.find("html")
    if html_tag:
        html_tag["lang"] = lang


def fix_relative_paths(soup: BeautifulSoup) -> None:
    """Rewrite only shared asset/data paths for docs/<lang>/ output.

    Same-language page links such as ./handbook.html must stay local to
    docs/<lang>/handbook.html. Rewriting them to ../handbook.html makes the
    public site fall back to stale root-level legacy pages.
    """
    for el in soup.find_all(attrs={"href": True}):
        href = el["href"]
        if href.startswith(("./assets/", "./data/")):
            el["href"] = "../" + href[2:]
    for el in soup.find_all(attrs={"src": True}):
        src = el["src"]
        if src.startswith(("./assets/", "./data/")):
            el["src"] = "../" + src[2:]


def replace_stale_screenshot(soup: BeautifulSoup, skill_count: int, lang: str) -> bool:
    """把 hero 区写死的 portal-after-install.png 替换成当前 skills-graph.png。"""
    for img in soup.find_all("img", src=True):
        if "portal-after-install" in img["src"]:
            img["src"] = "../assets/skills-graph.png"
            alt = (
                f"Skills 图谱 · 当前 {skill_count} 个用户级 skill"
                if lang == "zh"
                else f"Skills graph · {skill_count} user-level skills"
            )
            img["alt"] = alt
            return True
    return False


def update_skill_count_in_text(soup: BeautifulSoup, count: int) -> int:
    """把 hero demo block 里写死的 'skill_count = 6 → 7' 等替换成动态 'count-1 → count'。"""
    replaced = 0
    pattern = re.compile(r"skill_count\s*=\s*\d+\s*→\s*\d+")
    for code_el in soup.find_all("code"):
        if not code_el.string:
            continue
        new_string, n = pattern.subn(
            f"skill_count = {count - 1} → {count}", code_el.string
        )
        if n > 0:
            code_el.string = new_string
            replaced += n
    return replaced


def render_case_studies(states: list[dict], lang: str) -> str:
    """根据 case-studies.json 生成 case study HTML 段落（按状态时间序）。"""
    title = "§5. 图谱演化案例" if lang == "zh" else "§5. Graph Case Studies"
    lead = (
        f"{len(states)} 个图谱状态，按时间序展示新装 skill 时图谱怎么变。"
        if lang == "zh"
        else f"{len(states)} graph states walking through how the graph mutates as new skills are added."
    )
    delta_label = "Δ vs 上一个状态：" if lang == "zh" else "Δ vs previous state:"
    triggered_label = "触发命令：" if lang == "zh" else "Triggered by:"

    parts = [f'<section id="case-studies">',
             f'  <h2>{title}</h2>',
             f'  <p>{lead}</p>']

    for s in states:
        title = s.get(f"title_{lang}", s.get("title_en", f"State {s.get('id', '?')}"))
        desc = s.get(f"desc_{lang}", s.get("desc_en", ""))
        bullets = s.get(f"bullets_{lang}", s.get("bullets_en", []))
        png = s.get("png", "")
        cmd = s.get("trigger_cmd")
        delta = s.get(f"delta_{lang}")

        parts.append(f'  <h3 id="state-{s["id"]}">5.{s["id"] + 1} {title}</h3>')
        if cmd:
            parts.append(f'  <p><span>{triggered_label}</span> <code>{cmd}</code></p>')
        parts.append(f'  <p>{desc}</p>')
        if delta:
            parts.append(
                f'  <div class="delta-callout"><strong>{delta_label}</strong> <span>{delta}</span></div>'
            )
        if bullets:
            parts.append('  <ul>')
            for b in bullets:
                parts.append(f'    <li>{b}</li>')
            parts.append('  </ul>')
        if png:
            alt_zh = f"图谱状态 {s['id']}"
            alt_en = f"Skills graph state {s['id']}"
            alt = alt_zh if lang == "zh" else alt_en
            asset_path = (
                f"../assets/{png}"
                if png == "skills-graph.png"
                else f"../assets/screenshots/{png}"
            )
            parts.append(
                f'  <a href="{asset_path}" target="_blank" rel="noopener">'
                f'<img src="{asset_path}" alt="{alt}" class="graph-img"></a>'
            )

    parts.append('</section>')
    return "\n".join(parts)


def replace_case_studies_section(soup: BeautifulSoup, states: list[dict], lang: str) -> bool:
    section = soup.find("section", id="case-studies")
    if not section:
        return False
    new_html = render_case_studies(states, lang)
    new_section = BeautifulSoup(new_html, "lxml").find("section")
    section.replace_with(new_section)
    return True


def load_weekly_hot_skills() -> dict:
    if not WEEKLY_HOT_SKILLS.exists():
        return {}
    return json.loads(WEEKLY_HOT_SKILLS.read_text(encoding="utf-8"))


def publish_weekly_hot_skills(payload: dict) -> None:
    if not payload:
        return
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "weekly-hot-skills.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def load_alchaincyf_manifest() -> dict:
    if not ALCHAINCYF_MANIFEST.exists():
        return {}
    return json.loads(ALCHAINCYF_MANIFEST.read_text(encoding="utf-8"))


def publish_alchaincyf_manifest(payload: dict) -> None:
    if not payload:
        return
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "alchaincyf-skill-manifest.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _pick(d: dict, key: str, lang: str, default: str = "") -> str:
    return str(d.get(f"{key}_{lang}") or d.get(f"{key}_en") or d.get(key) or default)


def render_weekly_hot_skills(payload: dict, lang: str) -> str:
    window = payload.get("window", {})
    groups = payload.get("groups", [])
    radar = payload.get("radar", [])
    title = "本周热门 Skills Radar" if lang == "zh" else "Hot Skills Radar This Week"
    lead = (
        f"{window.get('start', '')} → {window.get('end', '')}：按 GitHub 活跃度、真实 SKILL.md 结构、与现有库互补性筛选。"
        if lang == "zh"
        else f"{window.get('start', '')} → {window.get('end', '')}: filtered by GitHub activity, real SKILL.md structure, and fit with the current library."
    )
    installed_label = "本次已安装" if lang == "zh" else "Installed now"
    source_label = "来源" if lang == "zh" else "Source"
    radar_title = "只观察，不整包导入" if lang == "zh" else "Watchlist, not bulk-installed"
    radar_lead = (
        "聚合目录和大包用于发现趋势；本地仓库只纳入经过筛选的子 skill。"
        if lang == "zh"
        else "Aggregators and large packs are used for discovery; the local library only accepts curated sub-skills."
    )

    parts = [
        '<section id="weekly-hot-skills" class="site-section section-panel">',
        '  <div class="section-head">',
        '    <div>',
        '      <p class="eyebrow">2026-06-14</p>',
        f'      <h2>{escape(title)}</h2>',
        f'      <p>{escape(lead)}</p>',
        '    </div>',
        f'    <a class="text-link" href="../data/weekly-hot-skills.json">{escape("查看 JSON 数据" if lang == "zh" else "View JSON data")} →</a>',
        '  </div>',
        '  <div class="hot-grid">',
    ]

    for group in groups:
        skills = group.get("skills", [])
        skill_tags = "\n".join(
            f'        <span class="tag">{escape(s)}</span>'
            for s in skills
        )
        stars = group.get("stars")
        stars_text = f"{stars:,} stars" if isinstance(stars, int) else ""
        updated = str(group.get("updated_at", ""))[:10]
        parts.extend([
            '    <article class="data-card">',
            '      <div class="card-head">',
            '        <div>',
            f'          <p class="mini-label">{escape(source_label)}</p>',
            f'          <h3><a href="{escape(group.get("url", ""))}" target="_blank" rel="noopener">{escape(group.get("repo", ""))}</a></h3>',
            '        </div>',
            f'        <span>{escape(updated)}</span>',
            '      </div>',
            f'      <p>{escape(_pick(group, "why", lang))}</p>',
            f'      <p class="card-accent">{escape(installed_label)} · {len(skills)} {escape("个" if lang == "zh" else "skills")}</p>',
            '      <div class="tag-row">',
            skill_tags,
            '      </div>',
            f'      <p class="muted-small">{escape(stars_text)}</p>',
            '    </article>',
        ])

    parts.extend([
        '  </div>',
        '  <div class="watchlist-panel">',
        f'    <h3>{escape(radar_title)}</h3>',
        f'    <p>{escape(radar_lead)}</p>',
        '    <div class="watchlist-grid">',
    ])

    for item in radar:
        parts.extend([
            f'      <a class="watchlist-item" href="{escape(item.get("url", ""))}" target="_blank" rel="noopener">',
            f'        <strong>{escape(item.get("repo", ""))}</strong>',
            f'        <span>{escape(str(item.get("stars", "")))} stars</span>',
            f'        <p>{escape(_pick(item, "decision", lang))}</p>',
            '      </a>',
        ])

    parts.extend([
        '  </div>',
        '</div>',
        '</section>',
    ])
    return "\n".join(parts)


def replace_weekly_hot_skills_section(soup: BeautifulSoup, payload: dict, lang: str) -> bool:
    section = soup.find("section", id="weekly-hot-skills")
    if not section or not payload:
        return False
    new_html = render_weekly_hot_skills(payload, lang)
    new_section = BeautifulSoup(new_html, "lxml").find("section")
    section.replace_with(new_section)
    return True


def render_alchaincyf_source_collection(payload: dict, lang: str) -> str:
    summary = payload.get("ingestion_summary", {})
    skills = payload.get("skills", [])
    install_items = [item for item in skills if item.get("action") == "install"]
    distill_items = [item for item in skills if item.get("action") == "distill-only"]
    skip_items = [item for item in skills if item.get("action") == "skip"]
    problem_counts: dict[str, int] = {}
    for item in install_items:
        node = str(item.get("problem_node", ""))
        if node:
            problem_counts[node] = problem_counts.get(node, 0) + 1
    top_nodes = sorted(problem_counts.items(), key=lambda kv: (-kv[1], kv[0]))[:8]

    if lang == "zh":
        title = "Alchaincyf source collection 已入库"
        lead = (
            f"{payload.get('snapshot_date', '')} 快照：不是整包复制，而是按 root / subdir / monorepo / distill-only "
            "四种模式拆解，映射到问题节点后再进入网站。"
        )
        source_label = "来源"
        installed_label = "运行时安装"
        modes_label = "安装模式"
        backlog_label = "蒸馏与跳过"
        node_label = "问题节点覆盖"
        json_label = "查看 manifest JSON"
        cards = [
            (source_label, payload.get("source_owner", "alchaincyf"), f"{payload.get('repo_count', 0)} repos · {payload.get('non_fork_count', 0)} non-forks · {payload.get('fork_count', 0)} forks"),
            (installed_label, str(summary.get("runtime_install_count", len(install_items))), f"{summary.get('direct_root_install_count', 0)} root · {summary.get('subdir_install_count', 0)} subdir · {summary.get('monorepo_install_count', 0)} monorepo"),
            (modes_label, "root / subdir / monorepo / none", "所有 runtime 写入都通过 portal API，distill-only 不安装。"),
            (backlog_label, f"{len(distill_items)} distill-only · {len(skip_items)} skipped", "橙皮书和产品仓库先作为来源材料，不盲目安装。"),
        ]
    else:
        title = "Alchaincyf Source Collection Ingested"
        lead = (
            f"{payload.get('snapshot_date', '')} snapshot: split by root, subdir, monorepo, and distill-only modes, "
            "then mapped into problem nodes before publishing."
        )
        source_label = "Source"
        installed_label = "Runtime installs"
        modes_label = "Install modes"
        backlog_label = "Distill and skip"
        node_label = "Problem-node coverage"
        json_label = "View manifest JSON"
        cards = [
            (source_label, payload.get("source_owner", "alchaincyf"), f"{payload.get('repo_count', 0)} repos · {payload.get('non_fork_count', 0)} non-forks · {payload.get('fork_count', 0)} forks"),
            (installed_label, str(summary.get("runtime_install_count", len(install_items))), f"{summary.get('direct_root_install_count', 0)} root · {summary.get('subdir_install_count', 0)} subdir · {summary.get('monorepo_install_count', 0)} monorepo"),
            (modes_label, "root / subdir / monorepo / none", "Runtime writes go through the portal API; distill-only records are not installed."),
            (backlog_label, f"{len(distill_items)} distill-only · {len(skip_items)} skipped", "Books and product repos stay as source material until distilled."),
        ]

    parts = [
        '<section class="site-section section-panel" id="alchaincyf-source-collection">',
        '  <div class="section-head">',
        '    <div>',
        '      <p class="eyebrow">GitHub source intake</p>',
        f'      <h2>{escape(title)}</h2>',
        f'      <p>{escape(lead)}</p>',
        '    </div>',
        f'    <a class="text-link" href="../data/alchaincyf-skill-manifest.json">{escape(json_label)} →</a>',
        '  </div>',
        '  <div class="hot-grid">',
    ]

    for label, value, text in cards:
        parts.extend([
            '    <article class="data-card">',
            f'      <p class="mini-label">{escape(label)}</p>',
            f'      <h3>{escape(value)}</h3>',
            f'      <p>{escape(text)}</p>',
            '    </article>',
        ])

    chips = "\n".join(
        f'      <span class="tag">{escape(node)} · {count}</span>'
        for node, count in top_nodes
    )
    parts.extend([
        '  </div>',
        '  <div class="watchlist-panel">',
        f'    <h3>{escape(node_label)}</h3>',
        '    <div class="tag-row">',
        chips,
        '    </div>',
        '  </div>',
        '</section>',
    ])
    return "\n".join(parts)


def replace_alchaincyf_source_collection(soup: BeautifulSoup, payload: dict, lang: str) -> bool:
    section = soup.find("section", id="alchaincyf-source-collection")
    if not section or not payload:
        return False
    new_html = render_alchaincyf_source_collection(payload, lang)
    new_section = BeautifulSoup(new_html, "lxml").find("section")
    section.replace_with(new_section)
    return True


def hydrate_homepage_console_stats(
    soup: BeautifulSoup,
    skill_count: int,
    problem_workflows: dict,
    alchaincyf_manifest: dict,
    lang: str,
) -> int:
    node_count = sum(len(stage.get("nodes", [])) for stage in problem_workflows.get("stages", []))
    source_runtime = (
        alchaincyf_manifest.get("ingestion_summary", {}).get("runtime_install_count")
        or len([item for item in alchaincyf_manifest.get("skills", []) if item.get("action") == "install"])
    )
    values = {
        "skills": skill_count,
        "nodes": node_count,
        "source-runtime": source_runtime,
        "publish-state": "Ready" if lang == "en" else "Ready",
    }
    replaced = 0
    for key, value in values.items():
        el = soup.find(attrs={"data-stat": key})
        if el:
            el.string = str(value)
            replaced += 1
    return replaced


def load_problem_workflows() -> dict:
    if not PROBLEM_WORKFLOWS_DATA.exists():
        return {}
    return json.loads(PROBLEM_WORKFLOWS_DATA.read_text(encoding="utf-8"))


def render_problem_workflows(payload: dict, lang: str) -> str:
    stages = payload.get("stages", [])
    title = "问题解决工作流" if lang == "zh" else "AI Automation Problem Workflow"
    lead = (
        "第二分类轴：从用户问题出发，把 skills 编排成从 idea 到上线、增长、运营、复盘的自动化链路。"
        if lang == "zh"
        else "A second classification axis: route user problems into automation chains from idea to launch, growth, operations, and learning."
    )
    data_label = "机器可读数据" if lang == "zh" else "Machine-readable data"
    node_label = "问题节点" if lang == "zh" else "Problem nodes"
    primary_label = "主力 skills" if lang == "zh" else "Primary skills"
    acceptance_label = "验收门槛" if lang == "zh" else "Acceptance gates"

    parts = [
        '<section id="problem-workflows">',
        f'  <h2>{escape(title)}</h2>',
        f'  <p>{escape(lead)}</p>',
        f'  <p><a href="../data/problem-workflows.json" target="_blank" rel="noopener">{escape(data_label)} →</a></p>',
        '  <div class="workflow-grid">',
    ]

    for stage in stages:
        stage_label = stage.get(f"label_{lang}") or stage.get("label_en") or stage.get("id", "")
        principle = stage.get("automation_principle", "")
        nodes = stage.get("nodes", [])
        parts.extend([
            '    <article class="workflow-stage">',
            '      <div class="workflow-stage-head">',
            f'        <span class="workflow-stage-id">{escape(stage.get("id", ""))}</span>',
            f'        <span class="workflow-stage-count">{len(nodes)} {escape(node_label)}</span>',
            '      </div>',
            f'      <h3>{escape(stage_label)}</h3>',
            f'      <p>{escape(principle)}</p>',
            '      <div class="workflow-node-list">',
        ])

        for node in nodes:
            problem = node.get(f"problem_{lang}") or node.get("problem_en") or ""
            primary = node.get("primary_skills", [])
            acceptance = node.get("acceptance", [])
            primary_chips = "".join(
                f'<code>{escape(skill)}</code>' for skill in primary[:4]
            )
            acceptance_text = " · ".join(str(item) for item in acceptance[:2])
            parts.extend([
                '        <div class="workflow-node">',
                f'          <strong>{escape(node.get("id", ""))}</strong>',
                f'          <p>{escape(problem)}</p>',
                f'          <div><span>{escape(primary_label)}:</span> {primary_chips}</div>',
                f'          <small>{escape(acceptance_label)}: {escape(acceptance_text)}</small>',
                '        </div>',
            ])

        parts.extend([
            '      </div>',
            '    </article>',
        ])

    parts.extend([
        '  </div>',
        '</section>',
    ])
    return "\n".join(parts)


def replace_problem_workflows_section(soup: BeautifulSoup, payload: dict, lang: str) -> bool:
    if not payload:
        return False
    new_html = render_problem_workflows(payload, lang)
    new_section = BeautifulSoup(new_html, "lxml").find("section")
    if not new_section:
        return False
    existing = soup.find("section", id="problem-workflows")
    if existing:
        existing.replace_with(new_section)
        return True
    domains = soup.find("section", id="domains")
    if not domains:
        return False
    domains.insert_after(new_section)
    return True


def build_one(page_filename: str, lang: str, zh: dict[str, dict[str, str]],
              weekly_hot: dict,
              problem_workflows: dict,
              alchaincyf_manifest: dict,
              skill_count: int, out_root: Path) -> dict:
    src_path = ORIGINALS / page_filename
    text = src_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(text, "lxml")

    fix_lang_attr(soup, lang)
    remove_runtime_i18n(soup)

    page_key = page_key_from_filename(page_filename)
    replaced = 0
    if lang == "zh":
        replaced = apply_zh_translations(soup, zh.get(page_key, {}))
    else:
        for el in soup.find_all(attrs={"data-i18n": True}):
            del el["data-i18n"]
        for el in soup.find_all(attrs={"data-i18n-html": True}):
            del el["data-i18n-html"]
        for el in soup.find_all(attrs={"data-i18n-attr": True}):
            del el["data-i18n-attr"]

    fix_relative_paths(soup)

    add_lang_switcher(soup, lang)

    sc_replaced = 0
    img_replaced = False
    if page_filename == "index.html":
        sc_replaced = update_skill_count_in_text(soup, skill_count)
        img_replaced = replace_stale_screenshot(soup, skill_count, lang)
        weekly_replaced = replace_weekly_hot_skills_section(soup, weekly_hot, lang)
        alchaincyf_replaced = replace_alchaincyf_source_collection(soup, alchaincyf_manifest, lang)
        console_stats = hydrate_homepage_console_stats(
            soup,
            skill_count,
            problem_workflows,
            alchaincyf_manifest,
            lang,
        )
    else:
        weekly_replaced = False
        alchaincyf_replaced = False
        console_stats = 0

    case_studies_replaced = False
    if page_filename == "handbook.html":
        states = json.loads(CASE_STUDIES.read_text(encoding="utf-8"))["states"]
        case_studies_replaced = replace_case_studies_section(soup, states, lang)
        problem_workflows_replaced = replace_problem_workflows_section(soup, problem_workflows, lang)
    else:
        problem_workflows_replaced = False

    out_dir = out_root / lang
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / page_filename
    out_path.write_text(str(soup), encoding="utf-8")

    return {
        "page": page_filename,
        "lang": lang,
        "translations_applied": replaced,
        "skill_count_patches": sc_replaced,
        "case_studies": case_studies_replaced,
        "weekly_hot_skills": weekly_replaced,
        "alchaincyf_source": alchaincyf_replaced,
        "console_stats": console_stats,
        "problem_workflows": problem_workflows_replaced,
        "out": str(out_path.relative_to(REPO_ROOT)),
    }


def build_root_redirect() -> None:
    """docs/index.html → 按浏览器语言重定向到 /zh/ 或 /en/。"""
    redirect_html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Skills Manager AI Agent</title>
  <meta http-equiv="refresh" content="0; url=./en/index.html">
  <link rel="canonical" href="https://zjgulai.github.io/Agent_skills/en/index.html">
  <script>
    var lang = (navigator.language || navigator.userLanguage || 'en').toLowerCase();
    var target = lang.indexOf('zh') === 0 ? './zh/index.html' : './en/index.html';
    window.location.replace(target);
  </script>
</head>
<body style="background:#0a0a0a;color:#a1a1aa;font-family:sans-serif;padding:2rem;">
  <p>Redirecting… <a href="./en/index.html" style="color:#34d399;">English</a> · <a href="./zh/index.html" style="color:#34d399;">中文</a></p>
</body>
</html>
"""
    (DOCS / "index.html").write_text(redirect_html, encoding="utf-8")


def build_legacy_page_redirects() -> None:
    """Replace root-level legacy pages with language-aware redirects.

    The source-of-truth pages now live under docs/zh/ and docs/en/. Keeping
    stale root pages makes old links look like the website was not updated.
    """
    for page in [*PAGES_TO_BUILD, *PASSTHROUGH_PAGES]:
        if page == "index.html":
            continue
        redirect_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Skills Manager AI Agent</title>
  <meta http-equiv="refresh" content="0; url=./en/{page}">
  <script>
    var lang = (navigator.language || navigator.userLanguage || 'en').toLowerCase();
    var target = lang.indexOf('zh') === 0 ? './zh/{page}' : './en/{page}';
    window.location.replace(target);
  </script>
</head>
<body style="background:#0f172a;color:#cbd5e1;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;padding:2rem;">
  <p>Skills Manager AI Agent is redirecting to the latest localized page:
    <a href="./en/{page}" style="color:#0f766e;">English</a>
    ·
    <a href="./zh/{page}" style="color:#0f766e;">中文</a>
  </p>
</body>
</html>
"""
        (DOCS / page).write_text(redirect_html, encoding="utf-8")


def main() -> None:
    status = json.loads((DATA / "portal-status.json").read_text(encoding="utf-8"))
    skill_count = status["skill_count"]
    zh = load_zh_dict()
    weekly_hot = load_weekly_hot_skills()
    alchaincyf_manifest = load_alchaincyf_manifest()
    problem_workflows = load_problem_workflows()
    publish_weekly_hot_skills(weekly_hot)
    publish_alchaincyf_manifest(alchaincyf_manifest)

    results: list[dict] = []
    for page in PAGES_TO_BUILD:
        for lang in ("zh", "en"):
            results.append(build_one(page, lang, zh, weekly_hot, problem_workflows, alchaincyf_manifest, skill_count, DOCS))

    for page in PASSTHROUGH_PAGES:
        for lang in ("zh", "en"):
            (DOCS / lang).mkdir(parents=True, exist_ok=True)
            shutil.copy(ORIGINALS / page, DOCS / lang / page)

    mirror = REPO_ROOT / "data-mirror" / "skills-graph.png"
    if mirror.exists():
        target = DOCS / "assets" / "skills-graph.png"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(mirror, target)

    build_root_redirect()
    build_legacy_page_redirects()

    print(f"\n📦 Build complete  ·  skill_count={skill_count}")
    for r in results:
        cs = "cs✅" if r["case_studies"] else ""
        weekly = "weekly✅" if r["weekly_hot_skills"] else ""
        alchaincyf = "alchaincyf✅" if r["alchaincyf_source"] else ""
        workflows = "workflow✅" if r["problem_workflows"] else ""
        print(f"   · {r['lang']}/{r['page']:30}  i18n={r['translations_applied']:>3}  "
              f"sc_patch={r['skill_count_patches']}  console={r['console_stats']}  "
              f"{cs} {weekly} {alchaincyf} {workflows}")


if __name__ == "__main__":
    main()
