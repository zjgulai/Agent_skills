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
from pathlib import Path

from bs4 import BeautifulSoup

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS = REPO_ROOT / "docs"
SRC = DOCS / "_src"
ORIGINALS = SRC / "originals"
DATA = DOCS / "data"
I18N = SRC / "i18n"
CASE_STUDIES = SRC / "case-studies.json"

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
    """因为输出移到 docs/<lang>/ 子目录，资源相对路径需要 ../ 前缀。"""
    for el in soup.find_all(attrs={"href": True}):
        href = el["href"]
        if href.startswith("./"):
            el["href"] = "../" + href[2:]
    for el in soup.find_all(attrs={"src": True}):
        src = el["src"]
        if src.startswith("./"):
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
        title = s[f"title_{lang}"]
        desc = s[f"desc_{lang}"]
        bullets = s[f"bullets_{lang}"]
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
            parts.append(
                f'  <a href="../assets/screenshots/{png}" target="_blank" rel="noopener">'
                f'<img src="../assets/screenshots/{png}" alt="{alt}" class="graph-img"></a>'
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


def build_one(page_filename: str, lang: str, zh: dict[str, dict[str, str]],
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

    case_studies_replaced = False
    if page_filename == "handbook.html":
        states = json.loads(CASE_STUDIES.read_text(encoding="utf-8"))["states"]
        case_studies_replaced = replace_case_studies_section(soup, states, lang)

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


def main() -> None:
    status = json.loads((DATA / "portal-status.json").read_text(encoding="utf-8"))
    skill_count = status["skill_count"]
    zh = load_zh_dict()

    results: list[dict] = []
    for page in PAGES_TO_BUILD:
        for lang in ("zh", "en"):
            results.append(build_one(page, lang, zh, skill_count, DOCS))

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

    print(f"\n📦 Build complete  ·  skill_count={skill_count}")
    for r in results:
        cs = "cs✅" if r["case_studies"] else ""
        print(f"   · {r['lang']}/{r['page']:30}  i18n={r['translations_applied']:>3}  "
              f"sc_patch={r['skill_count_patches']}  {cs}")


if __name__ == "__main__":
    main()
