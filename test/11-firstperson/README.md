# 11-firstperson - 实体关系抽取与清洗

## 职责范围

第一人负责知识图谱构建流水线中的抽取层：

- 实体抽取：从 LAD chunk、标题、正文中抽取 Method、Dataset、Metric、Concept、Task 等实体。
- 关系抽取：抽取 CONTAINS、USES、EVALUATES_ON、ACHIEVES、COMPARES_WITH 等关系。
- 结果清洗：处理重复实体、缩写/全称、模糊表达、噪声实体、低置信关系和自环关系。
- 抽取 demo：提供可运行的单文档抽取示例。
- 指标报告：输出抽取数量、清洗比例、去重比例、关系保留率和抽样精确度报告。

## 目录说明

| 路径 | 内容 |
|---|---|
| `src/` | 实体抽取、关系抽取、清洗模块源码 |
| `demo/extract_demo.py` | 单文档实体/关系抽取 demo |
| `results/` | demo 输出的实体、关系、清洗 JSON 结果 |
| `reports/pipeline_extraction_report.md` | 流水线抽取统计报告 |
| `reports/extraction_precision_report.md` | 抽取精确度、清洗效果和测试指标报告 |

## 运行方式

在项目根目录运行：

```powershell
python test/11-firstperson/demo/extract_demo.py
```

如未配置 DeepSeek API Key，抽取会自动退化为规则抽取，仍可完成 demo 和清洗流程。

