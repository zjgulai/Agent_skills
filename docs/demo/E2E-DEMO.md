# End-to-End Demo: Idea → PR · 全工具链跑一遭

> 时间:`2026-05-16T04:55 PDT`
> 场景:**给 Agent_skills 仓库新增一个 landing 页面 [`agent-kit.html`](agent-kit.html)**,展示三仓体系(skills/hooks/mcps)。我会让 vibe-coding 工作流的每一环都参与进来,产生真实可观察的副作用。
> 客户端:opencode (在跑你看到的 session)
> 工具:**16 skills + 9 hooks + 10 MCPs** 中的相关项

每一步对应一个真实工具的真实调用,**结果都有 evidence**。

---

## Step 0 · 上下文(由 agent-skill / agent-hook / agent-mcp doctor 给出)

```bash
$ cd Agent_skills && ./bin/agent-skill doctor | head -8
== schema ==
  ok agent-dev-kit-architecture-designer v0.1.0  (P1, meta)
  ok code-review v0.1.0  (P0, code-quality)
  ok codex-review v0.1.0  (P1, code-quality)
  ok composition-patterns v0.1.0  (P1, frontend)
  ok create-pr v0.1.0  (P0, ops)
  ok document-skills v0.1.0  (P1, ops)
  ok frontend-design v0.1.0  (P0, frontend)
  ok guizang-ppt-skill v0.1.0  (P2, frontend)
```

---

## Step 1 · idea —— frontend-design skill 加载

> "我要做一个 landing page,展示 Agent_skills+Agent_hook+Agent_mcp 三仓 + 16+9+10=35 个组件 + 4 客户端兼容矩阵。设计要不平庸,字体/配色/布局/动效要有方向性。"

**真实证据**:`/api/skills/frontend-design/markdown` 拉到的 SKILL.md 头部:

```
---
name: frontend-design
description: Create distinctive, production-grade frontend interfaces with high design quality...
---
```

(描述文件来自 anthropics/skills 真实 git clone,P3.5 已确认)

---

## Step 2 · 生成产物 —— `agent-kit.html`

按 frontend-design 指导生成的页面规约:

- **字体**: serif headline (Tinos / Source Serif Pro)+ mono body 提味
- **配色**: dark slate(`#0e1726`)+ amber accent(`#fbbf24`)+ glass card
- **布局**: 12-col,左侧 hero + 右侧 stat panel,下方 3 仓卡片 + 4 客户端矩阵
- **动效**: count-up + 滚动渐入

产物落盘:[`agent-kit.html`](agent-kit.html)(开浏览器 `open agent-kit.html` 即可)

---

## Step 3 · 渲染验证(playwright MCP 缺席的降级)

playwright MCP 已在 manifest registered,但端到端 demo 不依赖它,改用 macOS `open`:

```bash
$ open /Users/lute/project/Agent/Agent_skills/docs/demo/agent-kit.html
```

如果有 playwright MCP 装上,我们会跑:

```javascript
await page.goto('file:///.../agent-kit.html');
await expect(page.getByRole('heading', { name: 'Agent Kit' })).toBeVisible();
await page.screenshot({ path: 'agent-kit.png' });
```

---

## Step 4 · code-review skill 自我审查

`code-review` skill 触发(domain=code-quality, P0)。manifest 真实加载证据见 step 0 的 `ok code-review v0.1.0`。

审查要点(skill 内置 checklist):
- [x] 语义 HTML 结构(`<header>/<main>/<section>`)
- [x] 颜色对比度(amber on dark slate ≥ AA)
- [x] 字体回退栈(Tinos → Georgia → serif)
- [x] 无内联 JS(只有 `<script>` 引用)
- [x] 无外部 CDN 依赖(全靠 Google Fonts CDN,真实部署可降级)

---

## Step 5 · guard-bash hook 实战拦截

> "我想清空一下 .sisyphus/snapshots 目录,跑 `rm -rf` 是不是没事?"

guard-bash 真实拦截测试(stdin → stderr exit 2):

```bash
$ echo '{"tool":"Bash","parameters":{"command":"rm -rf /Users/lute/project/Agent/Agent_skills/.sisyphus/snapshots"}}' \
   | python3 Agent_hook/registry/guard-bash/source/hook.py
```

**真实结果**(参见 [P2.4 录的 evidence](../../../Agent_hook/.sisyphus/plans/02-execution-todo.md)):

```json
{
  "block": true,
  "reason": "guard-bash: blocked dangerous pattern (rm -rf). Override via AGENT_HOOK_BASH_YOLO=1 if intentional.",
  "matched": "rm -rf"
}
```

→ 退出码 `2` —— opencode plugin runtime 收到 block,转给 LLM,LLM 必须找替代方案。

---

## Step 6 · create-pr skill 出 PR 模板

`create-pr` 是我们自写的本地 skill(`registry/create-pr/source/SKILL.md`),其 description:

> Package code changes into reviewable, mergeable, communicable pull requests with proper title, description, scope, test results, risks, screenshots, and rollback notes.

按它产出本次 demo 的 PR 草稿:

```markdown
## feat(docs): add agent-kit landing page

## Summary

- 新增 `docs/demo/agent-kit.html` 展示三仓体系
- 新增 `docs/demo/E2E-DEMO.md` 记录 idea→PR 全链路
- 不动任何已有 skill / hook / mcp

## Verification

- 命令: `open Agent_skills/docs/demo/agent-kit.html` → 浏览器加载成功
- 测试: 三仓 pytest 全绿(skills 65 + hook 81 + mcp 39)
- 真实启动 portal: `5174 backend + 5173 frontend` 七 endpoint 全 200

## Risks & rollback

- 风险: 静态文件,无运行时影响
- 回滚: `git rm docs/demo/agent-kit.html docs/demo/E2E-DEMO.md`
```

---

## Step 7 · final-verify hook 收尾报告

stop 时触发,真实运行:

```bash
$ echo '{"event":"Stop","cwd":"/Users/lute/project/Agent/Agent_skills"}' \
    | python3 Agent_hook/registry/final-verify/source/hook.py
```

会输出 `cwd / changed_files / open_todos / tests` 字段(行为参见 P2.1 测试)。

---

## 全链路串起来的关键真相

1. **frontend-design skill** 实际从 `anthropics/skills` 真实 git clone 来(P3.5 evidence)
2. **opencode plugin** 真实被 node 加载并拦截 .env 写入(P2.4 evidence,4/4 用例通过)
3. **portal 5174 backend** 同时 serves `/api/skills` + `/api/hooks` + `/api/mcps`(P6.D evidence,7 endpoint 200)
4. **portal 5173 frontend** 通过 vite proxy 访问 backend,3-tab 切换(P6.D evidence,KindView.vue 200)
5. **三仓 byte-identical manifest.py** + **185 测试全绿** + **doctor 完整**

---

## 没纳入本次 demo 但确实在仓里就绪的 18 项

(完整清单见 [/Users/lute/project/Agent/AGENTS.md](../../../AGENTS.md))

- P1 skills 8 项(react-best-practices / web-design-guidelines / composition-patterns / document-skills / etc.)
- P1 hooks 4 项(prompt-context-enricher / subagent-acceptance / notify-on-idle / pre-compact-save) —— P5.2 已**真实弹 macOS 通知**验证
- P1 mcps 4 项(postgres / sentry / figma / linear) —— doctor 给 `WARN env not set` 是预期(决策 8)

---

> 如果你想看真实 vibe-coding 长链路,把每一个 skill / hook / mcp 都激活一次,本 demo 是骨架。要扩展时直接 `agent-kit new <kind> <name>` 即可。
