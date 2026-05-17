# 第二人模型参数测试报告

- 生成时间：2026-05-10 16:10:01
- 测试集：`D:\AI\ceate_design\DeepDoc-main\test\8-lad_rag_test\data\qasper_lad_testset.json`
- 说明：该脚本真实调用 DeepSeek API，需要配置 `DEEPSEEK_API_KEY` 或 `backend/.deepseek_api_key`。

## 参数模式汇总

| 参数模式 | 样本数 | 错误率 | 格式合规率 | 引用字段存在率 | 平均延迟(ms) | 平均答案长度 |
|:---|---:|---:|---:|---:|---:|---:|
| balanced | 6 | 0.0000 | 1.0000 | 1.0000 | 1968.83 | 184.00 |
| exploratory | 6 | 0.0000 | 1.0000 | 1.0000 | 2001.33 | 131.17 |
| stable | 6 | 0.0000 | 1.0000 | 1.0000 | 2032.33 | 159.67 |

## 参数影响分析

- 延迟最低的参数模式：`balanced`，平均延迟 1968.83 ms。
- 回答最长的参数模式：`balanced`，平均答案长度 184.00 字符。
- 错误率最低的参数模式：`balanced`，错误率 0.0000。
- 解释：`stable` 更偏稳定和短回答；`balanced` 用于默认折中；`exploratory` 更容易生成更长答案，但可能带来更高延迟。

## 样本明细

| Case | 参数模式 | 任务类型 | 检索策略 | 格式合规 | 引用数 | 延迟(ms) | 错误 |
|:---|:---|:---|:---:|:---:|---:|---:|:---|
| qasper_0001 | stable | `comparison_qa` | rag | True | 4 | 2211 |  |
| qasper_0001 | balanced | `comparison_qa` | rag | True | 4 | 1795 |  |
| qasper_0001 | exploratory | `comparison_qa` | rag | True | 4 | 1948 |  |
| qasper_0002 | stable | `comparison_qa` | rag | True | 4 | 2561 |  |
| qasper_0002 | balanced | `comparison_qa` | rag | True | 3 | 2683 |  |
| qasper_0002 | exploratory | `comparison_qa` | rag | True | 4 | 2791 |  |
| qasper_0003 | stable | `dataset_qa` | rag | True | 4 | 1610 |  |
| qasper_0003 | balanced | `dataset_qa` | rag | True | 4 | 1528 |  |
| qasper_0003 | exploratory | `dataset_qa` | rag | True | 4 | 1349 |  |
| qasper_0004 | stable | `fact_qa` | lad | True | 4 | 3188 |  |
| qasper_0004 | balanced | `fact_qa` | lad | True | 4 | 3038 |  |
| qasper_0004 | exploratory | `fact_qa` | lad | True | 4 | 2358 |  |
| qasper_0005 | stable | `method_qa` | rag | True | 1 | 1452 |  |
| qasper_0005 | balanced | `method_qa` | rag | True | 2 | 1581 |  |
| qasper_0005 | exploratory | `method_qa` | rag | True | 1 | 1607 |  |
| qasper_0006 | stable | `fact_qa` | lad | True | 2 | 1172 |  |
| qasper_0006 | balanced | `fact_qa` | lad | True | 2 | 1188 |  |
| qasper_0006 | exploratory | `fact_qa` | lad | True | 2 | 1955 |  |

## 模型回答样例

### qasper_0001 | stable | `comparison_qa`

- 问题：which multilingual approaches do they compare with?
- 引用：evidence_1, evidence_2, evidence_4, evidence_5
- 回答：The paper compares with three multilingual approaches: pivoting, multilingual NMT (MNMT), and cross-lingual transfer without pretraining.

### qasper_0001 | balanced | `comparison_qa`

- 问题：which multilingual approaches do they compare with?
- 引用：evidence_1, evidence_2, evidence_4, evidence_5
- 回答：The paper compares with three multilingual approaches: pivoting, multilingual NMT (MNMT), and cross-lingual transfer without pretraining.

### qasper_0001 | exploratory | `comparison_qa`

- 问题：which multilingual approaches do they compare with?
- 引用：evidence_1, evidence_2, evidence_4, evidence_5
- 回答：They compare with pivoting, multilingual NMT (MNMT), and cross-lingual transfer without pretraining.

### qasper_0002 | stable | `comparison_qa`

- 问题：what are the pivot-based baselines?
- 引用：evidence_1, evidence_2, evidence_4, evidence_6
- 回答：The pivot-based baselines include pivoting and pivot-synthetic. Pivoting translates source to pivot then to target in two steps (evidence_1, evidence_2, evidence_4, evidence_6). Pivot-synthetic trains a source→target model with pseudo data generated from source-pivot or pivot-target parallel data (evidence_6).

### qasper_0002 | balanced | `comparison_qa`

- 问题：what are the pivot-based baselines?
- 引用：evidence_2, evidence_4, evidence_6
- 回答：The pivot-based baselines are pivoting and pivot-synthetic. Pivoting translates source to pivot then to target in two steps, using MNMT to translate source to pivot then to target in two separate steps with each step receiving supervised signal of parallel corpora (evidence_2, evidence_4). Pivot-synthetic trains a source→target model with pseudo data generated from source-pivot or pivot-target parallel data (evidence_6).

### qasper_0002 | exploratory | `comparison_qa`

- 问题：what are the pivot-based baselines?
- 引用：evidence_1, evidence_2, evidence_4, evidence_6
- 回答：The pivot-based baselines include pivoting and pivot-synthetic. Pivoting translates source to pivot then to target in two steps (evidence_1, evidence_2, evidence_4, evidence_6). Pivot-synthetic trains a source→target model with pseudo data generated from source-pivot or pivot-target parallel data (evidence_6).

### qasper_0003 | stable | `dataset_qa`

- 问题：which datasets did they experiment with?
- 引用：evidence_1, evidence_2, evidence_3, evidence_4
- 回答：Europarl and MultiUN

### qasper_0003 | balanced | `dataset_qa`

- 问题：which datasets did they experiment with?
- 引用：evidence_1, evidence_2, evidence_3, evidence_4
- 回答：Europarl and MultiUN

### qasper_0003 | exploratory | `dataset_qa`

- 问题：which datasets did they experiment with?
- 引用：evidence_1, evidence_2, evidence_3, evidence_4
- 回答：Europarl and MultiUN

### qasper_0004 | stable | `fact_qa`

- 问题：what language pairs are explored?
- 引用：evidence_1, evidence_2, evidence_4, evidence_5
- 回答：The language pairs explored are: French-English-Spanish (Fr-En-Es), German-English-French (De-En-Fr), Romanian-English-German (Ro-En-De) for Europarl; and English-Arabic (En-Ar), English-Spanish (En-Es), English-Russian (En-Ru), and zero-shot pairs Arabic-Spanish (Ar-Es), Arabic-Russian (Ar-Ru), Spanish-Arabic (Es-Ar), Spanish-Russian (Es-Ru), Russian-Arabic (Ru-Ar), Russian-Spanish (Ru-Es) for MultiUN.

### qasper_0004 | balanced | `fact_qa`

- 问题：what language pairs are explored?
- 引用：evidence_1, evidence_2, evidence_4, evidence_5
- 回答：The language pairs explored are: for MultiUN corpus: Arabic-English, Spanish-English, Russian-English, and zero-shot pairs Arabic-Spanish, Arabic-Russian, Spanish-Arabic, Spanish-Russian, Russian-Arabic, Russian-Spanish. For Europarl corpus: French-English, English-Spanish, French-Spanish (zero-shot), German-English, English-French, German-French (zero-shot), Romanian-English, English-German, Romanian-German (zero-shot).

### qasper_0004 | exploratory | `fact_qa`

- 问题：what language pairs are explored?
- 引用：evidence_1, evidence_2, evidence_4, evidence_5
- 回答：MultiUN corpus: English-Arabic, English-Spanish, English-Russian, and zero-shot pairs Arabic-Spanish, Arabic-Russian, Spanish-Arabic, Spanish-Russian, Russian-Arabic, Russian-Spanish. Europarl corpus: French-English-Spanish, German-English-French, Romanian-English-German.

## 工程结论

- 任务分发链路已跑通：每条样本都经过 `task_type -> retrieval_mode -> prompt -> model_config`。
- 大模型异常处理已进入真实调用路径：API 错误、超时、空响应、JSON 解析失败会写入样本明细。
- 后续若要评估正确性，需要接入 gold answer 或 evidence 一致性评分；当前报告主要评估参数对格式、引用、长度和延迟的影响。
