# 11-secondperson - 图谱存储、写入与查询

## 职责范围

第二人负责知识图谱构建流水线中的存储和查询层：

- 设计统一 `GraphStore` 抽象接口。
- 实现 dict/JSON 本地存储方式。
- 预留 Neo4j 图数据库存储方式。
- 实现图谱写入接口：节点批量写入、关系批量写入、重复边处理。
- 实现图谱查询接口：名称搜索、类型查询、一跳邻居、路径查询、候选检索、统计摘要。
- 建立简单查询 demo，并对指定数据集做入库与查询测试。

## 目录说明

| 路径 | 内容 |
|---|---|
| `src/graph_store.py` | 图谱存储抽象接口 |
| `src/json_store.py` | dict + JSON 文件存储实现 |
| `src/neo4j_store.py` | Neo4j 存储接口尝试 |
| `src/query_engine.py` | 查询封装层 |
| `demo/query_demo.py` | 图谱查询 demo |
| `results/kg_graph.json` | 指定数据集入库后的图谱文件 |
| `reports/query_report.json` | 查询测试原始结果 |
| `reports/storage_query_report.md` | 入库和查询测试说明 |

## 运行方式

在项目根目录运行：

```powershell
python test/11-secondperson/demo/query_demo.py
```

demo 默认读取 `test/kg_output/kg_graph.json`。本目录中也保留了一份 `results/kg_graph.json` 作为第二人交付结果。

