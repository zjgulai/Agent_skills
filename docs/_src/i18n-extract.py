"""i18n-extract.py — 从原 docs/*.html 抽出 window.I18N_ZH[...] 字典到 YAML。

输入  docs/index.html, docs/handbook.html, ...
输出  docs/_src/i18n/zh.yaml, docs/_src/i18n/en.yaml
       (en 通过抽取 data-i18n 节点的 innerText 作为英文兜底)

只跑一次：完成模板重构后，本脚本即可弃用。但保留下来便于回归追溯。
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS = REPO_ROOT / "docs"
OUT = REPO_ROOT / "docs" / "_src" / "i18n"

HTML_PAGES = [
    "index.html",
    "handbook.html",
    "architecture.html",
    "domains.html",
    "commands.html",
    "case-study.html",
    "getting-started.html",
]

DICT_PATTERN = re.compile(
    r"window\.I18N_ZH\[['\"]([^'\"]+)['\"]\]\s*=\s*\{(.+?)\};",
    re.DOTALL,
)


def js_obj_to_pairs(body: str) -> list[tuple[str, str]]:
    """轻量级 JS 对象字面量解析。仅支持 'key': 'value', 形态。"""
    pairs: list[tuple[str, str]] = []
    pos = 0
    n = len(body)
    while pos < n:
        m_key = re.search(r"['\"]([^'\"]+)['\"]\s*:\s*", body[pos:])
        if not m_key:
            break
        key = m_key.group(1)
        cur = pos + m_key.end()
        if cur >= n:
            break
        quote = body[cur]
        if quote not in {'"', "'"}:
            pos = cur + 1
            continue
        cur += 1
        value_start = cur
        while cur < n:
            if body[cur] == "\\":
                cur += 2
                continue
            if body[cur] == quote:
                break
            cur += 1
        value = body[value_start:cur]
        try:
            value = json.loads(f'"{value}"') if quote == '"' else json.loads(
                f'"{value.encode().decode("unicode_escape")}"'.replace("\\", "\\\\")
            )
        except Exception:
            value = value
        pairs.append((key, value))
        pos = cur + 1
    return pairs


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    zh: dict[str, dict[str, str]] = {}
    for page in HTML_PAGES:
        path = DOCS / page
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for m in DICT_PATTERN.finditer(text):
            page_key = m.group(1)
            body = m.group(2)
            pairs = js_obj_to_pairs(body)
            if pairs:
                zh.setdefault(page_key, {})
                for k, v in pairs:
                    zh[page_key][k] = v

    out_path = OUT / "zh.json"
    out_path.write_text(json.dumps(zh, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    total = sum(len(v) for v in zh.values())
    print(f"✅ {out_path.relative_to(REPO_ROOT)}  — {len(zh)} 页 / {total} 条")
    for page_key, kv in zh.items():
        print(f"   · {page_key:18} {len(kv):>3} keys")


if __name__ == "__main__":
    main()
