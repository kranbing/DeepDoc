# KG Question-Driven Test Integration Report

- Project: `6cf73d20-55fb-43c6-987e-efc088417ca9`
- Source document: `pdf_fdbd9e01`
- Training QA: `10`
- Graph nodes: `37`
- Graph edges: `36`
- Structural policy: `Section/Chunk are evidence only, not main graph nodes.`

## Node Types

- `Method`: 7
- `Task`: 7
- `Capability`: 6
- `Concept`: 6
- `Problem`: 5
- `Scenario`: 2
- `Interaction`: 1
- `System`: 1
- `Metric`: 1
- `Evidence`: 1

## Relation Types

- `uses`: 5
- `needs`: 4
- `supports`: 3
- `causes`: 2
- `preserves`: 2
- `compared_with`: 2
- `includes`: 2
- `produces`: 2
- `applies_to`: 2
- `solves`: 1
- `provides`: 1
- `has_limitation`: 1
- `harms`: 1
- `improves`: 1
- `acts_as`: 1
- `stores`: 1
- `reduces`: 1
- `requires`: 1
- `organizes`: 1
- `expands_by`: 1
- `filters`: 1

## Test Decisions

### kg_test_01

- Question: 如果我要生成一张 DeepDoc 技术路线图，图谱能提供哪些节点和关系？
- Expected: `merge`
- Actual: `merge`
- Reasonable: `True`
- New nodes: `technical_roadmap`
- Reused nodes: `none`
- Structural nodes rejected: `none`
- Rationale: 测试问答能复用已有节点，并新增少量与生成任务或 LAD-RAG 相关的语义关系，适合合入项目级图谱。

### kg_test_02

- Question: 用户追问 LAD-RAG 与传统 RAG 的区别时，是否应该新增图谱节点？
- Expected: `merge`
- Actual: `merge`
- Reasonable: `True`
- New nodes: `lad_rag`
- Reused nodes: `none`
- Structural nodes rejected: `none`
- Rationale: 测试问答能复用已有节点，并新增少量与生成任务或 LAD-RAG 相关的语义关系，适合合入项目级图谱。

### kg_test_03

- Question: 生成项目总结文档时，图谱是否应该引入章节和 chunk 作为主节点？
- Expected: `reject_structural_nodes`
- Actual: `reject_structural_nodes`
- Reasonable: `True`
- New nodes: `section_nodes, chunk_nodes`
- Reused nodes: `none`
- Structural nodes rejected: `section_nodes, chunk_nodes`
- Rationale: 测试输入试图把章节或 chunk 作为主图谱节点；这会让问题驱动 KG 退化成结构图，应拒绝进入主图，只保留为证据。
