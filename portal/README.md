# Skills Portal

本地部署的 OpenCode skills 管理网站。把 `~/.config/opencode/skills/` 下的 skill 仓库管理可视化：分类展示、关联图谱、一键安装/卸载。

## 截图

| 页面 | 文件 |
|---|---|
| 首页（域分组卡片 + Skills Graph） | [`docs/screenshot-home.png`](docs/screenshot-home.png) |
| Skill 详情（内嵌 SKILL.md 渲染 + 卸载按钮） | [`docs/screenshot-detail.png`](docs/screenshot-detail.png) |
| 一键安装对话框（GitHub URL 或 上传 .md） | [`docs/screenshot-install.png`](docs/screenshot-install.png) |
| Portless HTTPS 部署 (`https://skills-portal.localhost`) | [`docs/screenshot-portless-https.png`](docs/screenshot-portless-https.png) |

## 启动

```bash
~/.config/opencode/skills-portal/bin/start
```

启动后（**优先 portless HTTPS，自动 fallback 到端口模式**）：

| 工具链 | URL |
|---|---|
| **portless 已装**（推荐）| `https://skills-portal.localhost` |
| API 健康检查 | `https://skills-portal.localhost/api/health` |
| OpenAPI 文档 | `https://skills-portal.localhost/api/docs` |
| **portless 没装** | `http://localhost:5173` |
| 等价 API | `http://localhost:5174/api/health` |

`Ctrl+C` 同时停 vite + uvicorn + portless route 自动清除。

### portless 集成说明

`bin/start` 会探测 `portless` 命令是否存在：

- **存在** → 用 `portless run --name skills-portal --app-port 5173 -- npm run dev` 包裹 Vite。所有流量从 `https://skills-portal.localhost`（443）进，由 portless 终结 TLS 后转给 5173；前端继续用 vite 自身的 `/api → 5174` proxy 把 API 路径转给 uvicorn。**整个 portal 只对外一个 hostname**。
- **不存在** → 退回纯端口模式 `http://localhost:5173` + `http://localhost:5174`。

为什么这样接：

| 问题 | portless 之前 | portless 之后 |
|---|---|---|
| 浏览器地址 | `localhost:5173` 容易和别的项目冲突 | `skills-portal.localhost` 稳定可记 |
| HTTPS | 没有，很多浏览器 API（clipboard、SecureContext-only）受限 | 系统受信本地 CA，真 HTTPS |
| Cookie / localStorage 隔离 | 所有 localhost 项目共享 | 每个 `*.localhost` 独立 origin |
| API 文档暴露 | 必须记 `:5174/docs` | 同 hostname 下 `/api/docs` |

`docs_url` 已改成 `/api/docs`，让 OpenAPI swagger UI 也能通过 vite 反代到 portless。

## 架构

```
skills-portal/
├── bin/start                   # 一键并起脚本
├── backend/                    # FastAPI + Python 3.9 venv
│   ├── .venv/                  # 隔离运行时（不污染全局 ~/Library/Python/3.9）
│   ├── app.py                  # HTTP routes
│   ├── installer.py            # git clone / upload → 探测 SKILL.md → 校验 → 拷贝
│   ├── build_index.py          # 扫 skills/ → data/skills-data.json
│   └── data/skills-data.json   # 预烘数据（启动时刷新；安装/卸载后增量重建）
└── frontend/                   # Vite + Vue 3 + TS + Pico CSS
    ├── vite.config.ts          # /api → 5174 反代
    └── src/
        ├── App.vue             # 主框架（搜索 + Graph + 卡片网格）
        ├── api.ts              # fetch 封装
        ├── types.ts            # SkillsData / Skill / Domain
        └── components/
            ├── TopBar.vue
            ├── DomainSection.vue   # 一个域 = 一组卡片
            ├── SkillCard.vue       # 卡片：name + desc + 触发词 chips
            ├── SkillDetail.vue     # 弹窗：marked 渲染 SKILL.md + 卸载按钮
            ├── GraphView.vue       # mermaid 内嵌渲染（CDN 不参与）
            ├── InstallDialog.vue   # GitHub URL / 上传 .md 双 tab
            └── ToastList.vue       # 操作反馈
```

## 数据流

```
~/.config/opencode/skills/*/SKILL.md
~/.config/opencode/skills/INDEX.md         (分类来源)
~/.config/opencode/skills/skills-graph.mmd  (graph 来源)
        │
        ▼
backend/build_index.py
        │
        ▼
backend/data/skills-data.json   ◄── GET /api/skills
                                ◄── DELETE /api/skills/{name}
                                ◄── POST /api/install/github
                                ◄── POST /api/install/upload
                                ◄── POST /api/refresh
        │
        ▼
frontend (Vue 3)
        │
        ▼
浏览器 http://localhost:5173
```

## API

| Method | Path | 用途 | Body |
|---|---|---|---|
| `GET` | `/api/health` | 健康检查 | — |
| `GET` | `/api/skills` | 完整 skills-data.json | — |
| `GET` | `/api/skills/{name}` | 单个 skill 的 frontmatter | — |
| `GET` | `/api/skills/{name}/markdown` | SKILL.md 原文 | — |
| `POST` | `/api/install/github` | 从 GitHub 安装 | `{url, subdir?}` |
| `POST` | `/api/install/upload` | 上传 SKILL.md | multipart `file` |
| `DELETE` | `/api/skills/{name}` | 卸载 | — |
| `POST` | `/api/refresh` | 重跑 build_index | — |

完整 OpenAPI 文档：http://localhost:5174/docs

## 一键安装策略（installer.py）

GitHub URL：

1. `git clone --depth 1` 到 `/tmp/skills-portal-clone/<uuid>`
2. SKILL.md 探测（深度 ≤ 2）：
   - 先 `<repo>/SKILL.md`
   - 否则递归找子目录第一层的 `<repo>/<subdir>/SKILL.md`
   - 多个候选 → 报错并要求 `subdir` 参数
3. 严格校验 frontmatter：
   - 必须有 `name` + `description`
   - `name` 通过 `^[a-z0-9]+(-[a-z0-9]+)*$` + 长度 1..64
   - `description` 长度 1..1024
4. 拷贝到 `~/.config/opencode/skills/<name>/`，跳过 `.git` / `LICENSE` / `README.md` / `.gitignore` / `package.json`
5. 重跑 build_index 增量更新 JSON

本地上传 SKILL.md：

- 自动剥除 ` ```markdown ... ``` ` 包裹（之前 Downloads/SKILL.md 的坑）
- 同样的 frontmatter 校验
- 装到 `<name>/SKILL.md`（无 resources 的最简 skill）

## 扩展指南

### 加一个新域

编辑 [`build_index.py`](backend/build_index.py) 的 `DOMAIN_DEFAULTS` 和 `DOMAIN_LABEL_TO_ID`，对应再去 `INDEX.md` 加一个 `### 域 N · 新域名` 段落。

### 改 graph 显示

源码在 `skills-graph.mmd`。GraphView.vue 直接读后端送来的 `mermaid_source` 字段，不需要前端改。

### 接入"调用 skill 上下文"

v1 没做。建议方向：

- 给每个 skill 卡片加 `复制 load_skills` 按钮 → 复制 `task(load_skills=["xxx"], ...)` 模板
- 或加 `选中`/`组合` 模式 → 选若干 skill → 一键复制套餐

## 已知局限 / v1 不做

- **没有鉴权**：仅本机 127.0.0.1，不要绑 0.0.0.0 暴露到局域网
- **没有 SSE/WebSocket**：安装大仓库时前端等待，无进度条
- **触发词抽取较弱**：只抓 description 里的反引号、双引号、中文角括号；其他描述呈现为长段落（v2 可加 NLP 提取）
- **多 skill 仓库批量安装**：需要先用 `subdir` 一个一个装；v2 可加"列出仓库内所有 SKILL.md → 多选安装"
- **覆盖确认**：当前是直接覆盖（仅在 warnings 里提示）。v2 应改成"探测到已存在 → 前端二次确认"

## 维护

```bash
# 强制重建索引
curl -X POST http://localhost:5174/api/refresh

# 手动重建（不通过 API）
~/.config/opencode/skills-portal/backend/.venv/bin/python \
  ~/.config/opencode/skills-portal/backend/build_index.py

# 查看后端日志
tail -f /tmp/portal-uvicorn.log    # 仅当用脚本启动时

# 重新构建 frontend production bundle（不是必需，dev 模式够用）
cd ~/.config/opencode/skills-portal/frontend && npm run build
```

## 端口冲突

`bin/start` 启动前会检查 5173 / 5174 是否被占用。手工排查：

```bash
lsof -ti:5173,5174
# 杀掉
lsof -ti:5173,5174 | xargs kill -9
```

## 第三方依赖

| 层 | 包 | 用途 |
|---|---|---|
| Backend | fastapi, uvicorn[standard], pyyaml, python-multipart, httpx | HTTP API + frontmatter 解析 + 文件上传 |
| Frontend | vue@3.5, vue-router@4, marked@15, mermaid@11, @picocss/pico@2 | UI + markdown 渲染 + graph 渲染 + 极简 CSS |
| 系统 | git CLI | 一键安装时 clone GitHub 仓库 |
