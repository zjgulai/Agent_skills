---
description: Given a task description, recommend a load_skills=[...] combination from installed skills.
agent: build
---

# /skill-recommend

Recommend which skill combination to load for a user's described task.

**Arguments**: `$ARGUMENTS` — natural-language task description (e.g., "我要做一份瑞士风 PPT" or "PR ship 前的最后检查").

## Execute

### Step 1 — Get full skill catalog

```bash
portal/backend/.venv/bin/python -m agent.lib.portal_client list
```

### Step 2 — Read INDEX.md "典型场景套餐表" (section 三 in INDEX.md)

This table maps common scenarios to recommended `load_skills=[...]` combos. Use it as the **first lookup**.

```bash
sed -n '/^## 三、典型场景套餐/,/^## /p' ~/.config/opencode/skills/INDEX.md
```

### Step 3 — Decide

Match the user's `$ARGUMENTS` against the scenario table. If a row matches semantically, use that combo as your recommendation.

If nothing matches, fall back to keyword inference:
- Match the user's task against each skill's description + triggers
- Score each skill (count of matching keyword phrases)
- Recommend the top 1-3 highest-scoring skills

### Step 4 — Output

Format:

```
任务："<user's task>"

推荐组合（按优先级）：
  load_skills=["<skill1>", "<skill2>"]

理由：
  • <skill1>: <one-line why this is relevant>
  • <skill2>: <one-line why this is relevant>

可直接复制：
  task(category="...", load_skills=["<skill1>", "<skill2>"], prompt="...", run_in_background=false)
```

If matching the table directly:
```
任务："<user's task>" → 命中 INDEX 套餐: 「<场景名>」

直接套用：
  load_skills=<原 INDEX 推荐组合>
```

If the user's task doesn't match any scenario AND scoring returns 0 skills:
```
没有找到匹配 skill。建议：
  1. 这个任务可能不需要专门 skill — OpenCode 内置能力足够
  2. 或考虑装新 skill（/skill-install）覆盖这个领域
```

Read-only. No writes.
