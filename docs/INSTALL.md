# 新机器安装手册

把 Skills Manager AI Agent 从 0 装到能用，覆盖 macOS（首选）+ Linux（最小适配）。Windows 不在 v1 支持范围。

> 一切假设你已经有 git、curl、Python 3.9+、Node 22+、OpenCode CLI。没有这些先装这些。

---

## 一、先决条件

| 工具 | 最低版本 | 检查 |
|---|---|---|
| git | 2.30+ | `git --version` |
| Python | 3.9+ | `python3 --version` |
| Node | 22+ | `node --version` |
| npm | 11+ | `npm --version` |
| OpenCode CLI | 已登录账户 | `opencode --version` |

可选但强烈推荐（macOS）：
- `portless`（提供 `https://*.localhost`，免去 5173/5174 端口冲突烦恼）：见本文 §六

---

## 二、Clone + 装 portal

```bash
# 1. clone 到合适位置（路径任意，下面假设 ~/project/Agent/Agent_skills）
mkdir -p ~/project/Agent
cd ~/project/Agent
git clone https://github.com/zjgulai/Agent_skills.git
cd Agent_skills

# 2. 装 portal backend venv
cd portal/backend
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install fastapi 'uvicorn[standard]' pyyaml python-multipart httpx mistune pytest
cd ../..

# 3. 装 portal frontend 依赖（首次需要拉 node_modules）
cd portal/frontend
npm install
cd ../..

# 4. 验证 portal 能起
./portal/bin/start
# → 看到 "✅ Skills Portal up:" 即成功，Ctrl+C 停掉
```

---

## 三、建 skills 仓库目录 + 三个元数据文件

如果你是**新装机**（之前从来没用过这套），需要先把 skill 仓库根建好：

```bash
mkdir -p ~/.config/opencode/skills
cd ~/.config/opencode/skills

# 三个元数据文件
touch INDEX.md skills-graph.mmd
# render-mermaid.py 从仓库源码复制（agent 调它重渲 graph PNG）
cp ~/project/Agent/Agent_skills/portal/backend/.venv/bin/python /dev/null  # 只是触发权限
```

如果你已经用过、有现成内容，**跳过这步**，保留原 INDEX.md 等。

INDEX.md 最小骨架（仅当从 0 开始时手写）：

```markdown
---
name: skills-index
description: 用户级 OpenCode skills 总目录与分类管理文档。
---

# OpenCode Skills 总目录

## 一、分类管理

### 域 1 · AI 工程基础设施

**何时进入这个域**：你不是在写业务代码，而是在设计/审计 AI agent 自身的工作环境。

> 暂为空。新装相关 skill 后会自动出现在这里。

### 域 2 · 代码质量与交付闭环

**何时进入这个域**：代码已经写完，进入"提交 / PR / 发布"前的最后一公里。

> 暂为空。新装相关 skill 后会自动出现在这里。

### 域 3 · 桌面应用工程

**何时进入这个域**：跨平台桌面应用 + 用户体感必须像原生。

> 暂为空。新装相关 skill 后会自动出现在这里。

### 域 4 · 创业与产品验证

**何时进入这个域**：手上是点子或早期产品。

> 暂为空。新装相关 skill 后会自动出现在这里。

### 域 5 · 知识产权交付

**何时进入这个域**：项目进入商业化保护阶段。

> 暂为空。新装相关 skill 后会自动出现在这里。

### 域 6 · 工具增强（横切层 · cross-cutting）

**何时进入这个域**：不绑定特定项目类型，但任何项目都可能需要的能力。

> 暂为空。新装相关 skill 后会自动出现在这里。
```

skills-graph.mmd 最小骨架：

```
flowchart LR
    classDef builtin fill:#eeeeee,stroke:#616161,color:#000,stroke-dasharray: 4 2

    %% --- Lifecycle flows ---

    %% --- Cross-domain reinforcements ---
```

`render-mermaid.py`：从老仓库带过来，或新写 —— 见 `~/.config/opencode/skills/render-mermaid.py`（依赖 playwright + chromium）。

---

## 四、Skill 仓库 + Agent 仓库的位置关系

```
~/project/Agent/Agent_skills/         ← 本仓库（管理层）
├── portal/                           ← 移到这里的 portal 源码
├── agent/                            ← AI 编排层
└── .opencode/                        ← OpenCode 自动发现 commands + subagents

~/.config/opencode/skills/            ← skill 仓库本体（被管理对象）
├── INDEX.md                          ← 6 域分类
├── skills-graph.mmd / .png           ← 关系图
├── render-mermaid.py                 ← graph 渲染脚本
└── <skill-name>/                     ← 每个 skill 一个目录
```

⚠️ 关键：**本仓库不替代 skill 仓库**。本仓库只管理 `~/.config/opencode/skills/`。两个目录是独立的，互不嵌套。

---

## 五、连通 OpenCode

OpenCode 自动发现：

- 项目级：进入 `~/project/Agent/Agent_skills/` 后 `.opencode/commands/` 和 `.opencode/agent/` 立即生效
- 验证：在 OpenCode 对话框输 `/skill-` —— 应该看到 11 个命令补全

第一次试：

```
/portal-start
/skill-list
/skill-doctor
```

---

## 六、（可选）portless HTTPS

让 portal 在 `https://skills-portal.localhost` 而不是 `http://localhost:5173`。好处：浏览器把 localhost 当作非安全上下文，很多 API 用不了；portless 提供受信本地 CA，给真 HTTPS。

```bash
# 装 portless（macOS）
brew install portless/tap/portless
portless setup    # 装 CA 到系统 keychain，可能需要 sudo

# 启动 portal 时 bin/start 会自动探测，若 portless 在 PATH 就用它
./portal/bin/start
```

不装 portless 也能用，自动 fallback 到 `http://localhost:5173`。

---

## 七、（macOS 可选）Skills Portal.app launcher

如果你想要 macOS Spotlight/Launchpad 启动 Portal：

```bash
# AppleScript applet
osacompile -o /Applications/Skills\ Portal.app <(cat <<'AS'
set portalURL to "https://skills-portal.localhost"
set startScript to "/Users/$USER/.config/opencode/skills-portal/bin/start"
set isRunning to false
try
    do shell script "pgrep -f 'uvicorn.*5174'"
    set isRunning to true
end try
if isRunning then
    do shell script "open " & quoted form of portalURL
else
    tell application "Terminal"
        activate
        do script startScript
    end tell
    delay 3
    do shell script "open " & quoted form of portalURL
end if
AS
)

# 创建软链接，让 .app 找到 portal/bin/start
ln -s ~/project/Agent/Agent_skills/portal ~/.config/opencode/skills-portal
```

替换 `$USER` 为你的用户名。

---

## 八、验证整个安装

```bash
cd ~/project/Agent/Agent_skills

# 1. portal_client 烟雾测试
portal/backend/.venv/bin/python -m agent.lib.portal_client ensure
portal/backend/.venv/bin/python -m agent.lib.portal_client health
portal/backend/.venv/bin/python -m agent.lib.portal_client list

# 2. 跑测试
portal/backend/.venv/bin/python -m pytest tests/ -q
# 期望：20 passed

# 3. doctor 体检
portal/backend/.venv/bin/python -m agent.lib.doctor all

# 4. 浏览器打开
open http://localhost:5173    # 或 https://skills-portal.localhost
```

如果都过：装好了。可以从 OpenCode 对话用 `/skill-install <github_url>` 装第一个 skill。

---

## 九、常见问题

### Q: ports 5173/5174 被占

```bash
lsof -ti:5173,5174 | xargs kill -9
```

### Q: pytest 报 portal venv missing

确认 `portal/backend/.venv/bin/python` 存在。如果不存在，回到 §二 step 2 重装 venv。

### Q: graph 渲染失败 (mmdc 报错)

`render-mermaid.py` 用 playwright + chromium-1217，不用 mmdc。装 playwright：

```bash
~/Library/Python/3.9/bin/pip install playwright
~/Library/Python/3.9/bin/python -m playwright install chromium
```

### Q: 桌面 launcher.app 启动后立刻退出

检查软链接 `~/.config/opencode/skills-portal` 是否指向真实存在的 `portal/` 目录。

### Q: 我想把 skill 仓库放在别的位置

改 `agent/lib/*.py` 顶部的 `SKILLS_ROOT = ...` 常量 + 改 `portal/backend/build_index.py` 同名常量。**不推荐** —— 整个生态默认假设 `~/.config/opencode/skills/`。

---

## 十、卸载

```bash
# 1. 停 portal
lsof -ti:5173,5174 | xargs kill -9 2>/dev/null

# 2. 删 agent 仓库
rm -rf ~/project/Agent/Agent_skills

# 3. 删反向软链接（如果建过）
rm ~/.config/opencode/skills-portal

# 4. 删 launcher.app（如果建过）
rm -rf /Applications/Skills\ Portal.app

# 5. （可选）删 skill 仓库 —— 注意这会把所有已装的 skill 都删掉
# rm -rf ~/.config/opencode/skills
```
