# Skills Manager AI Agent

OpenCode 用户级 skills 的统一管理 AI agent。在 `~/.config/opencode/skills/` 之上叠加一层会自动安装、分类、画图、健康检查、选型推荐的智能编排。

## 这是什么

两层一体：

- **`portal/`** — FastAPI + Vite/Vue 本地网站，提供 skills 的 REST API（5174）和可视化 UI（5173 / `https://skills-portal.localhost`）。`/Applications/Skills Portal.app` launcher 直达。
- **`.opencode/`** — OpenCode 自动发现的 11 个 slash 命令 + skills-manager subagent，编排 portal API + 三个元数据文件（`INDEX.md` / `skills-graph.mmd` / `skills-graph.png`）。
- **`agent/lib/`** — 命令共用的 Python 工具层（portal_client / domain_inference / index_md_writer / graph_writer / doctor）。

skill 仓库本体仍住在 [`~/.config/opencode/skills/`](file:///Users/lute/.config/opencode/skills)，**不动**。本仓库只管"管理"它们。

## 30 秒上手

> 第一次装？看 [`docs/INSTALL.md`](docs/INSTALL.md) —— 完整的新机器从 0 安装手册。
> 已经装好？继续：

```bash
# 进入仓库（OpenCode 自动加载本目录的 AGENTS.md + .opencode/commands/ + .opencode/agent/）
cd ~/project/Agent/Agent_skills

# 起 portal
./portal/bin/start

# 在 OpenCode 对话里
/skill-install https://github.com/op7418/guizang-ppt-skill   # 一键装新 skill
/skill-list                                                   # 看现有清单
/skill-doctor                                                 # 健康检查
/skill-recommend "我要做一份瑞士风 PPT"                          # 选型推荐
```

## 11 个命令

| 命令 | 用途 |
|---|---|
| `/skill-install <url> [--subdir X]` | GitHub URL 一键装 skill，自动分类、改 INDEX、画 graph |
| `/skill-uninstall <name>` | 卸载 + 反向清理元数据 |
| `/skill-update <name\|all>` | git pull + 刷新索引 |
| `/skill-list` | 按域分组打印所有已装 skill |
| `/skill-recommend <task>` | 根据任务描述推荐 `load_skills=[...]` 组合 |
| `/skill-classify <name>` | 手工重新归类 |
| `/skill-doctor [name\|all]` | 5 条规则健康检查 |
| `/skill-graph-sync` | INDEX.md → mmd → png 重渲（幂等） |
| `/portal-start` `/portal-stop` `/portal-status` | Portal 生命周期 |

## 硬约束

- skill 文件本身的增删改 → **必走 portal API（5174）**
- `INDEX.md` / `skills-graph.mmd` / `skills-graph.png` 三个元数据文件 → **agent 直写**（带时间戳备份）

## 详细计划

- 安装：[`docs/INSTALL.md`](docs/INSTALL.md)
- 主计划：[`.sisyphus/plans/01-skills-manager-agent-bootstrap.md`](.sisyphus/plans/01-skills-manager-agent-bootstrap.md)
- 执行 TODO：[`.sisyphus/plans/02-execution-todo.md`](.sisyphus/plans/02-execution-todo.md)
- 域分类规则：[`agent/docs/domain-taxonomy.md`](agent/docs/domain-taxonomy.md)
