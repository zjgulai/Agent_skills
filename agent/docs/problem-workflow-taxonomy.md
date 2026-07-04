---
name: problem-workflow-taxonomy
description: 面向问题解决的 AI 自动化全链路分类协议。作为 6 域 domain taxonomy 之外的第二分类轴，用于把 skill 映射到从产品 idea 到上市推广、运营迭代、复盘沉淀的 workflow 节点。
---

# Problem Workflow Taxonomy

本文定义 Skills Manager 的第二分类轴：**问题解决工作流**。

现有 6 域 taxonomy 回答的是“这个 skill 属于哪类能力管理域”；本文件回答的是“用户遇到什么问题时，该调用哪些 skills 组成自动化链路”。

---

## 一、四层协议

```
Lifecycle Stage → Problem Node → Task Intent → Automation Playbook
```

- **Lifecycle Stage**：产品和业务从 idea 到上市、增长、运营、复盘的阶段。
- **Problem Node**：阶段内稳定、可复现的问题类型。每个 node 有稳定 ID。
- **Task Intent**：用户自然语言中会出现的触发词和任务描述。
- **Automation Playbook**：AI 应该收集哪些输入、调用哪些 primary/supporting skills、产出什么、用什么标准验收。

每个 problem node 必须包含：

- `id`：稳定机器 ID，新增后不随文案重命名。
- `problem_zh` / `problem_en`：一句话定义问题。
- `task_intents`：用户可能说的话，不是抽象标签。
- `primary_skills`：解决该问题的主力 skills。
- `supporting_skills`：按需辅助的 skills。
- `inputs`：进入自动化链路前必须掌握的上下文。
- `outputs`：链路完成后交付的产物。
- `acceptance`：判断是否完成的验收门槛。

---

## 二、14 个阶段

| Stage | 中文名 | 问题焦点 |
|---|---|---|
| `00-agent-system` | AI 自动化底座 | agent、skill、上下文、治理、自动化基础设施 |
| `01-idea-discovery` | 机会与问题发现 | 趋势、竞品、痛点、行业认知 |
| `02-market-validation` | 市场与需求验证 | ICP、MVP、付费意愿、首批用户 |
| `03-product-definition` | 产品定义与路线图 | PRD、范围、issue、指标 |
| `04-design-prototype` | 设计、原型与体验验证 | UX、视觉、原型、设计 QA |
| `05-build-architecture` | 工程构建与架构 | 系统设计、TDD、可维护性 |
| `06-quality-security` | 质量、安全与可观测性 | review、测试、安全、日志、指标 |
| `07-launch-deploy` | 上线、部署与发布门禁 | release、CI/CD、回滚、线上验收 |
| `08-growth-marketing` | 增长、内容与推广 | SEO、内容、广告、邮件、转化 |
| `09-sales-customer` | 销售、客服与客户成功 | 工单、账号、客户材料 |
| `10-data-feedback` | 数据、反馈与洞察 | EDA、BI、VOC、指标驱动迭代 |
| `11-ops-iteration` | 运营、监控与持续迭代 | incident、性能、roadmap 刷新 |
| `12-ip-compliance` | 合规、法务与资产化 | 专利、软著、合同、合规风险 |
| `13-retro-knowledge` | 复盘、知识沉淀与再自动化 | post-mortem、知识库、skill/workflow 更新 |

---

## 三、新增 skill 的归类规则

新增 skill 时保留双轴：

1. **Domain axis**：仍按 `agent/docs/domain-taxonomy.md` 推断一个主域，写入 `INDEX.md` 和 graph。
2. **Problem workflow axis**：按本文件映射到一个或多个 `problem_nodes`。

推荐流程：

1. 读取 `name + description + SKILL.md` 的使用场景。
2. 判断它解决的是哪个用户问题，而不是它用了什么技术。
3. 如果一个 skill 能解决多个问题，最多先挂 3 个最强节点。
4. 如果找不到合适节点，新增 node 前必须定义 inputs / outputs / acceptance。
5. 新 node 必须进入 `docs/_src/problem-workflows.json`，并通过 `tests/test_problem_workflows.py`。

---

## 四、AI 自动化全链路原则

- **问题优先**：分类入口是“用户卡在哪里”，不是“skill 属于什么标签”。
- **可执行**：每个 node 都能转成自动化 playbook；只有描述、没有产物和验收的节点不合格。
- **可组合**：primary skills 解决主体问题，supporting skills 补上下文、视觉、数据、验证或交付。
- **可验收**：每条链路都必须说清楚完成标准。
- **可迭代**：复盘后发现重复动作，应更新 skill、node 或 playbook，而不是只写聊天总结。
- **可扩展**：新增 skill 不要求改 6 域体系；只要挂到 problem node，就能被推荐和站点展示消费。

---

## 五、维护入口

- 机器可读源：`docs/_src/problem-workflows.json`
- 生成数据：`docs/data/problem-workflows.json`
- Skill 反向索引：`docs/data/skills.json` 的 `problem_nodes`
- 渲染入口：`docs/_src/build.py::render_problem_workflows`
- 回归测试：`tests/test_problem_workflows.py`
