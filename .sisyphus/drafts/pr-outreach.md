# PR drafts · OpenCode ecosystem outreach

> 给 user 的 PR 草稿合集。我**不会**自动提交任何 PR——这些是给你审完后手动 push 的。
> Librarian 任务（bg_356d719b）会补全具体目标仓库 + 行号 + 格式参考。

---

## 通用 PR 模版

### 标题候选（按风格挑一个）

- **务实**：`Add: Skills Manager AI Agent (lifecycle layer for installed skills)`
- **简短**：`Add Skills Manager AI Agent`
- **特点导向**：`Add Agent_skills — auto-install/classify/graph/doctor for OpenCode skills`

### 通用 PR body（适合"awesome-list 风格"目标）

```markdown
Adds [Skills Manager AI Agent](https://github.com/zjgulai/Agent_skills) — an OpenCode skills lifecycle layer.

If you have 3+ skills installed in `~/.config/opencode/skills/`, this gives you 11 slash commands covering install / uninstall / update / classify / doctor / recommend / graph-sync / portal-control.

**Highlights:**
- One-command install: `/skill-install <github_url>` runs end-to-end in ~30s (clone → infer 6-domain classification → update INDEX.md → add graph node → re-render PNG → refresh portal)
- 5-rule health check across every installed skill via `/skill-doctor`
- Task-to-skills recommendation: free-form description → `load_skills=[...]` suggestion
- Local FastAPI + Vue portal (UI on :5173, REST on :5174)
- Bilingual docs (EN + 中文) at https://zjgulai.github.io/Agent_skills/handbook.html
- v1.0.0 released, MIT licensed

End-to-end verified by installing two real skills:
- `op7418/guizang-ppt-skill` (auto-classified into `tooling`)
- `anthropics/skills/skills/skill-creator` (uncategorized → manual classify into `meta`)

Both passed all 5 doctor rules; graph rendered correctly through both transitions.

Online handbook: https://zjgulai.github.io/Agent_skills/handbook.html
```

### 短版（适合"在表格里加一行"的目标）

```markdown
| [Agent_skills](https://github.com/zjgulai/Agent_skills) | OpenCode skills lifecycle manager: 11 commands for install/classify/graph/doctor backed by a local FastAPI+Vue portal | MIT |
```

或：

```markdown
- [zjgulai/Agent_skills](https://github.com/zjgulai/Agent_skills) — Skills lifecycle layer for OpenCode (install / classify / graph / doctor / recommend, 11 slash commands).
```

---

## 通用注意事项

### 写 PR 描述时

- **不要**说大话（"the best ..."），就说功能
- **要**说"verified" 和 "v1.0 released"——证明可用
- **要**有 bilingual 提示——OpenCode 早期用户多在 EN + ZH 圈
- **不要**贴你的 Twitter / 个人页面（与社区无关）
- **要**贴 site 链接 + repo 链接，**不要**贴 raw 文件链接

### PR 礼仪

- 先看目标仓库**最近 5 个 PR**——他们怎么写，跟着学
- 如果有 CONTRIBUTING.md，照做
- 用 squashed commit 写好 commit message
- 不要在多个仓库同时投——一个一个来
- 被拒了不解释，关闭即可

### 不投的红灯

- 仓库 last commit > 60 天 → 大概率没人 review
- 维护者最近 PR 都没回 → 同上
- PR description 模版里有"don't add personal projects" → 听话

---

## 待 librarian 补全（bg_356d719b）

需要把以下空白填上后才能用：

| 仓库 | section | 现有 entry 样本 | confidence |
|---|---|---|---|
| _待填_ | _待填_ | _待填_ | _待填_ |

---

## 备选：不发 PR 的推广路径

如果 PR 不合适，还有这些：

1. **GitHub Discussions** — 在 anomalyco/opencode 的 Discussions 里发一帖 "Share what you built" 类型
2. **OpenCode Discord** — 如果有官方 Discord（待查）
3. **Hacker News Show HN** — 周末发，写好"Why I built this"
4. **小红书 / X / Mastodon** — 中文圈用小红书，英文圈用 X
5. **Reddit r/LocalLLaMA** 或 r/ClaudeAI — 视具体定位
6. **写一篇 dev.to / Medium 长文** ——介绍"我怎么用 OpenCode 管理 8 个 skills"

> 我的建议：先 PR 1-2 个高质量目标试水，**同时**写一篇 dev.to 长文（你自己读起来都觉得有故事），两条腿走路。
