---
name: handbook-and-i18n
description: 新增 handbook.html 主参考页（合并 commands+domains+case-study 三页），全站加 EN/ZH 切换默认 EN，Skills graph 多实例动态展示。详尽的查询手册定位。i18n best-practices 等 librarian 结果到位后 finalize 策略选择。
---

# Skills Manager 站点 v2 · Handbook + i18n 计划（草稿）

> **状态**: i18n best-practices librarian 任务（bg_f297f50c）仍在跑。i18n 实施策略将在收到结果后 finalize。

---

## 一、用户决策（已锁定）

| 项 | 答 |
|---|---|
| 页面策略 | **B**: 合并 commands + domains + case-study 三页 → 1 个 handbook.html。6 → 4 页：Hero / Getting Started / **Handbook** / Architecture |
| i18n 范围 | 全站都加 EN/ZH 切换，**默认 EN** |
| Graph 呈现 | 多个 graph 实例（动态） — Mermaid 内嵌渲染 |
| Handbook 详度 | 详尽 — 11 命令 + 6 域 + 多 graph 实例，全页长 4-5× 首页 |

---

## 二、调查发现（来自 2 个 explore agent）

### 2.1 i18n 当前状态（bg_075a8cd6）

- 6 文件全部 `<html lang="zh-CN">` 但内容 **99.2% 英文**
- 只有 **87 个中文字符** 全在 3 文件：
  - `domains.html` 64 字 — **10 个域名/标签**（真 UI 内容）
  - `commands.html` 16 字 — `<code>` 内系统字面量（`> 暂为空` / "典型场景套餐表"）
  - `case-study.html` 7 字 — 同样系统字面量
- Mermaid 图全英文，无双语化负担
- **零现有 i18n 机制** — 没 data-i18n / hreflang / 切换按钮
- agent 推荐：**JS string-table swap**（最低维护成本）

### 2.2 Graph + 内容资产（bg_75f59b64）

**可直接复用**:
- `skills-graph.mmd`（65 行）— 节点命名 SHORT_ID 风格、edge 三种风格（solid/dashed/double）、6 域 classDef 颜色、5 builtin 节点
- `domain-taxonomy.md` — 6 域 + 推断算法 + 7 用例回归表
- 11 个 `.opencode/commands/*.md` — 已有逐命令一行 summary
- 5 张 portal 截图（已在 docs/assets/screenshots/）

**关键缺口**（必须新做）:
1. **Graph 历史状态 PNG** — 当前只有"最终态"PNG，需要重渲 2 个历史态：
   - State 0: 6 节点（pre-both）
   - State 1: 7 节点（含 GPS，pre-skill-creator）
   - State 2: 8 节点（current）
2. **典型场景套餐表** — 在 INDEX.md `## 三、典型场景套餐` 段落，但该文件是 **binary/encoded**（agent 读不出来）。**需要从 portal 跑读取**或从 `skill-recommend.md` Step 2 反推内容
3. **Graph legend** — .mmd 有边标签但没图例（dashed / solid / double 含义）
4. **11 命令的 ZH 翻译** — 命令 `.md` 文件全 EN，需要 ZH 翻译填入 i18n 字典

> 关于 INDEX.md "binary" 的疑问：~~我之前明明写过它（atomic write 测试通过），它**不是 binary**。~~ **已亲自验证 — INDEX.md 完全可读**。agent 误判的原因：`file` 命令把 macOS APFS dead-bytes-past-EOF 误识别为 data（这是我们之前发现的 APFS bug 重现）。Python `read_text` 正常读取 11932 字符。已提取关键内容块：
> - `/tmp/scenario-bundles.md` — 典型场景套餐表（6 行）
> - `/tmp/six-domains.md` — 6 域分类（6071 字符，全部完整）
> - `/tmp/index-changelog.md` — 维护变更日志
> - `/tmp/index-mermaid.mmd` — INDEX.md 内嵌的 mermaid graph（与独立的 skills-graph.mmd 是另一份，略简）

---

## 三、目标 IA（信息架构）

```
zjgulai.github.io/Agent_skills/
├── /                    Hero (语言切换器，默认 EN)
├── /getting-started     10 分钟安装（保留）
├── /handbook            ★ 新页 = 主参考（合并 3 页）
└── /architecture        架构（保留）
```

被合并删除：
- ~~commands.html~~ → handbook §3
- ~~domains.html~~ → handbook §2
- ~~case-study.html~~ → handbook §5

> ⚠️ 被删页面 URL **设 redirect**（用 `<meta http-equiv="refresh">` 单行 HTML 文件）防止外链 404

---

## 四、Handbook 页面骨架（详尽版）

```
docs/handbook.html

§1. Overview / 概览
   - 一句话定位：The single reference for the OpenCode skills lifecycle.
   - 跳转目录（in-page TOC, sticky right rail）

§2. Domain Taxonomy / 域分类
   - 6 域定义卡片（关键词 + 反信号 + 触发条件）
   - 推断算法 4 步
   - 优先级 tiebreak 链
   - 7 例回归测试表
   - 链接 → agent/docs/domain-taxonomy.md

§3. The 11 Methods / 11 个方法
   - Phase 1: Skill Lifecycle (install / uninstall / update) — 3 cards
   - Phase 2: Inspection (list / recommend / doctor) — 3 cards
   - Phase 3: Maintenance (classify / graph-sync) — 2 cards
   - Phase 4: Portal Control (start / stop / status) — 3 cards
   - 每命令: 一行 EN/ZH summary, 触发例, 影响（read/write/lifecycle badge）

§4. Skills Graph / 技能图谱
   - §4.1 How to read the graph（图例 — solid / dashed / double / classDef colors / SHORT_ID 命名）
   - §4.2 Live current graph（mermaid 内嵌渲染 from skills-graph.mmd 源码）
   - §4.3 Typical scenario bundles（从 INDEX.md 第三节提取）

§5. Graph Case Studies / 图演化案例
   - §5.1 Initial state（6 nodes 渲染）
   - §5.2 Case A: install guizang-ppt-skill → 7 nodes（mermaid 渲染 + 解释 GPS 节点出现 + 工具增强 classDef 自动创建）
   - §5.3 Case B: install skill-creator → 8 nodes（mermaid 渲染 + 解释 SC 出现 + meta 域同域边）
   - §5.4 Hypothetical: 装 3 个 desktop-domain skill 会发生什么（mermaid 渲染）

§6. Cross-references / 索引
   - 链接 architecture.html、getting-started.html、源码仓
```

---

## 五、i18n 实施策略（已锁定 · 来自 librarian bg_f297f50c）

**策略**：**Strategy B 的变体 — `data-i18n` 属性 + 内联 JS object（不 fetch JSON）**

### 选型理由

librarian 评估了 4 个策略：

| | A 平行目录 | **B 内联 data-i18n** | C URL param | D 双 .html |
|---|---|---|---|---|
| 7 页 → 14 文件 | ❌ | ✅ 1 套 | ✅ 1 套 | ❌ |
| Mermaid 双语 | ✅ 简单 | ⚠️ 不需要（label 全 EN） | ⚠️ 同 B | ✅ |
| SEO CN 索引 | ✅ 最好 | ❌ | ❌ | ✅ |
| 0 build | ✅ | ✅ | ✅ | ✅ |
| localStorage 持久化 | URL = 持久化 | ✅ | ⚠️ | ✅ |
| **总维护成本** | **最高** | **最低** | 最低 | 最高 |

**关键判断**：
- 你这站是**开发者工具文档**——CN 受众多从转介/直链来，不靠 CN Google SEO
- Mermaid label 全英文（已验证），**不需要双语化**——只翻译周围 prose
- 内容总量小（6 页 × ~200 行 prose），翻译 payload < 15KB，**内联即可**，不需要 fetch

### 实施文件结构

```
docs/
├── *.html                       ← 7 页（原 6 + 新 handbook）
├── assets/
│   └── i18n.js                  ← 共享切换逻辑（~80 行）
└── ...
```

每页 `<head>` 内嵌：
```html
<script>
window.I18N_ZH = window.I18N_ZH || {};
window.I18N_ZH['handbook'] = {
  'hero.title': '技能手册',
  'nav.getting-started': '快速开始',
  // ... 该页所有翻译
};
</script>
<script src="./assets/i18n.js" defer></script>
```

每页 `<head>` 顶部：
```html
<link rel="alternate" hreflang="en" href="https://zjgulai.github.io/Agent_skills/<page>.html">
<link rel="alternate" hreflang="x-default" href="https://zjgulai.github.io/Agent_skills/<page>.html">
```

HTML 标记：
```html
<a href="..." data-i18n="nav.getting-started">Getting Started</a>
<h1 data-i18n-html="hero.title">Give <span>OpenCode</span> a brain</h1>
```

Nav 加切换按钮：
```html
<button id="lang-toggle" onclick="window.i18nToggle()" ...>中文</button>
```

### i18n.js 核心逻辑

- 检测 page name from `location.pathname`
- 优先级：`localStorage > navigator.language(zh→zh, else→en) > 'en'`
- `applyLang()` 遍历 `[data-i18n]` 替换 textContent、`[data-i18n-html]` 替换 innerHTML
- 同步更新 `<html lang="">`
- 切换走 `location.reload()`（最干净，让 mermaid 重新初始化）
- 按钮 label 跟随当前 lang 显示对侧语言（EN 模式显示「中文」，反之）

### 已**确定不做**的事

- 不 fetch `i18n/zh.json`（inline 即可，省一次网络请求 + 本地 file:// 可用）
- 不做 URL `?lang=zh`（SEO 无收益，纯增 ugly URL）
- 不翻译 Mermaid 图标签（label 是技术节点名，保持 EN）
- 不翻译 highlight.js code block 内容（代码即代码）
- **不为 CN 内容做单独 hreflang**（接受 SEO tradeoff——单 URL i18n 的已知代价）

---

## 六、执行计划（13 任务，按顺序）

### 阶段 P · 准备资产（部分已完成）

- [x] **P1.** 验证 INDEX.md 可读（已确认 Python `read_text` 完美工作，agent 误判）
- [x] **P2.** 提取关键 4 块内容到 `/tmp/`（典型场景套餐 / 6 域 / 变更日志 / 内嵌 mermaid）
- [ ] **P3.** 重渲 3 个历史态 graph PNG 到 `docs/assets/screenshots/graph-*.png`：
  - `graph-state-0.png`：6 节点（pre-both 安装）
  - `graph-state-1.png`：7 节点（含 GPS，pre-skill-creator）
  - `graph-state-2.png`：8 节点（current，复用现有 PNG）
  - 方法：临时编辑 mmd 副本 → 跑 `render-mermaid.py` → 还原

### 阶段 H · Handbook 内容

- [ ] **H1.** 写 `docs/handbook.html` 骨架（§1-6 sections + sticky TOC + nav + footer + i18n hooks）
- [ ] **H2.** §2 Domain Taxonomy（6 域卡片 + 推断算法 + 7 例回归表，从 `domains.html` + `domain-taxonomy.md` 抽取）
- [ ] **H3.** §3 The 11 Methods（4 phases × 11 cards，每命令含 EN/ZH summary + trigger + badge）
- [ ] **H4.** §4 Skills Graph（图例 + live mermaid 渲染 + §4.3 套餐表）
- [ ] **H5.** §5 Graph Case Studies（4 mermaid 实例 + diff narrative）：
  - 5.1 Initial state（State 0）
  - 5.2 Case A: install guizang-ppt-skill → State 1（mermaid + GPS 节点 + 工具增强 classDef 自动创建解释）
  - 5.3 Case B: install skill-creator → State 2（mermaid + SC 节点 + meta 同域边）
  - 5.4 Hypothetical: 装 3 个 desktop skills 会怎样（mermaid 渲染 + 推理）
- [ ] **H6.** 删除 commands.html / domains.html / case-study.html，改成 redirect HTML：
  ```html
  <!doctype html><meta http-equiv="refresh" content="0; url=./handbook.html#commands">
  ```

### 阶段 I · i18n 系统

- [ ] **I1.** 写 `docs/assets/i18n.js`（~80 行，按 librarian sketch 实现）
- [ ] **I2.** 改 4 页 `<html lang="zh-CN">` → `<html lang="en">`（默认 EN）
- [ ] **I3.** 4 页（index / getting-started / handbook / architecture）每页：
  - 加 `<link rel="alternate" hreflang="en" ...>` + `x-default`
  - 加 `<script>window.I18N_ZH[...]={...}</script>` 翻译块
  - 加 `<script src="./assets/i18n.js" defer></script>`
  - 加 nav 切换按钮 `<button id="lang-toggle">中文</button>`
  - 给所有需要翻译的元素加 `data-i18n` 或 `data-i18n-html`
- [ ] **I4.** 完成 EN/ZH 翻译字典（重头是 handbook 页 — 4-5× hero 长度）

### 阶段 V · 验证

- [ ] **V1.** 本地 `python -m http.server` 跑测：4 页 EN + ZH 双语 200 检查
- [ ] **V2.** Playwright 截 8 张截图（4 页 × 2 语言），人工 look_at 检查
- [ ] **V3.** Doctor 确认 8 个 skill 仍 8/8 PASS（i18n 不应影响功能）
- [ ] **V4.** commit + push + 等 GitHub Pages 重 build
- [ ] **V5.** 线上 4 页 200 检查 + 浏览器视觉验证（生产）

---

## 七、不做的事（v1 边界）

- 不做服务器端 SSR（保持 0-build static）
- 不做 GitHub Actions 自动化部署（GitHub Pages 默认 build 够用）
- 不做内容自动同步（INDEX.md 改了 → handbook 不会自动跟新）
- 不做搜索功能（页内 TOC 即可）
- 不做暗色/亮色切换（统一暗色，有审美一致性）
