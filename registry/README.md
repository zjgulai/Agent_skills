# Agent_skills · registry/

> Skill 注册表（与 Agent_hook、Agent_mcp 同源 schema）

## 与现有 skills 仓的关系

**重要**：Skill **本体** 仍然住在 `~/.config/opencode/skills/<name>/`（受 [Agent_skills/AGENTS.md](../AGENTS.md) 硬约束保护，本仓不动其文件结构）。

`registry/<name>/manifest.yaml` 在本仓是**索引和元数据**，`source` 字段指向真实位置：

```yaml
kind: skill
name: frontend-design
source:
  type: external
  path: ~/.config/opencode/skills/frontend-design   # 已在 OpenCode 用户级 skill 目录
  upstream: https://github.com/anthropics/skills
```

或者对于"本仓自有"的 skill（少数）：

```yaml
source:
  type: local
  path: registry/<name>/source/
```

## 与 portal 的关系

**portal/ 是 P0 之前已有的成熟管理面板**，它读 `~/.config/opencode/skills/INDEX.md` 作为真相源。

P0.3 阶段 registry/ 的引入**不影响 portal 现有逻辑**。Phase 6 时合并三仓 portal，那时再让 portal 改用 registry/manifest.yaml 作为元数据来源。

## P3.1~P3.2 阶段会注册的 12 个 skill

来自 [全局 TODO](../.sisyphus/plans/02-execution-todo.md)：

- 已存在 8 个老 skill（agent-dev-kit-architecture-designer, codex-review, guizang-ppt-skill, native-feel-cross-platform-desktop, patent-disclosure-skill, skill-creator, software-copyright-materials, startup-pressure-test）→ P3.2 加 manifest 引用
- 新增 4 个 P0 skill（frontend-design, superpowers, code-review, create-pr）→ P3.1 拉源 + manifest
