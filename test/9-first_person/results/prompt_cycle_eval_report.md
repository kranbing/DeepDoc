# Prompt 调优与 QASPER 任务评估报告（第2次）

- 生成时间：2026-05-10 18:56:30
- 调优闭环：Round 2 -> Round 3
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

## 调优前提示词（Round 2）

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

## 调优前测试结果（Round 2）

| 轮次 | 任务类型 | 策略 | 样本数 | Chunk 召回 | Token 召回 | Section 召回 | MRR | 命中率 | 正确性 | 相关性 | 证据支撑 | 引用有效 | 检索效果分 | Prompt 控制分 | 总分 |
|:---:|:---|:---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 | `local_evidence_qa` | LADRAG | 6 | 0.6667 | 0.8528 | 0.6667 | 0.1352 | 0.6667 | 0.6406 | 0.8303 | 0.7132 | 0.7992 | 0.7459 | 0.8700 | 0.7831 |
| 2 | `multi_evidence_qa` | RAG | 26 | 0.5501 | 0.8283 | 0.8141 | 0.4214 | 0.9615 | 0.6189 | 0.8371 | 0.6724 | 0.7707 | 0.7248 | 0.8000 | 0.7474 |
| 2 | `method_qa` | RAG | 6 | 0.6667 | 0.8737 | 0.8333 | 0.1627 | 0.6667 | 0.6712 | 0.8449 | 0.7518 | 0.8262 | 0.7735 | 0.8700 | 0.8024 |
| 2 | `comparison_qa` | RAG | 1 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.8700 | 0.9610 |
| 2 | `dataset_qa` | LADRAG | 3 | 0.3333 | 0.8500 | 0.3333 | 0.1667 | 0.3333 | 0.4840 | 0.7617 | 0.4625 | 0.6237 | 0.5830 | 0.8700 | 0.6691 |
| 2 | `fact_qa` | LADRAG | 10 | 0.5000 | 0.8028 | 0.7000 | 0.2558 | 0.5000 | 0.6014 | 0.7619 | 0.6157 | 0.7310 | 0.6775 | 0.8700 | 0.7352 |

## 调优前问题分析与修改方向

| 任务类型 | 主要问题 | 修改方向 |
|:---|:---|:---|
| `local_evidence_qa` | 整体表现较稳定，主要优化空间在细粒度证据核验。 | 保留当前策略，补充 claim-level 证据检查。 |
| `multi_evidence_qa` | 整体表现较稳定，主要优化空间在细粒度证据核验。 | 保留当前策略，补充 claim-level 证据检查。 |
| `method_qa` | 整体表现较稳定，主要优化空间在细粒度证据核验。 | 保留当前策略，补充 claim-level 证据检查。 |
| `comparison_qa` | 整体表现较稳定，主要优化空间在细粒度证据核验。 | 保留当前策略，补充 claim-level 证据检查。 |
| `dataset_qa` | 证据支撑不足，回答质量主要受检索覆盖限制。 | 增强证据约束，并优先调整检索策略或 chunk 选择范围。 |
| `fact_qa` | 证据支撑不足，回答质量主要受检索覆盖限制。 | 增强证据约束，并优先调整检索策略或 chunk 选择范围。 |

## 调优后提示词（Round 3）

### local_evidence_qa

- 检索策略：`LADRAG`
- 较上一轮修改：
  - 增加回答前的证据核验步骤。
  - 要求引用 chunk 必须能直接支撑最终答案。
  - 保留 LADRAG，因为局部证据型问题仍适合受限 chunk 邻域。

```text
只能使用给定的局部 chunk。最终回答前，逐项核验答案中的每个判断是否至少被一个引用 chunk 直接支撑。返回 JSON，字段包括 answer、cited_chunk_ids、evidence_check、confidence、insufficient_evidence。如果局部 chunk 只能部分支撑答案，将 insufficient_evidence 设为 true，并在 evidence_check 中列出缺失证据。
```

### multi_evidence_qa

- 检索策略：`RAG`
- 较上一轮修改：
  - 增加逐条结论的证据核验，减少无依据综合。
  - 要求按答案结论组织引用 chunk。
  - 保留 RAG，因为跨章节问题需要更广的证据覆盖。

```text
使用检索 chunk 回答多证据问题。先识别问题需要回答的不同结论，再逐条用引用 chunk 核验。返回 JSON，字段包括 answer、claim_evidence_map、cited_chunk_ids、confidence、insufficient_evidence。如果某个必要结论缺少证据，需要明确说明，而不是补全推断。
```

### method_qa

- 检索策略：`RAG`
- 较上一轮修改：
  - 将“本文方法”和“背景/相关工作”的区分纳入证据核验。
  - 要求每个方法组成部分都携带支撑 chunk 编号。
  - 保留 RAG，因为方法细节可能分布在方法、实验和结果章节。

```text
只能使用检索 chunk 回答方法类问题。区分 proposed_method、background_or_related_work 和 experimental_settings，并为每个方法组成部分核验支撑 chunk。返回 JSON，字段包括 answer、proposed_method、background_or_related_work、experimental_settings、cited_chunk_ids、confidence、insufficient_evidence。
```

### comparison_qa

- 检索策略：`RAG`
- 较上一轮修改：
  - 增加先确定比较维度再生成答案的要求。
  - 要求每个比较对象和每个比较维度都有证据。
  - 保留某一侧证据缺失时的显式说明。

```text
只比较检索 chunk 中有证据支持的对象。先确定比较维度，再逐项核验每个对象在各维度下的证据。返回 JSON，字段包括 answer、comparison_dimensions、compared_items、cited_chunk_ids、confidence、insufficient_evidence。如果某个对象或维度缺少证据，需要标记为缺失。
```

### dataset_qa

- 检索策略：`RAG`
- 较上一轮修改：
  - 将检索策略从 LADRAG 调整为 RAG，因为第二轮数据集类问题的证据覆盖仍偏低。
  - 增加数据集属性级别的证据核验，避免补充无依据的数据集细节。
  - 要求无证据支撑的属性必须省略或标记为缺失。

```text
使用检索 chunk 回答数据集、基准或评测数据问题。写入任何数据集属性前都要先核验证据。返回 JSON，字段包括 answer、dataset_names、verified_attributes、missing_attributes、cited_chunk_ids、confidence、insufficient_evidence。只有引用 chunk 直接支持时，才写入名称、规模、语言、划分、指标或设置。
```

### fact_qa

- 检索策略：`LADRAG`
- 较上一轮修改：
  - 增加事实结论级别的证据核验。
  - 保留短答案要求，同时维持证据不足处理。
  - 保留 LADRAG，因为事实型答案通常受益于局部证据约束。

```text
只使用给定 chunk，用一到两句话回答事实型问题。最终回答前，需要用引用 chunk 核验事实结论。返回 JSON，字段包括 answer、cited_chunk_ids、evidence_check、confidence、insufficient_evidence。如果事实结论不能被直接支撑，将 insufficient_evidence 设为 true。
```

## 调优后测试结果（Round 3）

| 轮次 | 任务类型 | 策略 | 样本数 | Chunk 召回 | Token 召回 | Section 召回 | MRR | 命中率 | 正确性 | 相关性 | 证据支撑 | 引用有效 | 检索效果分 | Prompt 控制分 | 总分 |
|:---:|:---|:---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 3 | `local_evidence_qa` | LADRAG | 6 | 0.6667 | 0.8528 | 0.6667 | 0.1352 | 0.6667 | 0.6406 | 0.8303 | 0.7132 | 0.7992 | 0.7459 | 1.0000 | 0.8221 |
| 3 | `multi_evidence_qa` | RAG | 26 | 0.5501 | 0.8283 | 0.8141 | 0.4214 | 0.9615 | 0.6189 | 0.8371 | 0.6724 | 0.7707 | 0.7248 | 0.9300 | 0.7864 |
| 3 | `method_qa` | RAG | 6 | 0.6667 | 0.8737 | 0.8333 | 0.1627 | 0.6667 | 0.6712 | 0.8449 | 0.7518 | 0.8262 | 0.7735 | 1.0000 | 0.8415 |
| 3 | `comparison_qa` | RAG | 1 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| 3 | `dataset_qa` | RAG | 3 | 0.3333 | 0.8500 | 0.3333 | 0.1667 | 0.3333 | 0.4840 | 0.7617 | 0.4625 | 0.6237 | 0.5830 | 1.0000 | 0.7081 |
| 3 | `fact_qa` | LADRAG | 10 | 0.5000 | 0.8028 | 0.7000 | 0.2558 | 0.5000 | 0.6014 | 0.7619 | 0.6157 | 0.7310 | 0.6775 | 1.0000 | 0.7742 |

## 本次修改有效性结论

| 任务类型 | 检索效果变化 | Prompt 控制变化 | 总分变化 | 结论 | 说明 |
|:---|---:|---:|---:|:---:|:---|
| `local_evidence_qa` | +0.0000 | +0.1300 | +0.0390 | 约束增强 | Prompt 格式、引用或核验约束增强，但检索证据效果未改善。 |
| `multi_evidence_qa` | +0.0000 | +0.1300 | +0.0390 | 约束增强 | Prompt 格式、引用或核验约束增强，但检索证据效果未改善。 |
| `method_qa` | +0.0000 | +0.1300 | +0.0391 | 约束增强 | Prompt 格式、引用或核验约束增强，但检索证据效果未改善。 |
| `comparison_qa` | +0.0000 | +0.1300 | +0.0390 | 约束增强 | Prompt 格式、引用或核验约束增强，但检索证据效果未改善。 |
| `dataset_qa` | +0.0000 | +0.1300 | +0.0390 | 约束增强 | Prompt 格式、引用或核验约束增强，但检索证据效果未改善。 策略由 LADRAG 调整为 RAG，但检索效果未提升。 |
| `fact_qa` | +0.0000 | +0.1300 | +0.0390 | 约束增强 | Prompt 格式、引用或核验约束增强，但检索证据效果未改善。 |

总体结论：本次修改在 0/6 个任务类型上提升检索证据效果，在 6/6 个任务类型上增强 Prompt 控制能力，不能简单判定为整体有效；若检索效果未提升，应表述为 Prompt 约束增强而非任务效果提升。

