# Skills Manager AI Agent · 项目规则

本项目级规则覆盖 `~/.config/opencode/AGENTS.md` 中冲突的部分（项目级优先），未覆盖的部分继承全局。

## 一、项目定位

**Skills Manager AI Agent** — OpenCode 用户级 skills 的统一管理 AI agent。
两层一体：

- `portal/` — FastAPI（5174）+ Vite/Vue（5173）本地网站，提供 skills REST API 和可视化 UI。
- `.opencode/` — OpenCode 项目级 commands + subagents 自动发现目录。
- `agent/lib/` — Python 工具层（被 commands 调用），`agent/docs/` — 人类可读 specs。

**Skill 仓库本体住在 [`~/.config/opencode/skills/`](file:///Users/lute/.config/opencode/skills/)，本项目不动它的目录结构，只管"管理"它们。**

## 二、必读

接到任何任务前先读：

1. [本计划主文档](file:///Users/lute/project/Agent/Agent_skills/.sisyphus/plans/01-skills-manager-agent-bootstrap.md) — 决策、目标结构、风险、边界
2. [执行 TODO list](file:///Users/lute/project/Agent/Agent_skills/.sisyphus/plans/02-execution-todo.md) — 28 项可勾选任务
3. [portal/README.md](file:///Users/lute/project/Agent/Agent_skills/portal/README.md) — portal API 参考与端口规范
4. [`~/.config/opencode/skills/INDEX.md`](file:///Users/lute/.config/opencode/skills/INDEX.md) — 6 域分类的真相源

## 三、硬约束（不可违反）

### 文件系统访问

| 对象 | 谁能改 | 怎么改 |
|---|---|---|
| `~/.config/opencode/skills/<name>/` 下的 skill 内容（增/删/装/卸） | **必走 portal API（5174）** | `POST /api/install/github` / `DELETE /api/skills/{name}` / `POST /api/refresh` |
| `~/.config/opencode/skills/INDEX.md` | agent 直接读写 | 通过 `agent/lib/index_md_writer.py`，**必须先 `cp INDEX.md INDEX.md.bak.{timestamp}` 备份** |
| `~/.config/opencode/skills/skills-graph.mmd` | agent 直接读写 | 通过 `agent/lib/graph_writer.py`，幂等 |
| `~/.config/opencode/skills/skills-graph.png` | agent 直接重渲 | 调用 `~/.config/opencode/skills/render-mermaid.py` |
| `portal/` 下的所有文件 | 谨慎改 | 改前必读 portal/README.md；改后必跑 A3-2 烟雾测试 |

### 端口约定

- 5174：portal backend（FastAPI / uvicorn）
- 5173：portal frontend（Vite dev server）
- `https://skills-portal.localhost`：portless HTTPS 入口（可选）

启动 portal 前**必须**先 `lsof -ti:5173,5174` 检查占用。

### 永远不做

- 直接 `cp` / `rm` / `git clone` 到 `~/.config/opencode/skills/<name>/`（除三个元数据文件外）
- 把 portal 监听绑到 0.0.0.0
- 在装新 skill 前不跑 `portal_client.ensure_running()`
- 用裸正则改 INDEX.md（必须 markdown AST 解析）
- 用 `background_cancel(all=true)` —— 始终按 taskId 单独取消

## 四、路径常量（agent 代码硬编码用这些）

```python
from pathlib import Path
import os

# Skill 仓库根
SKILLS_ROOT = Path(os.path.expanduser("~/.config/opencode/skills"))

# 三个元数据文件
INDEX_MD = SKILLS_ROOT / "INDEX.md"
SKILLS_GRAPH_MMD = SKILLS_ROOT / "skills-graph.mmd"
SKILLS_GRAPH_PNG = SKILLS_ROOT / "skills-graph.png"
RENDER_MERMAID_PY = SKILLS_ROOT / "render-mermaid.py"

# Portal API
PORTAL_BASE = "http://127.0.0.1:5174"

# Portal 工作目录（本仓库相对）
PROJECT_ROOT = Path(__file__).resolve().parents[2]   # agent/lib/foo.py → repo root
PORTAL_DIR = PROJECT_ROOT / "portal"
PORTAL_VENV_PYTHON = PORTAL_DIR / "backend" / ".venv" / "bin" / "python"
PORTAL_START_SCRIPT = PORTAL_DIR / "bin" / "start"
```

## 五、Python 运行时

- **统一使用 portal 自带的 venv**：`portal/backend/.venv/bin/python`
- 不污染系统 Python，不另装第二套依赖
- agent/lib/ 下所有脚本的 shebang 用 `#!/usr/bin/env python3`，但通过 venv python 调用
- 测试在仓库根用 `portal/backend/.venv/bin/python -m pytest tests/`

## 六、6 个域（domain 推断的真相源）

```
meta       AI 工程基础设施（agents, skills, hooks, plugins）
closeout   代码质量与交付闭环（review, commit, PR, release）
desktop    桌面应用工程（Tauri, Electron, WebView, native）
founder    创业与产品验证（MVP, ICP, pressure-test）
ip         知识产权交付（专利, 软著, copyright）
tooling    工具增强 · 横切层（git, screenshot, ppt, docx, image, markdown）
```

详见 [agent/docs/domain-taxonomy.md](file:///Users/lute/project/Agent/Agent_skills/agent/docs/domain-taxonomy.md)（落地时生成）。

## 七、不要做的事（v1 边界）

- 不做多账户 / 多用户 portal（仍仅 127.0.0.1）
- 不做 web UI 的"编辑分类"（INDEX 编辑只走 agent 命令）
- 不做 skill 版本回滚（git pull 即版本控制）
- 不写 dependency graph 可视化（依赖检查靠 `/skill-doctor` 文本报告）

## 八、提交规则

继承全局规则：**永不未经请求自动 commit**。即使所有任务完成，也要把 `git status` 留给用户决定。
