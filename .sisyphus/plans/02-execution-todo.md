---
name: skills-manager-execution-todo
description: Skills Manager AI Agent 的 28 项可勾选 TODO list，按 10 个原子任务展开。每条都给出动作、验证、回退。与 OpenCode todo 系统同步。
---

# Skills Manager AI Agent · 执行 TODO list

> 配套主计划：[`01-skills-manager-agent-bootstrap.md`](01-skills-manager-agent-bootstrap.md)
> 决策已锁定（见主计划第七节）。

---

## 阶段 A · 仓库与搬迁

### 任务 1 · 仓库初始化

- [ ] **A1-1** `cd /Users/lute/project/Agent/Agent_skills && git init -b main`
  - 验证：`git status` 输出 "On branch main / No commits yet"
- [ ] **A1-2** 写 `.gitignore`，至少包含：`.DS_Store`、`portal/backend/.venv/`、`portal/backend/data/skills-data.json`、`portal/frontend/node_modules/`、`portal/frontend/dist/`、`portal/frontend/tsconfig.tsbuildinfo`、`.sisyphus/scratch/`、`__pycache__/`、`*.pyc`
  - 验证：`git status --ignored` 显示对应路径已被忽略
- [ ] **A1-3** 写最小 `README.md`（30 秒说明：这是什么、谁用、装哪儿、怎么用）
  - 不要 emoji，不要 marketing 语言

### 任务 2 · 搬迁 skills-portal（不可逆操作 · 用 `mv` + symlink）

- [ ] **A2-1** 杀掉 portal 进程：`lsof -ti:5173,5174 | xargs kill -9 2>/dev/null || true`
  - 验证：`lsof -ti:5173,5174` 无输出
- [ ] **A2-2** 原子搬迁：`mv ~/.config/opencode/skills-portal /Users/lute/project/Agent/Agent_skills/portal`
  - 验证：`ls Agent_skills/portal/bin/start` 存在；`ls ~/.config/opencode/skills-portal` 报 "No such file"
- [ ] **A2-3** 建反向软链接保留兼容：`ln -s /Users/lute/project/Agent/Agent_skills/portal ~/.config/opencode/skills-portal`
  - 验证：`readlink ~/.config/opencode/skills-portal` 指向 Agent_skills/portal
- [ ] **A2-4** 启动 launcher 烟雾测试：`/Applications/Skills\ Portal.app` 启动后能打开浏览器（确认 AppleScript 通过软链接找到 start）
  - 失败回退：`rm ~/.config/opencode/skills-portal && mv Agent_skills/portal ~/.config/opencode/skills-portal`

### 任务 3 · 路径常量验证（Momus 已确认 bin/start 自适应）

- [ ] **A3-1** `grep -rn "skills-portal" portal/bin/ portal/backend/*.py portal/frontend/vite.config.ts portal/frontend/package.json` → 列出所有自指
  - 验证：仅出现在注释 / docs / README，不在执行路径中
- [ ] **A3-2** 从 Agent_skills 根目录跑 `./portal/bin/start`，浏览器打开 `https://skills-portal.localhost` 或 `http://localhost:5173`
  - 验证：portal 首页显示 6 个 skill 卡片（与搬迁前一致）；`curl http://127.0.0.1:5174/api/health` 返回 `{"ok": true, ...}`
  - 然后 `Ctrl+C` 停掉，留给后续 `/portal-start` 命令验证

---

## 阶段 B · Agent 基础

### 任务 4 · `AGENTS.md`（项目级规则）

- [ ] **B4-1** 写 `/Users/lute/project/Agent/Agent_skills/AGENTS.md`，至少包含：
  - 项目一句话定位
  - 必读：本计划 + portal README
  - 硬约束：**增删 skill 走 portal API（5174）**；**INDEX.md / skills-graph.mmd / skills-graph.png 三文件 agent 直接写**（这是 portal 不管的元数据层）
  - 路径常量：skill 仓库 `~/.config/opencode/skills/`、portal 工作目录 `./portal/`、portal API base `http://127.0.0.1:5174`
  - 中文优先（继承 ~/.config/opencode/AGENTS.md 规则）

### 任务 5 · `opencode.json` + portal_client.py

- [ ] **B5-1** 写 `opencode.json`：声明 `commands` 路径为 `./agent/commands`、`subagents` 路径为 `./agent/subagents`
  - 验证：从本目录启动 opencode 后，`/skill-` 前缀命令能被发现（即便还没全部实现）
- [ ] **B5-2** 写 `agent/lib/portal_client.py`：
  - 方法：`health()`, `list_skills()`, `get_skill(name)`, `get_markdown(name)`, `install_github(url, subdir=None)`, `uninstall(name)`, `refresh()`, `ensure_running()`
  - `ensure_running()` 逻辑：先 `health()` 试 1 次；失败则 spawn `./portal/bin/start`，轮询 health 最多 15 秒；超时报具体错（venv 缺失 / 端口被占 / 别的）
  - 用 `portal/backend/.venv/bin/python` 执行，不污染系统 Python
  - 验证：`portal/backend/.venv/bin/python -m agent.lib.portal_client health` 返回 ok（portal 在跑时）

---

## 阶段 C · 核心命令

### 任务 6 · 生命周期 3 命令

- [ ] **C6-1** 实现 `agent/lib/domain_inference.py` + 配套 `agent/docs/domain-taxonomy.md`（人类可读判定 spec）
  - 输入：skill name + description
  - 输出：`domain_id ∈ {meta, closeout, desktop, founder, ip, tooling, uncategorized}`
  - 规则：6 域关键词命中 → 取命中最多的；全 0 → uncategorized
- [ ] **C6-2** 实现 `agent/lib/index_md_writer.py`
  - `append(name, domain, description)`：找到对应"### 域 N · XXX"段落的表格，幂等追加一行
  - `remove(name)`：删除该 skill 在表格里的行
  - **写之前必须 `cp INDEX.md INDEX.md.bak.{timestamp}`**
  - 用 markdown AST 解析（`mistune`），不用裸正则
- [ ] **C6-3** 实现 `agent/lib/graph_writer.py`
  - `add_node_and_edge(name, domain)`：往 mmd 加节点（`SHORTID[name]:::{domain}Domain`）+ 至少一条边到同域已有节点
  - `remove_node(name)`：删节点 + 删所有涉及它的边
  - 渲染调用：`python ~/.config/opencode/skills/render-mermaid.py mmd png`
- [ ] **C6-4** 写 `agent/commands/skill-install.md`：编排上述 lib，按主计划任务 6 的 7 步流程
- [ ] **C6-5** 写 `agent/commands/skill-uninstall.md`：反向 4 步
- [ ] **C6-6** 写 `agent/commands/skill-update.md`：支持 `<name>` 或 `all`；执行 `git -C ~/.config/opencode/skills/<n> pull` + `POST /api/refresh`

### 任务 7 · 分类与图谱

- [ ] **C7-1** 写 `agent/commands/skill-classify.md`：列出 6 域简介 → 用户选号 → 调 `index_md_writer.move()` + `graph_writer.change_class()`
- [ ] **C7-2** 写 `agent/commands/skill-graph-sync.md`：从 INDEX.md 反推 mmd（保证图永远是 INDEX 的视图） + 重渲 png（**幂等**）
- [ ] **C7-3** 写 `agent/commands/skill-list.md`：调 `GET /api/skills`，按 domains 分组打印，每个 skill 显示 name + 1 行描述

### 任务 8 · 选型推荐 + 健康检查 + portal 控制

- [ ] **C8-1** 写 `agent/commands/skill-recommend.md`：把 INDEX.md "典型场景套餐表" + 所有 skill description 加载进 prompt，输出 `task(load_skills=[...], ...)` 模板
- [ ] **C8-2** 实现 `agent/lib/doctor.py`：5 条规则（frontmatter / name 合法 / 在 INDEX / 在 graph / 依赖就位），输出红绿灯 dict
- [ ] **C8-3** 写 `agent/commands/skill-doctor.md`：调 `doctor.py`，单 skill 或全量扫描
- [ ] **C8-4** 写 `agent/commands/portal-start.md`：调 `portal_client.ensure_running()`，打印 URL
- [ ] **C8-5** 写 `agent/commands/portal-stop.md`：`lsof -ti:5173,5174 | xargs kill`
- [ ] **C8-6** 写 `agent/commands/portal-status.md`：打端口 / PID / build_index 时间 / skill_count

---

## 阶段 D · 验证

### 任务 9 · Subagent + 测试

- [ ] **D9-1** 写 `agent/subagents/skills-manager.md`：把 11 命令的能力封装成一个会自我决策的 subagent
  - 可被 `task(subagent_type="skills-manager", ...)` 调用
- [ ] **D9-2** 写 `tests/test_portal_client.py`：起 portal，调 `health()` 断言 ok
- [ ] **D9-3** 写 `tests/test_domain_inference.py`：6 个现有 skill 的 frontmatter 当回归集，准确率 ≥ 5/6
- [ ] **D9-4** 写 `tests/test_index_md_idempotent.py`：append("test", "tooling") → remove("test") → INDEX.md 字节完全一致
- [ ] **D9-5** `cd Agent_skills && portal/backend/.venv/bin/python -m pytest tests/` 全绿

### 任务 10 · 端到端真实验证（用 agent 自己装 guizang-ppt-skill）

- [ ] **D10-1** `/portal-start`：portal 起来，health ok
- [ ] **D10-2** `/skill-install https://github.com/op7418/guizang-ppt-skill`：期望输出全部 ✅
  - clone ok / frontmatter 校验通过 / 推断为 `tooling` 域 / INDEX.md 已加行 / mmd 加节点 / png 重渲 / refresh ok / portal 显示 7 个 skill
- [ ] **D10-3** `/skill-doctor guizang-ppt-skill`：5 条规则全绿
- [ ] **D10-4** 浏览器打开 portal，确认"工具增强"分组下有 guizang-ppt-skill 卡片
- [ ] **D10-5** 提示用户：现在可以新开一个对话发"帮我做一份瑞士风 PPT"，OpenCode 应自动 load 这个 skill

---

## 完成判据（10 任务全打勾后必须再全部满足）

1. `git status` 干净，没有未追踪 / 未提交的非 ignored 文件
2. `portal/bin/start` 从仓库根能起来，UI 显示 7 个 skill（含 guizang-ppt-skill）
3. `~/.config/opencode/skills/guizang-ppt-skill/SKILL.md` 真实存在
4. `~/.config/opencode/skills/INDEX.md` 第 124 行附近的"### 域 6 · 工具增强"表格里有 guizang 那一行（不再是"暂为空"）
5. `~/.config/opencode/skills/skills-graph.mmd` 含 GZP 节点，`skills-graph.png` mtime > 2026-05-15 任务开始时间
6. `portal/backend/.venv/bin/python -m pytest tests/ -q` 全绿
7. 主计划第五节 6 个风险全部命中缓解措施（即使没触发，缓解代码存在）

---

## 备注

- 每完成一个 [ ] 就立刻改 [x]，**不批量更新**
- 出问题时**先看 portal/backend uvicorn 日志**：`tail -f /tmp/portal-uvicorn.log`（如果用 bin/start 起的话）
- **不要修** `~/.config/opencode/skills/` 下任何 skill 自身的内容（只允许改三个元数据文件）
- **不要装** v1 边界外的能力（见主计划第六节）
