# KG 三人分工目录索引

本目录将原先分散在 `kg_extraction`、`kg_storage`、`kg_design`、`kg_output`、`kg_question_driven` 和 `run_kg_pipeline.py` 中的知识图谱测试内容，按三人职责重新整理为 `11-*` 目录。

## 第一人：`11-firstperson`

负责实体抽取、关系抽取、结果清洗、抽取 demo 和抽取指标报告。

主要内容：

- `src/entity_extractor.py`
- `src/relation_extractor.py`
- `src/cleaner.py`
- `demo/extract_demo.py`
- `reports/extraction_precision_report.md`
- `reports/pipeline_extraction_report.md`

## 第二人：`11-secondperson`

负责图谱存储结构、dict/JSON 与 Neo4j 存储尝试、写入接口、查询接口、查询 demo 和入库查询报告。

主要内容：

- `src/graph_store.py`
- `src/json_store.py`
- `src/neo4j_store.py`
- `src/query_engine.py`
- `demo/query_demo.py`
- `results/kg_graph.json`
- `reports/storage_query_report.md`
- `reports/query_report.json`

## 第三人：`11-thirdperson`

负责图谱 schema、实体/关系/属性设计、构建流程、流程脚本、测试案例集和展示页面。

主要内容：

- `design/kg_schema.md`
- `flow/kg_pipeline.md`
- `flow/run_kg_pipeline.py`
- `cases/kg_test_cases.json`
- `display/kg_graph_frontend.html`
- `question_driven_demo/`
- `reports/design_summary.md`

## 保留说明

原 `kg_*` 目录暂时保留，用作历史实验目录和兼容旧脚本。新提交、展示和验收建议优先使用 `11-firstperson`、`11-secondperson`、`11-thirdperson`。

