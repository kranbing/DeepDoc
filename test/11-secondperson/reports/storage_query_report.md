# 第二人测试报告：图谱存储、入库与查询

## 存储结构

本次实现采用统一抽象接口 + 多后端实现：

| 后端 | 文件 | 状态 | 用途 |
|---|---|---|---|
| dict/JSON | `src/json_store.py` | 已实现 | 本地 demo、测试、轻量持久化 |
| Neo4j | `src/neo4j_store.py` | 已尝试/预留 | 后续接入图数据库 |
| 抽象接口 | `src/graph_store.py` | 已实现 | 屏蔽具体存储后端 |

## JSON/dict 核心索引

| 索引 | 结构 | 作用 |
|---|---|---|
| `_nodes` | `Dict[str, Dict]` | 按节点 ID 存储节点 |
| `_edges` | `List[Dict]` | 存储边列表 |
| `_adjacency` | `Dict[str, List[int]]` | 一跳邻居和路径查询 |
| `_name_index` | `Dict[str, List[str]]` | 名称精确/模糊查询 |
| `_type_index` | `Dict[str, List[str]]` | 按实体类型查询 |

## 写入接口

| 接口 | 功能 | 测试状态 |
|---|---|---|
| `add_nodes(nodes)` | 批量写入节点，重复 ID 合并 | 通过 |
| `add_edges(edges)` | 批量写入关系，重复边保留高置信版本 | 通过 |
| `save(path)` | 写出 JSON 图谱 | 通过 |
| `load(path)` | 加载 JSON 并重建索引 | 通过 |

## 查询接口

| 接口 | 功能 | 测试结果 |
|---|---|---|
| `get_graph_summary()` | 图谱统计 | 723 nodes / 514 edges |
| `find_entity("BERT")` | 名称查询 | 1 条 |
| `find_entity("Transformer")` | 名称查询 | 2 条 |
| `find_entity("NMT")` | 名称查询 | 0 条 |
| `get_entity_relations(entity)` | 一跳邻居 | 示例实体 6 个邻居 |
| `check_relation(source, target)` | 路径查询 | 示例路径数 0 |
| `search_candidates("question answering")` | 候选检索 | 1 条 |
| `search_candidates("machine translation")` | 候选检索 | 0 条 |

## 入库数据统计

| 指标 | 数值 |
|---|---:|
| 总节点数 | 723 |
| 总关系数 | 514 |
| 图密度 | 0.000984663 |

### 节点类型分布

| 类型 | 数量 |
|---|---:|
| Chunk | 381 |
| Section | 213 |
| Concept | 101 |
| Method | 19 |
| Metric | 4 |
| Task | 2 |
| Dataset | 2 |
| Document | 1 |

### 关系类型分布

| 类型 | 数量 |
|---|---:|
| CONTAINS | 489 |
| COMPARES_WITH | 23 |
| ACHIEVES | 2 |

## 结论

- dict/JSON 存储已能支撑本地 demo、入库测试和基础查询。
- 当前查询能力覆盖名称检索、类型检索、一跳邻居、路径查询和候选搜索。
- Neo4j 后端已保留接口，后续可以将 `JsonGraphStore` 的图数据迁移为 Cypher 写入。
- 当前数据集中结构关系较多、语义关系较少，后续优化重点应放在第一人的关系抽取质量和第三人的 schema 约束上。

