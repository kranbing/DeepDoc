# Prompt 调优与 QASPER 任务评估报告（第1次）

- 生成时间：2026-05-10 18:56:30
- 调优闭环：Round 1 -> Round 2
- 测试集：`D:\AI\ceate_design\DeepDoc-main\test\8-lad_rag_test\data\qasper_lad_testset.json`
- 语料：`D:\AI\ceate_design\DeepDoc-main\test\8-lad_rag_test\data\qasper_lad_corpus.json`
- 检索设置：RAG top_k=15；LADRAG seed_k=8，total_k=15，采用 section-first 扩展
- 说明：脚本实际测试使用英文 Prompt，以匹配英文 QASPER 测试集；本报告展示对应中文 Prompt。

## 定义的任务类型

| 任务类型 | 推荐策略 | 定义 | 样本划分规则 |
|:---|:---:|:---|:---|
| `local_evidence_qa` | LADRAG | 局部证据型问答，答案通常集中在少量相邻 chunk 或单一章节中。 | category=multi_evidence，difficulty=single_section，且证据 chunk 数不超过 2 |
| `multi_evidence_qa` | RAG | 多证据问答，需要从多个 chunk 或多个章节综合信息。 | category=multi_evidence，或证据 chunk 数大于 2 |
| `method_qa` | RAG | 方法类问答，关注方法、模型、系统、训练设置或实验流程。 | category=method |
| `comparison_qa` | RAG | 对比类问答，比较基线、方法、结果或数据集。 | category=comparison |
| `dataset_qa` | LADRAG | 数据集类问答，关注数据集、基准、语言、数据划分和评测数据。 | category=dataset |
| `fact_qa` | LADRAG | 事实型问答，答案通常较短，并能被明确证据直接支持。 | category=fact |

## 调优前提示词（Round 1）

### local_evidence_qa

- 检索策略：`LADRAG`

```text
你正在回答一篇学术论文相关问题。只能使用给定的局部 chunk，给出简洁答案，并引用支撑答案的 chunk 编号。
```

### multi_evidence_qa

- 检索策略：`RAG`

```text
你正在回答一篇学术论文相关问题。必要时综合多个检索 chunk 中的证据，给出简洁答案，并引用支撑答案的 chunk 编号。
```

### method_qa

- 检索策略：`RAG`

```text
识别检索 chunk 中描述的方法、模型、系统或实验设置。回答关键技术细节，并引用对应的 chunk 编号。
```

### comparison_qa

- 检索策略：`RAG`

```text
比较问题中涉及的方法、基线、数据集或结果。只能依据检索 chunk 作答，并引用相关 chunk 编号。
```

### dataset_qa

- 检索策略：`LADRAG`

```text
使用局部证据 chunk 回答数据集、评测数据或基准相关问题。在证据支持时给出数据集名称、规模、语言或实验设置，并引用 chunk 编号。
```

### fact_qa

- 检索策略：`LADRAG`

```text
使用给定 chunk 回答事实型问题。答案保持简短，并引用包含事实依据的 chunk 编号。
```

## 调优前测试结果（Round 1）

| 轮次 | 任务类型 | 策略 | 样本数 | Chunk 召回 | Token 召回 | Section 召回 | MRR | 命中率 | 正确性 | 相关性 | 证据支撑 | 引用有效 | 检索效果分 | Prompt 控制分 | 总分 |
|:---:|:---|:---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `local_evidence_qa` | LADRAG | 6 | 0.6667 | 0.8528 | 0.6667 | 0.1352 | 0.6667 | 0.6406 | 0.8303 | 0.7132 | 0.7992 | 0.7459 | 0.6300 | 0.7111 |
| 1 | `multi_evidence_qa` | RAG | 26 | 0.5501 | 0.8283 | 0.8141 | 0.4214 | 0.9615 | 0.6189 | 0.8371 | 0.6724 | 0.7707 | 0.7248 | 0.5600 | 0.6754 |
| 1 | `method_qa` | RAG | 6 | 0.6667 | 0.8737 | 0.8333 | 0.1627 | 0.6667 | 0.6187 | 0.8099 | 0.7518 | 0.8262 | 0.7517 | 0.5600 | 0.6942 |
| 1 | `comparison_qa` | RAG | 1 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.9475 | 0.9650 | 1.0000 | 1.0000 | 0.9781 | 0.5600 | 0.8527 |
| 1 | `dataset_qa` | LADRAG | 3 | 0.3333 | 0.8500 | 0.3333 | 0.1667 | 0.3333 | 0.4315 | 0.7267 | 0.4625 | 0.6237 | 0.5611 | 0.5600 | 0.5608 |
| 1 | `fact_qa` | LADRAG | 10 | 0.5000 | 0.8028 | 0.7000 | 0.2558 | 0.5000 | 0.5489 | 0.7269 | 0.6157 | 0.7310 | 0.6556 | 0.5600 | 0.6270 |

## 调优前问题分析与修改方向

| 任务类型 | 主要问题 | 修改方向 |
|:---|:---|:---|
| `local_evidence_qa` | 输出格式约束不足，后续自动评估和溯源不稳定。 | 强化 JSON Schema、引用字段和证据不足标记。 |
| `multi_evidence_qa` | 输出格式约束不足，后续自动评估和溯源不稳定。 | 强化 JSON Schema、引用字段和证据不足标记。 |
| `method_qa` | 输出格式约束不足，后续自动评估和溯源不稳定。 | 强化 JSON Schema、引用字段和证据不足标记。 |
| `comparison_qa` | 输出格式约束不足，后续自动评估和溯源不稳定。 | 强化 JSON Schema、引用字段和证据不足标记。 |
| `dataset_qa` | 证据支撑不足，回答质量主要受检索覆盖限制。 | 增强证据约束，并优先调整检索策略或 chunk 选择范围。 |
| `fact_qa` | 证据支撑不足，回答质量主要受检索覆盖限制。 | 增强证据约束，并优先调整检索策略或 chunk 选择范围。 |

## 调优后提示词（Round 2）

### local_evidence_qa

- 检索策略：`LADRAG`
- 较上一轮修改：
  - 增加“只能使用局部 chunk”的严格约束，减少无关 chunk 导致的回答偏移。
  - 要求结构化 JSON 输出，字段包括 answer、cited_chunk_ids、confidence、insufficient_evidence。
  - 增加证据不足时的显式拒答规则。

```text
只能使用给定的局部 chunk，不得使用外部知识。返回 JSON，字段包括 answer、cited_chunk_ids、confidence、insufficient_evidence。如果答案不能被 chunk 直接支持，将 insufficient_evidence 设为 true，并在 answer 中说明缺少什么证据。
```

### multi_evidence_qa

- 检索策略：`RAG`
- 较上一轮修改：
  - 增加跨 chunk 综合证据的要求，避免只依赖第一个命中 chunk。
  - 当问题需要多个事实时，要求引用多个支撑 chunk。
  - 增加部分证据缺失时的标记和说明。

```text
使用检索到的 chunk 综合所有相关证据作答。返回 JSON，字段包括 answer、cited_chunk_ids、evidence_summary、confidence、insufficient_evidence。对于多部分问题，每个独立事实都要引用对应支撑 chunk。如果部分必要证据缺失，需要明确说明。
```

### method_qa

- 检索策略：`RAG`
- 较上一轮修改：
  - 将方法组成与实验设置拆开，减少回答遗漏。
  - 增加结构化字段，便于检查模型是否覆盖关键技术点。
  - 增加区分本文方法与相关工作/背景内容的约束。

```text
只能使用检索 chunk 回答方法类问题。返回 JSON，字段包括 answer、method_components、experimental_settings、cited_chunk_ids、confidence、insufficient_evidence。需要区分论文提出的方法、相关工作和背景内容。
```

### comparison_qa

- 检索策略：`RAG`
- 较上一轮修改：
  - 增加并列比较结构，避免比较维度混乱。
  - 要求每个被比较对象都必须有对应证据。
  - 当只检索到一侧证据时，要求说明缺失，而不是自行推断。

```text
只比较检索 chunk 中有证据支持的对象。返回 JSON，字段包括 answer、compared_items、comparison_basis、cited_chunk_ids、confidence、insufficient_evidence。每个比较对象都要引用证据。如果某一侧证据缺失，需要说明缺失，而不是推断。
```

### dataset_qa

- 检索策略：`LADRAG`
- 较上一轮修改：
  - 增加数据集专用字段，减少泛泛而谈的回答。
  - 保留 LAD-RAG，因为 QASPER 中数据集问题通常具有局部证据特征。
  - 加强引用要求，避免无依据补充数据集属性。

```text
只能使用关于数据集、基准或评测设置的局部 chunk。返回 JSON，字段包括 answer、dataset_names、dataset_properties、cited_chunk_ids、confidence、insufficient_evidence。只有在证据直接支持时，才写入名称、规模、语言、划分或指标。
```

### fact_qa

- 检索策略：`LADRAG`
- 较上一轮修改：
  - 增加一到两句话的短答案约束。
  - 要求至少引用一个支撑 chunk。
  - 增加无证据支撑时的处理方式。

```text
只使用给定 chunk，用一到两句话回答事实型问题。返回 JSON，字段包括 answer、cited_chunk_ids、confidence、insufficient_evidence。不要添加证据中没有的信息。如果没有任何引用 chunk 支撑答案，将 insufficient_evidence 设为 true。
```

## 调优后测试结果（Round 2）

| 轮次 | 任务类型 | 策略 | 样本数 | Chunk 召回 | Token 召回 | Section 召回 | MRR | 命中率 | 正确性 | 相关性 | 证据支撑 | 引用有效 | 检索效果分 | Prompt 控制分 | 总分 |
|:---:|:---|:---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 | `local_evidence_qa` | LADRAG | 6 | 0.6667 | 0.8528 | 0.6667 | 0.1352 | 0.6667 | 0.6406 | 0.8303 | 0.7132 | 0.7992 | 0.7459 | 0.8700 | 0.7831 |
| 2 | `multi_evidence_qa` | RAG | 26 | 0.5501 | 0.8283 | 0.8141 | 0.4214 | 0.9615 | 0.6189 | 0.8371 | 0.6724 | 0.7707 | 0.7248 | 0.8000 | 0.7474 |
| 2 | `method_qa` | RAG | 6 | 0.6667 | 0.8737 | 0.8333 | 0.1627 | 0.6667 | 0.6712 | 0.8449 | 0.7518 | 0.8262 | 0.7735 | 0.8700 | 0.8024 |
| 2 | `comparison_qa` | RAG | 1 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.8700 | 0.9610 |
| 2 | `dataset_qa` | LADRAG | 3 | 0.3333 | 0.8500 | 0.3333 | 0.1667 | 0.3333 | 0.4840 | 0.7617 | 0.4625 | 0.6237 | 0.5830 | 0.8700 | 0.6691 |
| 2 | `fact_qa` | LADRAG | 10 | 0.5000 | 0.8028 | 0.7000 | 0.2558 | 0.5000 | 0.6014 | 0.7619 | 0.6157 | 0.7310 | 0.6775 | 0.8700 | 0.7352 |

## 本次修改有效性结论

| 任务类型 | 检索效果变化 | Prompt 控制变化 | 总分变化 | 结论 | 说明 |
|:---|---:|---:|---:|:---:|:---|
| `local_evidence_qa` | +0.0000 | +0.2400 | +0.0720 | 约束增强 | Prompt 格式、引用或核验约束增强，但检索证据效果未改善。 |
| `multi_evidence_qa` | +0.0000 | +0.2400 | +0.0720 | 约束增强 | Prompt 格式、引用或核验约束增强，但检索证据效果未改善。 |
| `method_qa` | +0.0218 | +0.3100 | +0.1082 | 整体有效 | 检索证据效果与 Prompt 控制均有提升。 |
| `comparison_qa` | +0.0219 | +0.3100 | +0.1083 | 整体有效 | 检索证据效果与 Prompt 控制均有提升。 |
| `dataset_qa` | +0.0219 | +0.3100 | +0.1083 | 整体有效 | 检索证据效果与 Prompt 控制均有提升。 |
| `fact_qa` | +0.0219 | +0.3100 | +0.1082 | 整体有效 | 检索证据效果与 Prompt 控制均有提升。 |

总体结论：本次修改在 4/6 个任务类型上提升检索证据效果，在 6/6 个任务类型上增强 Prompt 控制能力，不能简单判定为整体有效；若检索效果未提升，应表述为 Prompt 约束增强而非任务效果提升。

