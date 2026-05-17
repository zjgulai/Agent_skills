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

### 一句话搞定（推荐）

直接在 opencode 里说：
```
/skill-install https://github.com/<org>/<repo>
```

agent 会自动跑完 12 步：
0. **scan** 仓库结构 → 自动识别单 skill / monorepo / catalog stub
1. portal ensure
2. **一次 clone 批量装**（monorepo 时 17× 提速）
3-7. 读 frontmatter → 域推断 → INDEX.md → graph + render → portal refresh
8. `bin/sync-data` 镜像元数据到 `data-mirror/`
9. 问你最少的问题补 case-study（monorepo 合为 1 个 state；预填可用时不问）
10-11. git commit + push
12. 报告 GitHub Actions CI 链接

### dry-scan 预览（推荐先扫再装）

```
/skill-install <url> --dry-scan
```

仅做：scan + 读 frontmatter + 域推断 + 与现有 skill 重叠分析 → 输出报告，**不下载、不装**。让你决策后再装。已验证有效场景：
- catalog stub 仓库（如 open-design）：报告显示 SKILL.md 只是"广告卡"，建议改装上游正牌
- 命名违规仓库（如 `ckm:` 前缀）：报告显示哪些会被 portal 拒绝
- monorepo 含太多无关 skill：报告让你按主题挑

### 手工退路

```bash
# 1. 装到本地
portal/backend/.venv/bin/python -m agent.lib.portal_client install <URL> [SUBDIR]
# 或一次 clone 批量装
portal/backend/.venv/bin/python -m agent.lib.portal_client install-monorepo <URL> [SUBDIR1 SUBDIR2 ...]
# 2. 同步元数据
bin/sync-data
# 3. 编辑 docs/_src/case-studies.json 追加 State N+1
# 4. 提交
git add data-mirror/ docs/_src/case-studies.json
git commit -m "feat(skills): add <skill-name>"
git push
```

## 边界 / 已知限制

### v2 已修复 ✅
- `data-i18n-attr` 属性已支持（之前 handbook 残留 188 个 i18n key 未渲染）
- case study 动态化（`case-studies.json` → 多 state，含 agent-reach / superpowers / gstack / ui-ux-pro-max / bb-browser / notebooklm 等历史快照）
- hero 截图改为 `assets/skills-graph.png`（实时图谱，不再是 7-skill 时代旧截图）
- monorepo 一次 clone 批量装（`install_monorepo_from_github`），17× 加速
- scan / install 两端 SKIP_DIRS 对齐（保留 `.claude/skills/`，跳过 `.git / node_modules` 等基础设施）
- 友好 frontmatter 校验错误（`name 'ckm:foo' contains ':'` 时给 sanitized 建议）

### 已知工程限制
- **超大产品级仓库 git clone 不可行**：实测 `nexu-io/open-design`（1011 commits + apps + design-systems）即便 `--filter=blob:none` 仍 5+ 分钟无果。对策：用 GitHub raw URL 直拉 SKILL.md，或走上游正牌仓库
- **catalog stub 仓库**：有些仓库（如 open-design）的 skills/ 目录是「广告卡片」，每张卡只有 SKILL.md + upstream 字段。装这种卡片等于装路标——应顺 upstream 找真仓库。dry-scan 流程已验证有效
- **subdir name ≠ frontmatter name**：例如 `Leonxlnx/taste-skill/skills/taste-skill/SKILL.md` 的 frontmatter 实际是 `name: design-taste-frontend`。portal 以 frontmatter 为准

### v3 待办
- `graph-state-0/1/2.png` 仍是历史快照 — 未自动随新装 skill 重生
- case-studies.json 仍手工维护 — 未来可让 `bin/sync-data --diff-skills` 检测后自动追加 state 草稿
