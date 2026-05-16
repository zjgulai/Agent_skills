# Skills Manager AI Agent

[![Site](https://img.shields.io/badge/site-online-10b981.svg?style=flat-square)](https://zjgulai.github.io/Agent_skills/)
[![Pages](https://img.shields.io/github/deployments/zjgulai/Agent_skills/github-pages?style=flat-square&label=Pages)](https://github.com/zjgulai/Agent_skills/deployments)
[![License](https://img.shields.io/github/license/zjgulai/Agent_skills?style=flat-square)](LICENSE)
[![Last commit](https://img.shields.io/github/last-commit/zjgulai/Agent_skills?style=flat-square)](https://github.com/zjgulai/Agent_skills/commits/main)
[![Made with](https://img.shields.io/badge/made%20with-OpenCode%20%2B%20Claude-6B5B95?style=flat-square)](https://github.com/anomalyco/opencode)
[![Bilingual](https://img.shields.io/badge/docs-EN%20%2B%20%E4%B8%AD%E6%96%87-blueviolet?style=flat-square)](https://zjgulai.github.io/Agent_skills/handbook.html)

> **OpenCode skills 缺失的生命周期层。** 安装 · 分类 · 图谱 · 诊断 · 推荐 —— 全部由你笔电上跑的本地 FastAPI + Vue portal 驱动。

📖 **[在线手册](https://zjgulai.github.io/Agent_skills/handbook.html)** · [快速开始](https://zjgulai.github.io/Agent_skills/getting-started.html) · [架构](https://zjgulai.github.io/Agent_skills/architecture.html)

---

## Why this exists

如果你在 OpenCode 上装了 **≥ 3 个 skill**，你大概率遇到过这些痛点：

- 🤔 **不记得哪个 skill 该 load**——"我要做 PPT，是 guizang-ppt-skill 还是 frontend-ui-ux？"
- 📝 **手工维护 INDEX.md 又累又错**——每装一个新 skill 都得手写分类、画图、改链接
- 🗂️ **skill 越多越混乱**——8 个、12 个、20 个之后，光"我装了什么"都说不清
- 🔧 **要在多台机器之间同步 skill 配置**——complex
- 🩺 **某个 skill 半个月没用，今天调忽然报错**——是依赖缺了还是 frontmatter 出问题？没法快速诊断

**Skills Manager AI Agent 把这 5 件事变成 11 条命令。**

- `/skill-install <url>` —— 一条命令，clone + 推断域 + 改 INDEX + 画 graph + 重渲，**端到端约 30 秒**
- `/skill-recommend "做一份瑞士风 PPT"` —— 描述任务，自动推 `load_skills=[...]`
- `/skill-doctor` —— 5 条规则体检每个已装 skill
- `/skill-graph-sync` —— 自动对齐 INDEX 与图谱
- ……另外 7 条命令覆盖更新、卸载、归类、portal 控制

它不替代 OpenCode 本身，**只在它之上加一层"管理"**。skill 仓库本体仍住在 `~/.config/opencode/skills/`，不动它的目录结构。

---

## 这是什么

两层一体：

- **`portal/`** — FastAPI + Vite/Vue 本地网站，提供 skills 的 REST API（5174）和可视化 UI（5173 / `https://skills-portal.localhost`）。`/Applications/Skills Portal.app` launcher 直达。
- **`.opencode/`** — OpenCode 自动发现的 11 个 slash 命令 + skills-manager subagent，编排 portal API + 三个元数据文件（`INDEX.md` / `skills-graph.mmd` / `skills-graph.png`）。
- **`agent/lib/`** — 命令共用的 Python 工具层（portal_client / domain_inference / index_md_writer / graph_writer / doctor）。

skill 仓库本体仍住在 `~/.config/opencode/skills/`，**不动**。本仓库只管"管理"它们。

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

完整参考：[手册 §3 11 个方法](https://zjgulai.github.io/Agent_skills/handbook.html#methods)

## 硬约束

- skill 文件本身的增删改 → **必走 portal API（5174）**
- `INDEX.md` / `skills-graph.mmd` / `skills-graph.png` 三个元数据文件 → **agent 直写**（带时间戳备份）

## 详细计划

- 在线手册：[zjgulai.github.io/Agent_skills](https://zjgulai.github.io/Agent_skills/handbook.html)
- 安装：[`docs/INSTALL.md`](docs/INSTALL.md)
- 主计划：[`.sisyphus/plans/01-skills-manager-agent-bootstrap.md`](.sisyphus/plans/01-skills-manager-agent-bootstrap.md)
- 执行 TODO：[`.sisyphus/plans/02-execution-todo.md`](.sisyphus/plans/02-execution-todo.md)
- 域分类规则：[`agent/docs/domain-taxonomy.md`](agent/docs/domain-taxonomy.md)

## License

[MIT](LICENSE) © 2026 Bestore.Pray

## Related repos

Agent_skills is the **methodology** layer of a three-repo system. The two companion repos share the same `agent/lib/manifest.py` (byte-identical, md5 `b46c2f55…`) and the same 4-client adapter pattern (opencode · codex · cursor · kimi):

- [Agent_hook](https://github.com/zjgulai/Agent_hook) — **enforcement** layer · 9 hooks · Claude Code style Python with stdin/stdout/exit-2 protocol
- [Agent_mcp](https://github.com/zjgulai/Agent_mcp) — **context** layer · 10 MCP servers · one install command writes to all 4 client configs
