# `docs/` 动态站构建系统

本目录托管 GitHub Pages 静态站。**与原 v1 不同**：所有页面现在是 `_src/` + 数据双语构建出来的，不再手工维护过期的 skill 计数和列表。

## 总览

```
data-mirror/                         # 真相源（git tracked）
├── INDEX.md
├── skills-graph.mmd
└── skills-graph.png

docs/
├── _src/                            # 构建源码（不发布到 Pages）
│   ├── originals/                   # 原 HTML 备份（构建期 read-only）
│   ├── i18n/zh.json                 # 中文字典（285 条）
│   ├── data-collect.py              # 解析 INDEX.md → JSON
│   ├── i18n-extract.py              # 一次性脚本：原 HTML → zh.json
│   └── build.py                     # 主构建器（DOM 替换 + 双语渲染）
├── data/                            # data-collect.py 输出
│   ├── skills.json
│   ├── domains.json
│   └── portal-status.json
├── zh/, en/                         # build.py 输出（双语版）
├── assets/                          # 静态资源（截图等）
└── index.html                       # 顶层语言重定向页（build.py 写入）
```

## 本地构建

```bash
bin/sync-data                              # 1. 同步 ~/.config/opencode/skills/ → data-mirror/
portal/backend/.venv/bin/python docs/_src/data-collect.py   # 2. 生成 JSON
portal/backend/.venv/bin/python docs/_src/build.py          # 3. 构建 HTML
```

构建后浏览器打开：
- `docs/index.html` 自动跳转到对应语言版
- `docs/zh/index.html` 中文版
- `docs/en/index.html` 英文版

## CI 自动构建

工作流：`.github/workflows/deploy-docs.yml`

触发条件：
- `data-mirror/**` 变更
- `docs/**` 变更
- 手动 `workflow_dispatch`

CI 步骤：
1. checkout
2. setup Python 3.12
3. install jinja2 / bs4 / lxml / pyyaml
4. `python docs/_src/data-collect.py`
5. `python docs/_src/build.py`
6. mirror `data-mirror/skills-graph.png` → `docs/assets/skills-graph.png`
7. upload + deploy Pages artifact

## GitHub Pages 配置（仅首次需要）

Settings → Pages → Source 改为 **GitHub Actions**（不是 "Deploy from a branch"）。

## 装新 skill 后的流程

```bash
/skill-install <github-url>           # 1. 装到 ~/.config/opencode/skills/
bin/sync-data                          # 2. 镜像到 data-mirror/
# 3. 在 docs/_src/case-studies.json 里追加一条 State N+1 记录（含 trigger_cmd / desc / bullets / delta）
git add data-mirror/ docs/_src/case-studies.json
git commit -m "feat(skills): add <skill-name>"
git push                               # 4. CI 自动重建并部署
```

## 边界 / 已知限制（v2 后）

- `handbook.html` 历史 `data-i18n-attr` 已支持，所有页面 i18n key 残留为 0 ✅
- case study 现已动态化，按 `case-studies.json` 渲染（State 0 → 3，含 agent-reach）✅
- `assets/screenshots/portal-after-install.png` 已被 build.py 替换为 `assets/skills-graph.png`（你当前真实图谱）✅
- v3 范围：`graph-state-0/1/2.png` 仍是历史快照，新装 skill 时不会自动生成新的截图（需要在装 skill 后手动跑 `render-mermaid.py` 截一张新的 PNG 进 `assets/screenshots/`）
- v3 范围：case-studies.json 是手工维护的（追加 State N+1 是 sync 流程的一环），未来可以让 `bin/sync-data` 检测 diff 自动追加
