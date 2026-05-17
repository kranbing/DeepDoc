# Chunk 证据链答案溯源评估报告

- 生成时间：2026-05-10 18:56:29
- 输入报告：`D:\AI\ceate_design\DeepDoc-main\test\9-second_person\results\model_param_test_report.json`
- 说明：本报告复用第二人真实大模型输出，构造 QASPER evidence chunk_context，评估结构化输出、引用存在性和 claim->chunk 支撑一致性。

## 结构化输出要求

| 字段 | 要求 |
|:---|:---|
| `answer` | 模型最终答案，字符串 |
| `cited_chunk_ids` | 答案引用的 chunk 编号列表 |
| `claim_evidence_map` | 每个关键结论对应的依赖 chunk 编号 |
| `insufficient_evidence` | 证据不足时为 true |
| `follow_up_questions` | 后续问题列表 |

## 汇总结果

| 任务类型 | 样本数 | 结构合规率 | 引用存在率 | 定位完整率 | Claim 支撑率 | 平均支撑分 | 无效引用数 | 缺失引用率 |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|
| `comparison_qa` | 6 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.8772 | 0 | 0.0000 |
| `dataset_qa` | 3 | 0.6667 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0 | 0.0000 |
| `fact_qa` | 6 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.9491 | 0 | 0.0000 |
| `method_qa` | 3 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.9667 | 0 | 0.0000 |

## 样本明细

| Case | 参数模式 | 任务类型 | 结构合规 | 引用存在率 | Claim 支撑率 | 平均支撑分 | 缺失引用 |
|:---|:---|:---|:---:|---:|---:|---:|:---|
| qasper_0001 | stable | `comparison_qa` | True | 1.0000 | 1.0000 | 0.8333 | 无 |
| qasper_0001 | balanced | `comparison_qa` | True | 1.0000 | 1.0000 | 0.8333 | 无 |
| qasper_0001 | exploratory | `comparison_qa` | True | 1.0000 | 1.0000 | 1.0000 | 无 |
| qasper_0002 | stable | `comparison_qa` | True | 1.0000 | 1.0000 | 0.8500 | 无 |
| qasper_0002 | balanced | `comparison_qa` | True | 1.0000 | 1.0000 | 0.8966 | 无 |
| qasper_0002 | exploratory | `comparison_qa` | True | 1.0000 | 1.0000 | 0.8500 | 无 |
| qasper_0003 | stable | `dataset_qa` | True | 1.0000 | 1.0000 | 1.0000 | 无 |
| qasper_0003 | balanced | `dataset_qa` | True | 1.0000 | 1.0000 | 1.0000 | 无 |
| qasper_0003 | exploratory | `dataset_qa` | False | 1.0000 | 1.0000 | 1.0000 | 无 |
| qasper_0004 | stable | `fact_qa` | True | 1.0000 | 1.0000 | 0.9048 | 无 |
| qasper_0004 | balanced | `fact_qa` | True | 1.0000 | 1.0000 | 0.8667 | 无 |
| qasper_0004 | exploratory | `fact_qa` | True | 1.0000 | 1.0000 | 0.9231 | 无 |
| qasper_0005 | stable | `method_qa` | True | 1.0000 | 1.0000 | 1.0000 | 无 |
| qasper_0005 | balanced | `method_qa` | True | 1.0000 | 1.0000 | 0.9000 | 无 |
| qasper_0005 | exploratory | `method_qa` | True | 1.0000 | 1.0000 | 1.0000 | 无 |
| qasper_0006 | stable | `fact_qa` | True | 1.0000 | 1.0000 | 1.0000 | 无 |
| qasper_0006 | balanced | `fact_qa` | True | 1.0000 | 1.0000 | 1.0000 | 无 |
| qasper_0006 | exploratory | `fact_qa` | True | 1.0000 | 1.0000 | 1.0000 | 无 |

## 错误案例

### qasper_0003 | exploratory | `dataset_qa`

- 问题：which datasets did they experiment with?
- 答案：Europarl and MultiUN
- 缺失字段：无
- 类型错误：follow_up_questions must be list
- 无效引用：无
- Claim 支撑：[{"claim": "Europarl and MultiUN", "chunk_ids": ["evidence_1", "evidence_2", "evidence_3", "evidence_4"], "existing_chunk_ids": ["evidence_1", "evidence_2", "evidence_3", "evidence_4"], "missing_chunk_ids": [], "support_score": 1.0, "support_level": "strong"}]

## 结论

- 证据链包装模块已能统一输出 `resolved_citations`、`missing_chunk_ids`、`claim_traces` 和一致性指标。
- 当前第二人输出没有原生 `claim_evidence_map` 和 `insufficient_evidence`，第三人脚本会补齐默认结构用于评估；主系统后续应强制模型原生返回这些字段。
- 如果引用编号全部来自构造的 `evidence_1` 等 evidence chunk，则引用存在性可以验证；真实主系统接入时应改用实际 `chunkId` 并保留 page/bbox 定位信息。
