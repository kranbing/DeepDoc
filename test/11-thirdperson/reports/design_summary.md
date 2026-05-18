# 第三人交付总结：图谱结构、流程、测试案例与展示

## 图谱基本结构

图谱采用“语义实体为主、结构节点为证据”的设计：

| 类别 | 说明 |
|---|---|
| 主图节点 | Method、Dataset、Metric、Concept、Task、Tool、Document |
| 结构节点 | Section、Chunk，主要用于证据定位和结构关系 |
| 问题驱动节点 | Interaction、Capability、Scenario、Problem、Evidence |

问题驱动 KG 中明确约束：Section/Chunk 不作为主图谱语义节点泛滥扩展，只作为 evidence 或结构辅助信息。

## 实体类型设计

| 类型 | 含义 |
|---|---|
| Document | 文档级节点 |
| Section | 章节结构节点 |
| Chunk | 文档片段节点 |
| Method | 算法、模型、技术方法 |
| Dataset | 数据集、基准集 |
| Metric | 评价指标 |
| Concept | 技术概念 |
| Task | 任务类型 |
| Tool | 工具/框架 |
| Capability | 系统能力 |
| Interaction | 用户问题或问答事件 |
| Evidence | 引用证据 |

## 关系类型设计

| 关系 | 含义 |
|---|---|
| CONTAINS | 文档/章节包含下级节点 |
| USES | 方法使用工具、能力或技术 |
| EVALUATES_ON | 方法在数据集上评估 |
| ACHIEVES | 方法达到指标 |
| BASED_ON | 基于某方法或模型 |
| COMPARES_WITH | 对比关系 |
| PART_OF | 从属关系 |
| SUPPORTS | 证据支持结论 |
| EXPANDS_FROM | 问题驱动图谱由问答拓展 |
| CITES | 问答引用 chunk 证据 |

## 构建流程

1. 读取 LAD chunk 和文档结构。
2. 第一人模块抽取实体和关系。
3. 第一人模块执行实体清洗、关系清洗和 ID 规范化。
4. 第二人模块写入图谱存储。
5. 第二人模块执行入库和查询测试。
6. 第三人模块根据 schema 生成展示数据和测试案例。
7. 系统侧在用户问答后执行问题驱动增量 KG 更新。

## 测试案例

测试案例包括：

- 实体抽取案例：验证 Method、Dataset、Metric、Concept 等实体类型。
- 关系抽取案例：验证 USES、ACHIEVES、COMPARES_WITH、CONTAINS 等关系。
- 查询案例：验证名称搜索、一跳邻居、路径查询、候选检索。
- 问题驱动案例：验证问答是否应合入主图、是否拒绝结构节点进入主图。

## 展示设计

展示层包含两类页面：

- `display/kg_graph_frontend.html`：基础 KG 展示页面。
- `question_driven_demo/kg_graph_preview.html`：问题驱动 KG 预览页面。

主系统中已进一步集成嵌入式 KG 展示方式，点击 KG 后在文档中间 viewer 内展示图谱，不再新开页面。

## 交付状态

| 项目 | 状态 |
|---|---|
| 图谱 schema | 已完成 |
| 构建流程文档 | 已完成 |
| 流程脚本 | 已完成 |
| 测试案例集 | 已完成 |
| 图谱展示页面 | 已完成 |
| 问题驱动 KG demo | 已完成 |

