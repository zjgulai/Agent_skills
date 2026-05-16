---
name: domain-taxonomy
description: 6 个 skill 域的判定规则。给 `agent/lib/domain_inference.py` 当人类可读的真相源。每域列出关键词、定位说明、命中边界。新增域时先改本文，再改代码。
---

# Skill 域分类规则（6 域 · v1）

> 真相源：本文。`domain_inference.py` 的 KEYWORD 表只是本文的代码镜像。
> 改判定规则时：先改本文 → 改代码 → 跑 `test_domain_inference.py` 回归。

---

## 一、域定义

### `meta` · AI 工程基础设施

**何时进入**：任务的对象**就是 AI agent 本身的工作环境**（仓库结构、agent 记忆、skill 库、hook、subagent、plugin、agent 自我治理）。

**强信号关键词**：
- 名词：`agent`, `subagent`, `hook`, `plugin`, `MCP server`, `prompt template`
- 文件 / 配置：`AGENTS.md`, `CLAUDE.md`, `.opencode/`, `~/.config/opencode/`, `opencode.json`
- 行为：`agent directory structure`, `agent guardrails`, `team-wide agent distribution`, `agent self-improvement`

> 注意：`skill` 单字不进 meta 关键词表 —— 太宽泛（几乎所有 SKILL.md 的描述都会出现 "skill"，会污染分类）。`subagent` / `agent` / 文件配置项才是 meta 的强信号。

**反信号**（命中以下→**不要**归 meta）：业务代码、UI 实现、第三方库使用。

---

### `closeout` · 代码质量与交付闭环

**何时进入**：代码已经写完，进入"提交 / PR / 发布 / 上线"前的最后一公里。

**强信号关键词**：
- 行为：`review`, `code review`, `commit`, `pull request`, `PR`, `merge`, `release`, `ship`, `lint`, `audit`
- 工具：`codex review`, `git rebase`, `cherry-pick`, `changelog`, `semver`
- 阶段：`pre-commit`, `pre-push`, `pre-merge`, `before ship`, `before release`

**反信号**：写新功能、设计架构、找 bug 原因（这是 build / debug，不是 closeout）。

---

### `desktop` · 桌面应用工程

**何时进入**：跨平台桌面应用 + **用户体感必须像原生**。

**强信号关键词**：
- 平台 / 框架：`Tauri`, `Electron`, `WebView`, `WebView2`, `WKWebView`, `WebKit`, `native macOS`, `Windows native`
- 主题：`launcher app`, `system tray app`, `global hotkey`, `window manager`, `Raycast`, `Spotlight`
- 性能 / 体感：`native feel`, `cold start`, `instant launch`, `liquid glass`, `vibrancy`, `Mica material`

**反信号**：纯 Web 应用、纯 mobile（iOS only / Android only）、CLI / TUI 工具。

---

### `founder` · 创业与产品验证

**何时进入**：手上是**点子或早期产品**，在写代码前判断"这事值不值得做 / 怎么做"。

**强信号关键词**：
- 框架 / 概念：`MVP`, `ICP`, `pressure-test`, `validate problem`, `market fit`, `founder-market fit`, `PMF`
- 行动：`first 10 customers`, `pivot`, `launch plan`, `landing page test`, `cold outreach`
- 阶段：`pre-seed`, `idea stage`, `pre-revenue`, `2-week launch`

**反信号**：已上线产品的运营优化（那是 growth / ops，不是 founder validation）。

---

### `ip` · 知识产权交付

**何时进入**：项目进入**商业化保护阶段**，把代码资产变成可申报的法律文件。

**强信号关键词**：
- 中文：`专利`, `软著`, `软件著作权`, `技术交底书`, `国知局`, `知识产权`
- 英文：`patent`, `patent disclosure`, `copyright`, `software copyright`, `prior art search`, `claim drafting`
- 形态：`.docx` 申请书、操作手册、源代码材料

**反信号**：技术文档、API 文档、内部 wiki（那是文档，不是 IP）。

---

### `tooling` · 工具增强（横切层）

**何时进入**：不绑定特定项目类型，**任何项目都可能需要**的工具能力。

**强信号关键词**：
- 文档 / 制作物：`PPT`, `slide deck`, `presentation`, `magazine`, `swiss style`, `cover`, `social cover`
- 媒体 / 图像：`image prompt`, `image generation`, `screenshot`, `cover art`, `editorial layout`
- 文件格式：`docx`, `pdf`, `markdown`, `xlsx`, `pptx`, `html`
- 通用工具：`git workflow`, `i18n`, `markdown lint`, `font management`

**反信号**：业务逻辑、平台特定（那应该是某个具体域）。

---

### `uncategorized` · 兜底

**何时进入**：上面 6 域都没命中（多域评分都是 0），需要人工 `/skill-classify`。

---

## 二、判定算法

```
1. 把 skill 的 name + description 转小写，记作 text
2. 对每个 domain，统计 keywords 在 text 中的出现次数（每个关键词只计一次，避免重复词刷分）
3. 取得分最高的 domain
4. 若最高分为 0 → uncategorized
5. 若最高分有平局 → 按域优先级（见下）取第一个
6. 输出 domain_id + 命中证据（哪些关键词触发了）
```

**域优先级**（仅当评分平局时启用，从高到低）：
1. `ip` — IP 关键词通常很明确，平局时 IP 是更稳的猜测
2. `desktop` — 桌面关键词足够特定
3. `founder` — 早期项目标志明显
4. `meta` — meta-engineering 关键词识别度高
5. `closeout` — closeout 关键词容易和 meta 混
6. `tooling` — 最通用，作为最后兜底（高于 uncategorized）

---

## 三、典型案例（用作回归测试）

| Skill name | description 关键词 | 期望 domain | 关键证据 |
|---|---|---|---|
| `agent-dev-kit-architecture-designer` | `CLAUDE.md, skills, hooks, subagents, plugins, agent directory structure` | meta | agent / skill / hook / subagent / plugin |
| `codex-review` | `codex review, 二次审查, 提交前审查, ship/commit/PR` | closeout | codex review / ship / commit / PR |
| `native-feel-cross-platform-desktop` | `Tauri vs native, WebView wrapper, Raycast architecture, WKWebView, system tray app` | desktop | Tauri / WebView / Raycast / WKWebView / system tray |
| `startup-pressure-test` | `validate problem, ICP, MVP, 2-week launch plan, founder-market fit` | founder | ICP / MVP / founder-market fit |
| `patent-disclosure-skill` | `专利挖掘, 交底书, 国知局查新` | ip | 专利 / 交底书 / 国知局 |
| `software-copyright-materials` | `软件著作权, 软著申请资料, 操作手册` | ip | 软件著作权 / 软著 |
| `guizang-ppt-skill` | `polished HTML slide decks, image prompts, social covers` | tooling | slide deck / image prompts / cover |

> 准确率指标：≥ 6/7 = 85.7% （回归集合）。
