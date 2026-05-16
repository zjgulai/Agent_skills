---
name: skills-manager-agent-bootstrap
description: Skills Management AI Agent 项目从 0 到 1 的可执行计划。覆盖 portal 搬迁、AI agent 工程结构搭建、6 项能力（install/uninstall/update、分类、选型、健康检查、portal 启停、graph 同步）的 subagent + slash 命令落地、最终 guizang-ppt-skill 用 agent 自身命令完成首装验证。
---

# Skills Manager AI Agent · 工程化落地计划

> **当前状态**：`~/project/Agent/Agent_skills/` 空目录。
> **目标**：把 `~/.config/opencode/skills-portal/` 整体搬入并由本仓库接管，叠加一个 OpenCode 原生 AI agent 层（subagents + slash commands + AGENTS.md），最终用 agent 自己的 `/skill-install` 命令完成 `guizang-ppt-skill` 的安装。

---

## 一、需求拆解（用户确认结果）

| 决策项 | 答复 |
|---|---|
| Agent_skills 定位 | **把 portal 完全搬入并接管**（monorepo） |
| guizang-ppt-skill 安装 | **等 agent 项目搭好后用 agent 自身命令装** |
| Agent 能力（多选） | install/uninstall/update + 分类与 INDEX.md + 选型推荐 + 健康检查 + portal 启停 + graph 自动更新（**6 项全要**） |
| 仓库形态 | **git init + AGENTS.md + 完整工程结构** |

---

## 二、现状盘点（已通过工具验证）

### 2.1 已有资产（不可破坏）

| 路径 | 用途 | 状态 |
|---|---|---|
| `~/.config/opencode/skills/` | 6 个用户级 skill + INDEX.md + skills-graph.mmd + render-mermaid.py | **生产数据，永不删** |
| `~/.config/opencode/skills-portal/` | FastAPI（5174）+ Vite/Vue（5173），含 `.venv` + `node_modules` + `dist/` | **要搬迁，搬迁后用软链接保留旧路径以防其他工具引用** |
| `/Applications/Skills Portal.app` | AppleScript launcher，调用 `~/.config/opencode/skills-portal/bin/start` | **start 路径要保持有效**（靠软链接） |
| `~/.config/opencode/AGENTS.md` | 全局规则 | 项目级 AGENTS.md 优先级更高，但本计划不冲突 |

### 2.2 Portal 已实现的 API（搬迁后保持兼容）

```
GET    /api/health
GET    /api/skills              → skills-data.json（含 domains + skills + graph.mermaid_source）
GET    /api/skills/{name}       → 单 skill frontmatter
GET    /api/skills/{name}/markdown → SKILL.md 原文
POST   /api/install/github      {url, subdir?}
POST   /api/install/upload      multipart .md
DELETE /api/skills/{name}
POST   /api/refresh
```

> Agent 的所有"做事"命令都通过 HTTP 调用本 API，**不直接动文件系统**。这样 portal UI 和 agent 命令永远看到一致的状态。

### 2.3 当前缺口（agent 要补的能力）

| 缺口 | 现状 | 要补 |
|---|---|---|
| 自动分类 | INDEX.md 由人工写，新装 skill 默认进 `uncategorized` 域 | Agent 自动读 SKILL.md → 推断域 → 改 INDEX.md |
| Graph 同步 | 装/卸载后 mmd 不会自动改 | Agent 在新增/删除时改 mmd + 调 render-mermaid.py 重渲 |
| 健康检查 | 无 | Agent 扫所有 skill：frontmatter 合法性、依赖（如 .NET / mmdc / playwright）、被 INDEX 收录与否 |
| 选型推荐 | INDEX.md 三、典型场景套餐表是静态的 | 用户描述任务 → agent 推荐 `load_skills=[...]` 组合 |
| Portal 启停 | 只能手敲 `bin/start` | `/portal-start` `/portal-stop` `/portal-status` 命令 |
| Update | 无 | `/skill-update <name>` → `git -C ~/.config/opencode/skills/<name> pull` + 调 `/api/refresh` |

---

## 三、目标工程结构

```
Agent_skills/                              # = 本仓库根，已 git init
├── AGENTS.md                              # 项目级规则（覆盖 ~/.config/opencode/AGENTS.md）
├── README.md                              # 用户面向：30 秒了解、装、用
├── .gitignore                             # 忽略 .venv / node_modules / dist / .DS_Store / .sisyphus/scratch
├── .sisyphus/
│   └── plans/                             # 本计划 + 后续计划
├── portal/                                # ★ 从 ~/.config/opencode/skills-portal/ 搬过来
│   ├── README.md                          # 保留原文
│   ├── bin/start                          # 保留原文
│   ├── backend/
│   │   ├── app.py
│   │   ├── installer.py
│   │   ├── build_index.py
│   │   ├── data/skills-data.json          # gitignore（运行时产物）
│   │   └── .venv/                         # gitignore
│   └── frontend/
│       ├── src/
│       ├── package.json
│       ├── node_modules/                  # gitignore
│       └── dist/                          # gitignore
├── agent/                                 # ★ AI agent 工程层（新写）
│   ├── commands/                          # OpenCode slash 命令
│   │   ├── skill-install.md               # /skill-install <github_url> [--subdir X]
│   │   ├── skill-uninstall.md             # /skill-uninstall <name>
│   │   ├── skill-update.md                # /skill-update <name>|all
│   │   ├── skill-list.md                  # /skill-list（按域分组打印）
│   │   ├── skill-recommend.md             # /skill-recommend <task description>
│   │   ├── skill-classify.md              # /skill-classify <name>（重新归类 + 改 INDEX.md）
│   │   ├── skill-doctor.md                # /skill-doctor [name|all]（健康检查）
│   │   ├── skill-graph-sync.md            # /skill-graph-sync（INDEX.md → mmd → png）
│   │   ├── portal-start.md                # /portal-start
│   │   ├── portal-stop.md                 # /portal-stop
│   │   └── portal-status.md               # /portal-status
│   ├── subagents/
│   │   └── skills-manager.md              # 主 subagent，可被父 agent 通过 task() 调
│   ├── lib/                               # 命令共用 Python 工具
│   │   ├── portal_client.py               # HTTP 包装：GET/POST/DELETE 调 5174
│   │   ├── domain_inference.py            # 读 SKILL.md → 推断 domain（关键词匹配 + 兜底 LLM 提示）
│   │   ├── index_md_writer.py             # 安全改 INDEX.md（保留人工编辑）
│   │   ├── graph_writer.py                # 改 skills-graph.mmd（节点 + 至少一条边）
│   │   └── doctor.py                      # 健康检查规则集
│   └── docs/
│       ├── architecture.md                # 双层（portal API + agent 编排）的架构图
│       ├── command-reference.md           # 11 个 slash 命令使用手册
│       └── domain-taxonomy.md             # 6 域的判定规则（给 domain_inference.py 当人类可读 spec）
├── opencode.json                          # 项目级 OpenCode 配置：声明 commands/ 与 subagents/ 路径
└── tests/
    ├── test_portal_client.py              # 用 httpx 打 5174 健康检查
    ├── test_domain_inference.py           # 给若干 SKILL.md 样本，断言推断结果
    └── fixtures/                          # 样本 SKILL.md
```

---

## 四、分阶段执行计划（10 个原子任务）

> 每个任务 ≤30 分钟。每个任务结束都有可验证产物。失败回退点明确。

### 阶段 A · 仓库与搬迁（任务 1–3）

#### **任务 1**：仓库初始化

```bash
cd ~/project/Agent/Agent_skills
git init -b main
```

**产物**：`.git/`, `.gitignore`, `README.md`, `AGENTS.md`, `opencode.json`（最小骨架）

**验证**：`git status` 干净；`git log` 报 "no commits yet"。

#### **任务 2**：搬迁 skills-portal（关键不可逆操作 → 用 mv + symlink，**不复制**）

```bash
# 1. 实际搬动（mv 是原子的）
mv ~/.config/opencode/skills-portal ~/project/Agent/Agent_skills/portal

# 2. 软链接保留旧路径，让 /Applications/Skills Portal.app 和其他引用照常工作
ln -s ~/project/Agent/Agent_skills/portal ~/.config/opencode/skills-portal

# 3. 验证 launcher 还能用
ls -la ~/.config/opencode/skills-portal/bin/start    # 应能解析到 portal/bin/start
~/.config/opencode/skills-portal/bin/start --help    # 或运行后立刻 Ctrl+C
```

> **风险**：用户在搬迁期间正用 portal → 会断 5 秒。建议先 `lsof -ti:5173,5174 | xargs kill -9` 再搬。

**回退**：`mv portal ~/.config/opencode/skills-portal && rm ~/.config/opencode/skills-portal`（如果是软链接）。

**产物**：`portal/` 在仓库根，软链接活在原位。

#### **任务 3**：portal 路径常量审计

`portal/backend/build_index.py` 第 17 行硬编码 `SKILLS_ROOT = ~/.config/opencode/skills`。**保持不变**——skill 仓库就是要继续住在那里，搬的只是 portal 自己。

但 `portal/bin/start` 里有可能写死 `~/.config/opencode/skills-portal` 的工作目录。**必读必改**：

```bash
grep -rn "skills-portal" portal/bin/ portal/backend/ portal/frontend/vite.config.ts portal/frontend/package.json
```

把所有"自指"路径改成相对路径或 `$(dirname "$0")/..` 推导。

**验证**：`./portal/bin/start` 能从 Agent_skills 仓库根目录跑起来；浏览器打开 portal 主页正常显示 6 个 skill。

---

### 阶段 B · Agent 基础（任务 4–5）

#### **任务 4**：写 `AGENTS.md`（项目级规则）

要点：

- 项目定位（一句话）：Skills Management AI Agent，统一管理 OpenCode 用户级 skills。
- 必读：本计划的"四、分阶段"作为执行手册；portal 的 README.md 作为 API 参考。
- 工作流硬约束：**所有 skill 增删改必须走 portal API（5174）**，禁止 agent 直接 `cp` `rm` `git clone` 到 `~/.config/opencode/skills/`。原因：保证 portal UI 和 agent 视图一致。
- 例外：`/skill-update` 可以 `git -C` 进 skill 目录跑 `git pull`（portal 没有这个 API），但 pull 完必须立刻 `POST /api/refresh`。
- 安全：禁止 0.0.0.0 监听；portal start 前要查端口占用。

#### **任务 5**：搭 `opencode.json` + `agent/lib/portal_client.py`

`opencode.json` 至少声明：

```json
{
  "$schema": "https://opencode.ai/config.json",
  "commands": "./agent/commands",
  "subagents": "./agent/subagents"
}
```

`portal_client.py` 提供：

```python
class PortalClient:
    BASE = "http://127.0.0.1:5174"
    def health(self) -> dict: ...
    def list_skills(self) -> dict: ...                    # GET /api/skills
    def get_skill(self, name) -> dict: ...
    def get_markdown(self, name) -> str: ...
    def install_github(self, url, subdir=None) -> dict: ...
    def install_upload(self, md_path) -> dict: ...
    def uninstall(self, name) -> dict: ...
    def refresh(self) -> dict: ...
    def ensure_running(self) -> bool:
        """如果 5174 不通，自动调 portal/bin/start，等 health 返回 ok。"""
```

**验证**：`python -m agent.lib.portal_client health` 在 portal 跑着时返回 `{"ok": true, ...}`。

---

### 阶段 C · 核心命令（任务 6–8）

#### **任务 6**：3 个生命周期命令（install / uninstall / update）

| 命令 | 实现要点 |
|---|---|
| `/skill-install <url> [--subdir X]` | (1) `portal_client.ensure_running()`；(2) `install_github(url, subdir)`；(3) 收到 skill_name 后调用 `domain_inference.infer(name)`；(4) `index_md_writer.append(name, domain)`；(5) `graph_writer.add_node_and_edge(name, domain)`；(6) `python render-mermaid.py mmd png`；(7) 打印安装报告（域、触发词、被插入的 INDEX 章节） |
| `/skill-uninstall <name>` | (1) DELETE /api/skills/{name}；(2) `index_md_writer.remove(name)`；(3) `graph_writer.remove_node(name)`；(4) 重渲 graph |
| `/skill-update <name|all>` | name=all → 列出 `~/.config/opencode/skills/*/.git/`；逐个 `git -C pull`；最后 `POST /api/refresh` |

**风险**：`index_md_writer` 必须**幂等**且**保留人工编辑**——不能粗暴覆盖整段。策略：用 markdown AST 解析（`mistune`）找到 `### 域 N · XXX` 段落的表格，只在表格里追加/删除一行。

**验证**：

```bash
# 装一个测试用 skill（用 guizang-ppt-skill 作为首个真实 case，见任务 10）
# 然后看：
cat ~/.config/opencode/skills/INDEX.md | grep guizang
cat ~/.config/opencode/skills/skills-graph.mmd | grep guizang
ls ~/.config/opencode/skills/skills-graph.png   # 比上一次 mtime 新
```

#### **任务 7**：分类与图谱命令（classify / graph-sync）

`/skill-classify <name>`：手工触发重新归类，用于"装的时候推断错了"的情况。给用户列出 6 个域的简介，用户选号，写回 INDEX。

`/skill-graph-sync`：从 INDEX.md 反推 mmd（保证图永远是 INDEX 的视图），重渲 png。**幂等**。

`agent/lib/domain_inference.py` 的判定规则（人类可读 spec 写在 `agent/docs/domain-taxonomy.md`）：

| 域 | 关键词命中 |
|---|---|
| meta | `agent`, `subagent`, `skill`, `hook`, `plugin`, `CLAUDE.md`, `AGENTS.md` |
| closeout | `review`, `commit`, `PR`, `release`, `lint`, `ship` |
| desktop | `Tauri`, `Electron`, `WebView`, `WKWebView`, `WebKit`, `native`, `WindowManager`, `system tray` |
| founder | `MVP`, `ICP`, `pressure-test`, `validate`, `pivot`, `market fit` |
| ip | `专利`, `软著`, `patent`, `copyright`, `disclosure`, `国知局` |
| tooling | `git`, `screenshot`, `markdown`, `pdf`, `docx`, `ppt`, `image generation` |

> **guizang-ppt-skill 的预期判定**：description 含 "ppt"、"image prompts"、"covers"，应归 **tooling 域**。

> 若关键词命中 ≥2 个域 → 取命中最多的；若全 0 → 进 `uncategorized` + 提醒用户跑 `/skill-classify`。

#### **任务 8**：选型推荐 + 健康检查 + portal 控制

| 命令 | 实现要点 |
|---|---|
| `/skill-recommend <task>` | LLM prompt：把当前 INDEX.md 的"典型场景套餐"表 + 所有 skill 的 description 喂给 agent 自身的对话上下文，让它输出 `task(load_skills=[...], ...)` 模板 |
| `/skill-doctor [name|all]` | 规则：(a) frontmatter 解析得出来吗？(b) name 合法吗？(c) 在 INDEX 里吗？(d) 在 graph 里吗？(e) skill 自身宣称的依赖装了吗（如 patent skill 检查 mmdc + playwright，docx-toolkit 检查 .NET）。**容许部分通过**，输出红绿灯报告 |
| `/portal-start` | 检查端口；run `./portal/bin/start &`；等 `/api/health` ok |
| `/portal-stop` | `lsof -ti:5173,5174 \| xargs kill` |
| `/portal-status` | 端口、PID、最近一次 build_index 时间、skill_count |

---

### 阶段 D · 验证（任务 9–10）

#### **任务 9**：subagent + 测试

写 `agent/subagents/skills-manager.md`（OpenCode subagent 文件）：把 11 个命令的能力封装成"一个会自我决策的 subagent"，可以被父 agent `task(subagent_type="skills-manager", ...)` 调。

写 3 个最小 pytest：

```python
# test_portal_client.py
def test_health(): assert client.health()["ok"]

# test_domain_inference.py
def test_guizang_to_tooling():
    fm = {"name": "guizang-ppt-skill", "description": "AI-agent Skill for generating polished HTML slide decks..."}
    assert infer_domain(fm) == "tooling"

# test_index_md_idempotent.py
def test_append_then_remove_restores_file():
    before = INDEX_MD.read_text()
    append("test-skill", "tooling")
    remove("test-skill")
    assert INDEX_MD.read_text() == before
```

#### **任务 10**：用 agent 自身命令安装 guizang-ppt-skill（**端到端真实验证**）

```bash
# 1. 启 portal
/portal-start

# 2. 装
/skill-install https://github.com/op7418/guizang-ppt-skill

# 期望 agent 输出：
#   ✅ portal API 健康
#   ✅ git clone 成功（portal installer 完成）
#   ✅ frontmatter 校验通过：name=guizang-ppt-skill
#   ✅ 域推断：tooling（命中关键词：ppt, image prompts, covers）
#   ✅ INDEX.md 已更新：在 "### 域 6 · 工具增强" 下追加一行
#   ✅ skills-graph.mmd 已更新：节点 GZP，至少一条边
#   ✅ skills-graph.png 已重渲（4xxx × 1xxx）
#   ✅ POST /api/refresh 完成；portal 现在显示 7 个 skill

# 3. 健康检查
/skill-doctor guizang-ppt-skill
# 期望：所有项绿灯

# 4. 浏览器视觉验证
open https://skills-portal.localhost   # 或 http://localhost:5173
# 看到 guizang-ppt-skill 卡片在"工具增强"分组下

# 5. 试触发（用户要拿这个 skill 真用一次）
# 由用户在另一会话发：「帮我做一份瑞士风 PPT」
# 期望 OpenCode 自动 load 这个 skill
```

**通过条件**：上面 5 个期望全部满足，无回退。

---

## 五、关键风险与缓解

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| `mv skills-portal` 时 portal 还在跑 → uvicorn fd 被中断 | 中 | 数据无损（只是进程死），但用户当下可能在用 | 任务 2 **第一步**：`lsof -ti:5173,5174 \| xargs kill -9` |
| 软链接在某些 macOS 工具下不识别 | 低 | launcher .app 启动失败 | 用绝对路径软链接 + 任务 2 末尾验证 launcher 能跑 |
| `index_md_writer` 写崩 INDEX.md（破坏人工编辑） | **高** | INDEX.md 是 portal UI 的分类来源 | (a) 改之前 `cp INDEX.md INDEX.md.bak.{timestamp}`；(b) 用 markdown AST 改而非正则；(c) test_index_md_idempotent 必须过 |
| domain_inference 把所有 skill 都判成 uncategorized | 中 | 用户体验差，每装一个都要手工 classify | 任务 9 用现有 6 个 skill 当回归集，准确率必须 ≥5/6 |
| graph_writer 出 mermaid 语法错 → render-mermaid.py 报错 | 中 | png 不更新，但 mmd 也不能用 | 渲染前先用 `node -e "..."` 或 `mmdc --validate` 干跑一遍 |
| portal 5174 自启在用户没装 .venv 时炸 | 低 | 任务 5 起就坏 | `portal_client.ensure_running()` 检测到 venv 缺失时给明确错误：`portal/backend/.venv 缺失，跑 portal/bin/init-venv` |

---

## 六、不做的事（v1 边界）

- **不做**多用户多账户 portal（任然是 127.0.0.1）。
- **不做** skills 版本管理 / 回滚（git pull 就是版本控制）。
- **不做** Web UI 的"编辑分类"（只在 agent 命令侧改 INDEX，portal UI 只读展示）。
- **不做** skill 依赖图（patent → playwright 这种依赖关系）的图形可视化——继续靠 `/skill-doctor` 文本报告。
- **不做** `~/.config/opencode/skills-portal/` 软链接的清理；保留兼容期。

---

## 七、确认门（已锁定 · 2026-05-15）

| 决策 | 用户确认 |
|---|---|
| 搬迁时机 | **直接搬**（任务 2 第一步先 kill 5173/5174） |
| agent/lib 语言 | **Python 3.9 复用 portal 的 `.venv`**（不再装第二套依赖） |
| 文件系统访问硬约束 | **三文件 agent 直写**：`INDEX.md` / `skills-graph.mmd` / `skills-graph.png`；**其他 skill 增删改照样走 portal API**（保证 portal UI 状态一致）|

---

## 八、Momus Plan Review（2026-05-15）

**判定**：**[OKAY]**（最高级）

**关键利好**：`portal/bin/start` 已用 `$(dirname "${BASH_SOURCE[0]}")` 做相对路径推导，搬迁后自动适配。**任务 3「路径常量审计」从"必改"降级为"只需一次性验证"**。

---

## 九、可执行 TODO list（详见配套文件）

[02-execution-todo.md](02-execution-todo.md) 给出按 10 个原子任务展开的 28 条勾选项，每条都有：
- 触发条件 / 输入
- 执行动作（命令 / 文件路径 / 写什么）
- 验证手段（怎么知道这一步真的做完了）
- 回退方案（出错怎么撤）
