# Agent_skills · adapters/

四客户端 Skill 适配器（**符号链接为主**，按决策 1）。

## 分发原则

每个客户端的 skill 发现路径：

| 客户端 | 发现路径 | 适配方式 |
|---|---|---|
| opencode | `~/.config/opencode/skills/<name>/` | `ln -s` 指向 source.path |
| codex | `~/.codex/skills/<name>/`（避开 `.system/`） | `ln -s` |
| cursor | `~/.cursor/skills-cursor/<name>/` | `ln -s` |
| kimi | `~/.kimi/config.toml` 的 `extra_skill_dirs` 数组 | 写配置（不用 `ln -s`，因为 kimi 支持目录数组） |

## kimi 特殊处理

kimi 的 `extra_skill_dirs = []` 接受目录数组。我们把 `Agent_skills/registry/*/source/`（或它们 link 出去的目标）拼成一个父目录加进去。一次配置即可让 kimi 看见所有 skill。

## 危险性

- `ln -s` 可逆但需小心：删错 link 不会删源；删源会让所有 link 变僵尸。
- 卸载时只删 link，不删 source。
- doctor 命令检查孤儿 link（指向不存在的 source）。

## 实现

`agent/lib/adapter_skill_*.py`（P3.3 阶段）。
