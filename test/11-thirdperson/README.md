# 11-thirdperson - 图谱结构设计、流程与展示

## 职责范围

第三人负责知识图谱的设计和验证材料：

- 设计知识图谱基本结构。
- 确定实体类型、关系类型和节点/边属性。
- 撰写 schema 与流程设计文档。
- 设计图谱构建流程，提供流程图/流程说明。
- 制作知识图谱测试案例集。
- 设计图谱展示页面和问题驱动 KG 展示 demo。

## 目录说明

| 路径 | 内容 |
|---|---|
| `design/kg_schema.md` | 实体类型、关系类型、属性设计 |
| `flow/kg_pipeline.md` | 图谱构建流程文档 |
| `flow/run_kg_pipeline.py` | 端到端 KG 流水线入口 |
| `cases/kg_test_cases.json` | 图谱测试案例集 |
| `display/kg_graph_frontend.html` | 图谱展示页面 |
| `display/schema_graph_preview.html` | schema 图预览 |
| `display/visualize_graph.py` | 图谱可视化脚本 |
| `question_driven_demo/` | 问题驱动 KG 测试集、图谱和集成报告 |
| `reports/design_summary.md` | 第三人设计交付总结 |

## 运行方式

端到端构建：

```powershell
python test/11-thirdperson/flow/run_kg_pipeline.py
```

查看展示 demo：

```powershell
start test/11-thirdperson/display/kg_graph_frontend.html
start test/11-thirdperson/question_driven_demo/kg_graph_preview.html
```

