"""Generate a question-driven KG demo for one DeepDoc project document.

This is a deterministic simulation:
- 10 Q/A turns incrementally build the project knowledge graph.
- 3 held-out Q/A turns test whether proposed additions should merge into it.
- Structural chunk/section data is used only as evidence, not as graph nodes.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
TEST_DIR = ROOT / "test"
OUT_DIR = TEST_DIR / "kg_question_driven"
DOC_DIR = (
    ROOT
    / "data"
    / "projects"
    / "6cf73d20-55fb-43c6-987e-efc088417ca9"
    / "documents"
    / "pdf_fdbd9e01"
)
LAD_CHUNK_PATH = DOC_DIR / "lad_chunk.json"

PROJECT_ID = "6cf73d20-55fb-43c6-987e-efc088417ca9"
DOC_ID = "pdf_fdbd9e01"
DOC_NAME = "DeepDoc-文档理解与多源数据整合的知识服务平台.pdf"


def evidence(*chunk_ids: str) -> list[dict[str, Any]]:
    return [
        {
            "projectId": PROJECT_ID,
            "docId": DOC_ID,
            "docName": DOC_NAME,
            "chunkId": chunk_id,
        }
        for chunk_id in chunk_ids
    ]


TRAIN_QA: list[dict[str, Any]] = [
    {
        "id": "kg_train_01",
        "scope": "document",
        "question": "DeepDoc 这个项目要解决的核心问题是什么？",
        "answer": "DeepDoc 面向企业和教育场景中非结构化文档难以理解、检索和复用的问题，目标是把文档解析、RAG 检索、知识图谱和证据溯源组合成知识服务平台。",
        "evidence": evidence("p0003_c002", "p0007_c005", "p0007_c008"),
        "graph_delta": {
            "nodes": [
                ["deepdoc", "System", "DeepDoc"],
                ["unstructured_document_problem", "Problem", "非结构化文档理解困难"],
                ["knowledge_service_platform", "Capability", "知识服务平台"],
            ],
            "edges": [
                ["deepdoc", "solves", "unstructured_document_problem"],
                ["deepdoc", "provides", "knowledge_service_platform"],
            ],
        },
    },
    {
        "id": "kg_train_02",
        "scope": "document",
        "question": "DeepDoc 的整体技术路线包括哪些关键能力？",
        "answer": "技术路线可以概括为解析、理解、关联和应用：先做文档内容抽取，再通过布局感知检索与 RAG 理解长文档，之后用知识图谱建立语义关联，最后支撑问答、图表和文档生成。",
        "evidence": evidence("p0003_c002", "p0009_c007", "p0010_c001", "p0010_c002"),
        "graph_delta": {
            "nodes": [
                ["document_parsing", "Capability", "文档解析"],
                ["layout_aware_retrieval", "Method", "布局感知检索"],
                ["rag", "Method", "检索增强生成"],
                ["knowledge_graph", "Method", "知识图谱"],
                ["content_generation", "Capability", "内容生成"],
            ],
            "edges": [
                ["deepdoc", "uses", "document_parsing"],
                ["deepdoc", "uses", "layout_aware_retrieval"],
                ["deepdoc", "uses", "rag"],
                ["deepdoc", "uses", "knowledge_graph"],
                ["deepdoc", "supports", "content_generation"],
            ],
        },
    },
    {
        "id": "kg_train_03",
        "scope": "document",
        "question": "为什么普通 RAG 对长文档效果不好？",
        "answer": "普通 RAG 常把文档切成扁平 chunk，容易破坏章节层级和上下文边界；长文档中同一概念跨章节出现时，检索结果缺少结构约束，答案容易片段化。",
        "evidence": evidence("p0010_c001", "p0024_c004", "p0025_c002"),
        "graph_delta": {
            "nodes": [
                ["traditional_rag", "Method", "传统 RAG"],
                ["flat_chunking", "Problem", "扁平切块"],
                ["context_fragmentation", "Problem", "上下文碎片化"],
                ["long_document_qa", "Task", "长文档问答"],
            ],
            "edges": [
                ["traditional_rag", "has_limitation", "flat_chunking"],
                ["flat_chunking", "causes", "context_fragmentation"],
                ["context_fragmentation", "harms", "long_document_qa"],
            ],
        },
    },
    {
        "id": "kg_train_04",
        "scope": "document",
        "question": "LAD 或布局感知机制相比传统 chunk 的价值是什么？",
        "answer": "LAD 强调保留文档结构和版面语义，使检索不只依赖文本相似度，还能利用章节、标题、邻近块等结构线索，缓解长文档中的语义断裂。",
        "evidence": evidence("p0024_c004", "p0025_c002", "p0025_c004"),
        "graph_delta": {
            "nodes": [
                ["lad", "Method", "布局感知文档块 LAD"],
                ["document_structure", "Concept", "文档结构"],
                ["semantic_boundary", "Concept", "语义边界"],
                ["retrieval_precision", "Metric", "检索精度"],
            ],
            "edges": [
                ["lad", "preserves", "document_structure"],
                ["lad", "preserves", "semantic_boundary"],
                ["lad", "improves", "retrieval_precision"],
                ["lad", "compared_with", "flat_chunking"],
            ],
        },
    },
    {
        "id": "kg_train_05",
        "scope": "document",
        "question": "知识图谱在 DeepDoc 中承担什么作用？",
        "answer": "知识图谱不应只展示章节结构，而应把问题、概念、方法、模块、场景和结论连接起来，作为项目级知识记忆，为跨文档问答和内容生成提供结构化上下文。",
        "evidence": evidence("p0010_c002", "p0024_c006", "p0032_c009"),
        "graph_delta": {
            "nodes": [
                ["project_memory", "Capability", "项目级知识记忆"],
                ["cross_document_qa", "Task", "跨文档问答"],
                ["semantic_relation", "Concept", "语义关系"],
            ],
            "edges": [
                ["knowledge_graph", "acts_as", "project_memory"],
                ["knowledge_graph", "supports", "cross_document_qa"],
                ["knowledge_graph", "stores", "semantic_relation"],
            ],
        },
    },
    {
        "id": "kg_train_06",
        "scope": "document",
        "question": "DeepDoc 如何保证回答可追溯？",
        "answer": "系统需要把回答、知识节点和关系都绑定到源文档 chunk、页码或章节，让用户能从生成结论回到原文证据，降低幻觉风险。",
        "evidence": evidence("p0003_c002", "p0036_c001", "p0036_c004"),
        "graph_delta": {
            "nodes": [
                ["evidence_traceability", "Capability", "证据溯源"],
                ["source_chunk", "Evidence", "来源 chunk"],
                ["hallucination_risk", "Problem", "幻觉风险"],
            ],
            "edges": [
                ["evidence_traceability", "uses", "source_chunk"],
                ["evidence_traceability", "reduces", "hallucination_risk"],
                ["knowledge_graph", "requires", "evidence_traceability"],
            ],
        },
    },
    {
        "id": "kg_train_07",
        "scope": "document",
        "question": "平台为什么需要支持自动生成图表或文档？",
        "answer": "图表和文档生成是知识服务的输出层，可以把问答中沉淀的结构化知识转成技术路线图、对比表、总结报告等交付物。",
        "evidence": evidence("p0003_c002", "p0010_c004", "p0038_c002"),
        "graph_delta": {
            "nodes": [
                ["chart_generation", "Task", "图表生成"],
                ["report_generation", "Task", "文档生成"],
                ["deliverable", "Concept", "交付物"],
            ],
            "edges": [
                ["content_generation", "includes", "chart_generation"],
                ["content_generation", "includes", "report_generation"],
                ["chart_generation", "produces", "deliverable"],
                ["report_generation", "produces", "deliverable"],
            ],
        },
    },
    {
        "id": "kg_train_08",
        "scope": "document",
        "question": "企业场景下 DeepDoc 的典型用途是什么？",
        "answer": "企业场景更关注合同审查、制度文档问答、知识资产沉淀和多源资料整合，DeepDoc 可以把分散文档变成可检索、可追溯、可生成的知识资源。",
        "evidence": evidence("p0003_c002", "p0007_c007", "p0034_c003"),
        "graph_delta": {
            "nodes": [
                ["enterprise_scenario", "Scenario", "企业场景"],
                ["contract_review", "Task", "合同审查"],
                ["knowledge_asset", "Concept", "知识资产"],
                ["multi_source_integration", "Capability", "多源资料整合"],
            ],
            "edges": [
                ["deepdoc", "applies_to", "enterprise_scenario"],
                ["enterprise_scenario", "needs", "contract_review"],
                ["enterprise_scenario", "needs", "knowledge_asset"],
                ["deepdoc", "supports", "multi_source_integration"],
            ],
        },
    },
    {
        "id": "kg_train_09",
        "scope": "document",
        "question": "教育场景下知识图谱有什么价值？",
        "answer": "教育场景中，知识图谱可以把课程文档、论文、知识点和学习路径连接起来，用于文献研读、课程知识组织和个性化问答。",
        "evidence": evidence("p0003_c002", "p0034_c006", "p0038_c004"),
        "graph_delta": {
            "nodes": [
                ["education_scenario", "Scenario", "教育场景"],
                ["literature_reading", "Task", "文献研读"],
                ["course_knowledge_graph", "Task", "课程知识图谱"],
                ["learning_path", "Concept", "学习路径"],
            ],
            "edges": [
                ["deepdoc", "applies_to", "education_scenario"],
                ["education_scenario", "needs", "literature_reading"],
                ["education_scenario", "needs", "course_knowledge_graph"],
                ["course_knowledge_graph", "organizes", "learning_path"],
            ],
        },
    },
    {
        "id": "kg_train_10",
        "scope": "document",
        "question": "问题驱动图谱和一次性全文图谱有什么区别？",
        "answer": "问题驱动图谱围绕用户提问逐步扩展，只沉淀被问题触发且有证据支撑的知识关系；一次性全文图谱容易把章节和 chunk 结构全部画出来，造成认知噪声。",
        "evidence": evidence("p0010_c002", "p0024_c006", "p0032_c009"),
        "graph_delta": {
            "nodes": [
                ["question_driven_kg", "Method", "问题驱动知识图谱"],
                ["full_document_graph", "Method", "一次性全文图谱"],
                ["cognitive_noise", "Problem", "认知噪声"],
            ],
            "edges": [
                ["question_driven_kg", "expands_by", "user_question"],
                ["question_driven_kg", "filters", "cognitive_noise"],
                ["full_document_graph", "causes", "cognitive_noise"],
                ["question_driven_kg", "compared_with", "full_document_graph"],
            ],
        },
    },
]

TEST_QA: list[dict[str, Any]] = [
    {
        "id": "kg_test_01",
        "scope": "cross_document_or_project",
        "question": "如果我要生成一张 DeepDoc 技术路线图，图谱能提供哪些节点和关系？",
        "answer": "应复用 DeepDoc、文档解析、布局感知检索、RAG、知识图谱、证据溯源和内容生成等节点，并用 uses、supports、requires、produces 等关系组织成路线图。",
        "evidence": evidence("p0003_c002", "p0010_c001", "p0010_c002", "p0010_c004"),
        "expected_decision": "merge",
        "proposed_delta": {
            "nodes": [["technical_roadmap", "Deliverable", "技术路线图"]],
            "edges": [
                ["chart_generation", "produces", "technical_roadmap"],
                ["technical_roadmap", "uses", "question_driven_kg"],
            ],
        },
    },
    {
        "id": "kg_test_02",
        "scope": "document",
        "question": "用户追问 LAD-RAG 与传统 RAG 的区别时，是否应该新增图谱节点？",
        "answer": "不应重复新增 LAD、传统 RAG、扁平切块等已有节点，应该合并到已有实体，并补充“LAD-RAG 减少上下文碎片化”的关系。",
        "evidence": evidence("p0010_c001", "p0024_c004", "p0025_c002"),
        "expected_decision": "merge",
        "proposed_delta": {
            "nodes": [["lad_rag", "Method", "LAD-RAG"]],
            "edges": [
                ["lad_rag", "uses", "lad"],
                ["lad_rag", "uses", "rag"],
                ["lad_rag", "reduces", "context_fragmentation"],
                ["lad_rag", "compared_with", "traditional_rag"],
            ],
        },
    },
    {
        "id": "kg_test_03",
        "scope": "project_generation",
        "question": "生成项目总结文档时，图谱是否应该引入章节和 chunk 作为主节点？",
        "answer": "不应该。章节和 chunk 应作为证据来源保留，主图谱仍应围绕系统、方法、问题、场景和交付物组织，否则会退化成结构图。",
        "evidence": evidence("p0036_c001", "p0038_c002", "p0038_c004"),
        "expected_decision": "reject_structural_nodes",
        "proposed_delta": {
            "nodes": [["section_nodes", "Structure", "章节节点"], ["chunk_nodes", "Structure", "Chunk 节点"]],
            "edges": [
                ["report_generation", "should_not_use_as_main_node", "section_nodes"],
                ["report_generation", "should_not_use_as_main_node", "chunk_nodes"],
            ],
        },
    },
]


def load_chunk_index() -> dict[str, dict[str, Any]]:
    if not LAD_CHUNK_PATH.exists():
        return {}
    payload = json.loads(LAD_CHUNK_PATH.read_text(encoding="utf-8"))
    chunks = payload.get("chunks") if isinstance(payload.get("chunks"), list) else []
    index: dict[str, dict[str, Any]] = {}
    for chunk in chunks:
        cid = str(chunk.get("chunkId") or "")
        if not cid:
            continue
        text = (
            chunk.get("normalizedContent")
            or chunk.get("cleanText")
            or chunk.get("content")
            or ""
        )
        index[cid] = {
            "pageNo": chunk.get("pageNo"),
            "sectionId": chunk.get("sectionId"),
            "sectionTitle": chunk.get("sectionTitle"),
            "textPreview": str(text).replace("\n", " ")[:240],
        }
    return index


def enrich_evidence(items: list[dict[str, Any]], chunk_index: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    enriched = []
    for item in items:
        cid = item.get("chunkId")
        extra = chunk_index.get(str(cid), {})
        enriched.append({**item, **extra})
    return enriched


def add_node(graph: dict[str, Any], node_id: str, node_type: str, label: str, source_qa: str, evidence_items: list[dict[str, Any]]) -> None:
    existing = graph["nodes"].setdefault(
        node_id,
        {
            "id": node_id,
            "type": node_type,
            "label": label,
            "aliases": [],
            "sourceQaIds": [],
            "evidence": [],
            "confidence": 0.75,
        },
    )
    if source_qa not in existing["sourceQaIds"]:
        existing["sourceQaIds"].append(source_qa)
    existing["evidence"].extend(evidence_items)


def add_edge(graph: dict[str, Any], source: str, relation: str, target: str, source_qa: str, evidence_items: list[dict[str, Any]]) -> None:
    edge_id = f"{source}::{relation}::{target}"
    existing = graph["edges"].setdefault(
        edge_id,
        {
            "id": edge_id,
            "source": source,
            "relation": relation,
            "target": target,
            "sourceQaIds": [],
            "evidence": [],
            "confidence": 0.72,
        },
    )
    if source_qa not in existing["sourceQaIds"]:
        existing["sourceQaIds"].append(source_qa)
    existing["evidence"].extend(evidence_items)


def build_graph(train_qa: list[dict[str, Any]], chunk_index: dict[str, dict[str, Any]]) -> dict[str, Any]:
    graph: dict[str, Any] = {
        "metadata": {
            "projectId": PROJECT_ID,
            "sourceDocId": DOC_ID,
            "sourceDocName": DOC_NAME,
            "mode": "question_driven_incremental_kg",
            "structuralPolicy": "Section/Chunk are evidence only, not main graph nodes.",
            "generatedAt": datetime.now().isoformat(timespec="seconds"),
            "trainQaCount": len(train_qa),
        },
        "nodes": {},
        "edges": {},
        "buildLog": [],
    }

    add_node(graph, "user_question", "Interaction", "用户问题", "system", [])

    for qa in train_qa:
        ev = enrich_evidence(qa["evidence"], chunk_index)
        for node_id, node_type, label in qa["graph_delta"]["nodes"]:
            add_node(graph, node_id, node_type, label, qa["id"], ev)
        for source, relation, target in qa["graph_delta"]["edges"]:
            add_edge(graph, source, relation, target, qa["id"], ev)
        graph["buildLog"].append(
            {
                "qaId": qa["id"],
                "question": qa["question"],
                "addedNodeCandidates": len(qa["graph_delta"]["nodes"]),
                "addedEdgeCandidates": len(qa["graph_delta"]["edges"]),
            }
        )

    graph["nodes"] = list(graph["nodes"].values())
    graph["edges"] = list(graph["edges"].values())
    graph["metadata"]["nodeCount"] = len(graph["nodes"])
    graph["metadata"]["edgeCount"] = len(graph["edges"])
    return graph


def evaluate_tests(graph: dict[str, Any], test_qa: list[dict[str, Any]], chunk_index: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    node_ids = {n["id"] for n in graph["nodes"]}
    edge_ids = {e["id"] for e in graph["edges"]}
    results = []
    for qa in test_qa:
        proposed_nodes = qa["proposed_delta"]["nodes"]
        proposed_edges = qa["proposed_delta"]["edges"]
        new_nodes = [n for n in proposed_nodes if n[0] not in node_ids]
        reused_nodes = [n for n in proposed_nodes if n[0] in node_ids]
        new_edges = [
            e for e in proposed_edges if f"{e[0]}::{e[1]}::{e[2]}" not in edge_ids
        ]
        structural_nodes = [n for n in proposed_nodes if n[1] in {"Structure", "Section", "Chunk", "Document"}]
        if structural_nodes:
            decision = "reject_structural_nodes"
            rationale = "测试输入试图把章节或 chunk 作为主图谱节点；这会让问题驱动 KG 退化成结构图，应拒绝进入主图，只保留为证据。"
        elif reused_nodes or any(e[0] in node_ids or e[2] in node_ids for e in proposed_edges):
            decision = "merge"
            rationale = "测试问答能复用已有节点，并新增少量与生成任务或 LAD-RAG 相关的语义关系，适合合入项目级图谱。"
        else:
            decision = "add"
            rationale = "测试问答提出了新主题，且没有结构节点污染，可作为新知识簇加入。"

        results.append(
            {
                "qaId": qa["id"],
                "question": qa["question"],
                "expectedDecision": qa["expected_decision"],
                "actualDecision": decision,
                "isReasonable": decision == qa["expected_decision"],
                "newNodeCandidates": [n[0] for n in new_nodes],
                "reusedNodeCandidates": [n[0] for n in reused_nodes],
                "newEdgeCandidates": [f"{s}::{r}::{t}" for s, r, t in new_edges],
                "structuralNodeCandidates": [n[0] for n in structural_nodes],
                "rationale": rationale,
                "evidence": enrich_evidence(qa["evidence"], chunk_index),
            }
        )
    return results


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_report(path: Path, graph: dict[str, Any], results: list[dict[str, Any]]) -> None:
    node_types = Counter(n["type"] for n in graph["nodes"])
    rel_types = Counter(e["relation"] for e in graph["edges"])
    lines = [
        "# KG Question-Driven Test Integration Report",
        "",
        f"- Project: `{PROJECT_ID}`",
        f"- Source document: `{DOC_ID}`",
        f"- Training QA: `{graph['metadata']['trainQaCount']}`",
        f"- Graph nodes: `{graph['metadata']['nodeCount']}`",
        f"- Graph edges: `{graph['metadata']['edgeCount']}`",
        "- Structural policy: `Section/Chunk are evidence only, not main graph nodes.`",
        "",
        "## Node Types",
        "",
    ]
    for key, count in node_types.most_common():
        lines.append(f"- `{key}`: {count}")
    lines.extend(["", "## Relation Types", ""])
    for key, count in rel_types.most_common():
        lines.append(f"- `{key}`: {count}")
    lines.extend(["", "## Test Decisions", ""])
    for item in results:
        lines.extend(
            [
                f"### {item['qaId']}",
                "",
                f"- Question: {item['question']}",
                f"- Expected: `{item['expectedDecision']}`",
                f"- Actual: `{item['actualDecision']}`",
                f"- Reasonable: `{item['isReasonable']}`",
                f"- New nodes: `{', '.join(item['newNodeCandidates']) or 'none'}`",
                f"- Reused nodes: `{', '.join(item['reusedNodeCandidates']) or 'none'}`",
                f"- Structural nodes rejected: `{', '.join(item['structuralNodeCandidates']) or 'none'}`",
                f"- Rationale: {item['rationale']}",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_preview(path: Path, graph: dict[str, Any]) -> None:
    nodes = graph["nodes"]
    edges = graph["edges"]
    type_color = {
        "System": "#4e79a7",
        "Method": "#e15759",
        "Capability": "#59a14f",
        "Problem": "#f28e2c",
        "Task": "#b07aa1",
        "Concept": "#76b7b2",
        "Metric": "#edc948",
        "Scenario": "#9c755f",
        "Evidence": "#86bcb6",
        "Deliverable": "#ff9da7",
        "Interaction": "#bab0ac",
    }
    node_lookup = {node["id"]: node for node in nodes}
    visible_edges = [e for e in edges if e["source"] in node_lookup and e["target"] in node_lookup]
    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Question Driven KG</title>
  <style>
    body {{ margin: 0; font-family: system-ui, -apple-system, "Microsoft YaHei", sans-serif; background: #0f172a; color: #e5e7eb; }}
    .layout {{ display: grid; grid-template-columns: 320px 1fr; min-height: 100vh; }}
    aside {{ border-right: 1px solid #334155; background: #111827; padding: 18px; overflow: auto; }}
    h1 {{ font-size: 18px; color: #93c5fd; margin: 0 0 12px; }}
    .stat {{ color: #cbd5e1; margin: 6px 0; }}
    .legend {{ display: grid; gap: 6px; margin-top: 18px; }}
    .legend span {{ display: flex; gap: 8px; align-items: center; font-size: 13px; }}
    .dot {{ width: 10px; height: 10px; border-radius: 50%; display: inline-block; }}
    main {{ padding: 24px; overflow: auto; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(210px, 1fr)); gap: 12px; }}
    .node {{ border: 1px solid #334155; background: #1f2937; border-radius: 8px; padding: 12px; min-height: 86px; }}
    .node strong {{ display: block; color: #fff; margin-bottom: 6px; }}
    .node small {{ color: #94a3b8; }}
    .edges {{ margin-top: 24px; display: grid; gap: 8px; }}
    .edge {{ border: 1px solid #263244; background: #111827; border-radius: 6px; padding: 8px 10px; font-size: 13px; }}
    code {{ color: #93c5fd; }}
  </style>
</head>
<body>
  <div class="layout">
    <aside>
      <h1>问题驱动知识图谱</h1>
      <div class="stat">Nodes: <code>{len(nodes)}</code></div>
      <div class="stat">Edges: <code>{len(visible_edges)}</code></div>
      <div class="stat">Source doc: <code>{DOC_ID}</code></div>
      <div class="legend">
        {''.join(f'<span><i class="dot" style="background:{color}"></i>{escape(t)}</span>' for t, color in type_color.items())}
      </div>
    </aside>
    <main>
      <section class="grid">
        {''.join(f'<article class="node" style="border-color:{type_color.get(n["type"], "#64748b")}"><strong>{escape(n["label"])}</strong><small>{escape(n["type"])} · {escape(n["id"])}</small></article>' for n in nodes)}
      </section>
      <section class="edges">
        {''.join(f'<div class="edge"><code>{escape(node_lookup[e["source"]]["label"])}</code> -- {escape(e["relation"])} --&gt; <code>{escape(node_lookup[e["target"]]["label"])}</code></div>' for e in visible_edges)}
      </section>
    </main>
  </div>
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")


def write_graph_preview(path: Path, graph: dict[str, Any]) -> None:
    """Write a standalone SVG graph preview for the question-driven KG."""
    import math

    nodes = graph["nodes"]
    edges = graph["edges"]
    type_color = {
        "System": "#4e79a7",
        "Method": "#e15759",
        "Capability": "#59a14f",
        "Problem": "#f28e2c",
        "Task": "#b07aa1",
        "Concept": "#76b7b2",
        "Metric": "#edc948",
        "Scenario": "#9c755f",
        "Evidence": "#86bcb6",
        "Deliverable": "#ff9da7",
        "Interaction": "#bab0ac",
    }
    node_lookup = {node["id"]: node for node in nodes}
    visible_edges = [edge for edge in edges if edge["source"] in node_lookup and edge["target"] in node_lookup]
    node_types = Counter(node["type"] for node in nodes)
    rel_types = Counter(edge["relation"] for edge in visible_edges)

    width = 1500
    height = 960
    cx = 760
    cy = 470
    groups = list(node_types.keys())
    positions: dict[str, tuple[float, float]] = {}
    for index, node in enumerate(nodes):
        group_index = groups.index(node["type"])
        radius = 135 + (group_index % 4) * 82
        angle = (index / max(1, len(nodes))) * math.tau + group_index * 0.42
        positions[node["id"]] = (cx + math.cos(angle) * radius, cy + math.sin(angle) * radius)

    for _ in range(120):
        displacement = {node["id"]: [0.0, 0.0] for node in nodes}
        for a_index, a in enumerate(nodes):
            ax, ay = positions[a["id"]]
            for b in nodes[a_index + 1 :]:
                bx, by = positions[b["id"]]
                dx = bx - ax
                dy = by - ay
                dist_sq = dx * dx + dy * dy or 1.0
                dist = math.sqrt(dist_sq)
                force = min(1300 / dist_sq, 1.6)
                ux = dx / dist
                uy = dy / dist
                displacement[a["id"]][0] -= ux * force
                displacement[a["id"]][1] -= uy * force
                displacement[b["id"]][0] += ux * force
                displacement[b["id"]][1] += uy * force
        for edge in visible_edges:
            sx, sy = positions[edge["source"]]
            tx, ty = positions[edge["target"]]
            dx = tx - sx
            dy = ty - sy
            dist = math.sqrt(dx * dx + dy * dy) or 1.0
            force = (dist - 150) * 0.012
            ux = dx / dist
            uy = dy / dist
            displacement[edge["source"]][0] += ux * force
            displacement[edge["source"]][1] += uy * force
            displacement[edge["target"]][0] -= ux * force
            displacement[edge["target"]][1] -= uy * force
        for node in nodes:
            x, y = positions[node["id"]]
            dx, dy = displacement[node["id"]]
            x += dx + (cx - x) * 0.01
            y += dy + (cy - y) * 0.01
            positions[node["id"]] = (x, y)

    edge_svg = []
    edge_label_svg = []
    for edge in visible_edges:
        sx, sy = positions[edge["source"]]
        tx, ty = positions[edge["target"]]
        mx = (sx + tx) / 2
        my = (sy + ty) / 2
        edge_svg.append(
            f'<line class="edge" x1="{sx:.1f}" y1="{sy:.1f}" x2="{tx:.1f}" y2="{ty:.1f}">'
            f'<title>{escape(node_lookup[edge["source"]]["label"])} -- {escape(edge["relation"])} --> {escape(node_lookup[edge["target"]]["label"])}</title>'
            "</line>"
        )
        edge_label_svg.append(
            f'<text class="edge-label" x="{mx:.1f}" y="{my:.1f}">{escape(edge["relation"])}</text>'
        )

    node_svg = []
    for node in nodes:
        x, y = positions[node["id"]]
        label = node["label"]
        short = label if len(label) <= 14 else label[:13] + "..."
        evidence = node.get("evidence") or []
        evidence_text = "; ".join(str(item.get("chunkId", "")) for item in evidence[:4])
        node_svg.append(
            f'<g class="node">'
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{18 if node["type"] == "System" else 14}" fill="{type_color.get(node["type"], "#64748b")}">'
            f'<title>{escape(label)}\nType: {escape(node["type"])}\nSource QA: {escape(", ".join(node.get("sourceQaIds", [])))}\nEvidence: {escape(evidence_text)}</title>'
            f'</circle><text x="{x:.1f}" y="{y - 22:.1f}">{escape(short)}</text></g>'
        )

    node_legend = "".join(
        f'<span><i style="background:{type_color.get(t, "#64748b")}"></i>{escape(t)} ({count})</span>'
        for t, count in node_types.most_common()
    )
    rel_legend = "".join(f"<span>{escape(t)} ({count})</span>" for t, count in rel_types.most_common())
    edge_list = "".join(
        f'<div class="row"><code>{escape(node_lookup[e["source"]]["label"])}</code> '
        f'<b>{escape(e["relation"])}</b> <code>{escape(node_lookup[e["target"]]["label"])}</code></div>'
        for e in visible_edges
    )

    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>KG Question Driven Graph</title>
  <style>
    body {{ margin:0; background:#0f172a; color:#e5e7eb; font-family:system-ui,-apple-system,"Microsoft YaHei",sans-serif; }}
    .layout {{ display:grid; grid-template-columns:300px minmax(900px,1fr) 360px; height:100vh; }}
    aside,.side {{ background:#111827; border-color:#334155; padding:18px; overflow:auto; }}
    aside {{ border-right:1px solid #334155; }}
    .side {{ border-left:1px solid #334155; }}
    h1 {{ margin:0 0 12px; color:#93c5fd; font-size:18px; }}
    h2 {{ margin:20px 0 8px; color:#bfdbfe; font-size:14px; }}
    .stat {{ margin:6px 0; color:#cbd5e1; font-size:13px; }}
    .legend {{ display:grid; gap:7px; }}
    .legend span {{ display:flex; align-items:center; gap:8px; color:#cbd5e1; font-size:13px; }}
    .legend i {{ width:10px; height:10px; border-radius:50%; display:inline-block; }}
    main {{ overflow:auto; background:radial-gradient(circle at center,#14213d 0,#0f172a 48%,#0b1020 100%); }}
    svg {{ min-width:{width}px; min-height:{height}px; display:block; }}
    .edge {{ stroke:#64748b; stroke-opacity:.44; stroke-width:1.35; }}
    .edge-label {{ fill:#94a3b8; font-size:10px; text-anchor:middle; paint-order:stroke; stroke:#0f172a; stroke-width:4px; }}
    .node circle {{ stroke:#0f172a; stroke-width:2.2px; }}
    .node text {{ fill:#e5e7eb; font-size:11px; text-anchor:middle; paint-order:stroke; stroke:#0f172a; stroke-width:4px; }}
    .row {{ border:1px solid #263244; background:#0f172a; border-radius:7px; padding:8px; margin:8px 0; font-size:12px; line-height:1.45; }}
    code {{ color:#93c5fd; }}
    b {{ color:#fbbf24; font-weight:600; }}
  </style>
</head>
<body>
  <div class="layout">
    <aside>
      <h1>问题驱动知识图谱</h1>
      <div class="stat">Nodes: <code>{len(nodes)}</code></div>
      <div class="stat">Edges: <code>{len(visible_edges)}</code></div>
      <div class="stat">Source doc: <code>{DOC_ID}</code></div>
      <h2>节点类型</h2>
      <div class="legend">{node_legend}</div>
      <h2>关系类型</h2>
      <div class="legend">{rel_legend}</div>
    </aside>
    <main>
      <svg viewBox="0 0 {width} {height}" role="img" aria-label="问题驱动知识图谱">
        <g>{''.join(edge_svg)}</g>
        <g>{''.join(edge_label_svg)}</g>
        <g>{''.join(node_svg)}</g>
      </svg>
    </main>
    <section class="side">
      <h1>语义关系</h1>
      {edge_list}
    </section>
  </div>
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")


def write_query_centered_preview(path: Path, graph: dict[str, Any]) -> None:
    """Write an interactive query/entity-centered subgraph preview."""
    nodes = graph["nodes"]
    edges = graph["edges"]
    type_color = {
        "System": "#4e79a7",
        "Method": "#e15759",
        "Capability": "#59a14f",
        "Problem": "#f28e2c",
        "Task": "#b07aa1",
        "Concept": "#76b7b2",
        "Metric": "#edc948",
        "Scenario": "#9c755f",
        "Evidence": "#86bcb6",
        "Deliverable": "#ff9da7",
        "Interaction": "#bab0ac",
    }
    node_lookup = {node["id"]: node for node in nodes}
    visible_edges = [edge for edge in edges if edge["source"] in node_lookup and edge["target"] in node_lookup]
    node_types = Counter(node["type"] for node in nodes)
    rel_types = Counter(edge["relation"] for edge in visible_edges)
    default_center = "deepdoc" if "deepdoc" in node_lookup else nodes[0]["id"]

    html = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>KG Query Centered Graph</title>
  <style>
    :root {
      --bg-page: #f7f8fa;
      --surface: #ffffff;
      --surface-muted: #fafafa;
      --accent: #4a6fa5;
      --accent-hover: #5a7fb5;
      --accent-soft: rgba(74, 111, 165, 0.12);
      --accent-ring: rgba(74, 111, 165, 0.22);
      --btn-primary-bg: #1a1d24;
      --btn-primary-hover: #2a2f3a;
      --btn-secondary-bg: #eceef2;
      --btn-secondary-hover: #e0e3e9;
      --border-subtle: #eeeeee;
      --border-input: #e5e5e5;
      --text-title: #111111;
      --text-body: #333333;
      --text-muted: #888888;
      --radius-control: 12px;
      --radius-btn: 11px;
      --shadow-float: 0 2px 8px rgba(0, 0, 0, 0.04);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--bg-page);
      color: var(--text-body);
      font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, "PingFang SC", "Microsoft YaHei", sans-serif;
      overflow: hidden;
      -webkit-font-smoothing: antialiased;
    }
    .app-shell { height: 100vh; display: flex; flex-direction: column; overflow: hidden; }
    .topbar {
      height: 56px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 16px;
      background: rgba(255,255,255,.88);
      border-bottom: 1px solid var(--border-subtle);
      backdrop-filter: blur(10px);
      box-shadow: 0 1px 0 rgba(0,0,0,.03);
      flex: 0 0 auto;
    }
    .brand { display: flex; align-items: center; gap: 12px; }
    .brand-icon {
      width: 36px; height: 36px; border-radius: var(--radius-control);
      background: var(--btn-primary-bg); color: #fff; display: grid; place-items: center;
      font-size: 14px; box-shadow: var(--shadow-float);
    }
    .brand-title { font-weight: 700; font-size: 15px; color: var(--text-title); line-height: 1.15; }
    .brand-subtitle { font-size: 12px; color: var(--text-muted); margin-top: 3px; font-weight: 500; }
    .layout { display:grid; grid-template-columns:320px minmax(0, 1fr) 360px; min-height:0; flex:1; }
    aside,.detail {
      background: var(--surface);
      padding: 18px;
      overflow: auto;
      border-color: var(--border-subtle);
    }
    aside { border-right:1px solid var(--border-subtle); }
    .detail { border-left:1px solid var(--border-subtle); }
    h1 { margin:0 0 12px; color: var(--text-title); font-size:16px; font-weight:700; }
    h2 { margin:18px 0 8px; color: var(--text-title); font-size:13px; font-weight:700; }
    .stat { margin:6px 0; color: var(--text-muted); font-size:13px; }
    .hint { color: var(--text-muted); font-size:12px; line-height:1.55; margin:10px 0; }
    input,select {
      width:100%; padding:10px 12px; margin:6px 0;
      border:1px solid var(--border-input); border-radius:var(--radius-control);
      background: var(--surface); color: var(--text-body); outline: none;
      font: inherit; font-size: 13px;
    }
    input:focus, select:focus { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-ring); }
    button {
      background: var(--btn-secondary-bg); color: var(--text-body);
      border:1px solid var(--border-subtle); border-radius:var(--radius-btn);
      padding:10px 14px; cursor:pointer; font-weight:600; font-size:13px;
      transition: background .2s ease, border-color .2s ease, transform .2s ease;
    }
    button:hover { background: var(--btn-secondary-hover); transform: translateY(-1px); }
    .actions { display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-top:8px; }
    #btnSearch, #btnCore { background: var(--btn-primary-bg); color: #fff; border-color: var(--btn-primary-bg); }
    #btnSearch:hover, #btnCore:hover { background: var(--btn-primary-hover); }
    .chips { display:flex; gap:6px; flex-wrap:wrap; margin-top:8px; }
    .chip {
      padding:5px 9px; border:1px solid var(--border-subtle); border-radius:999px;
      font-size:12px; color: var(--text-body); background: var(--surface-muted);
    }
    .chip:hover { border-color: var(--accent); color: var(--accent); cursor:pointer; }
    .legend { display:grid; gap:6px; margin-top:8px; }
    .legend span { display:flex; gap:8px; align-items:center; font-size:13px; color: var(--text-body); }
    .legend i { width:10px; height:10px; border-radius:50%; display:inline-block; box-shadow: inset 0 0 0 1px rgba(0,0,0,.08); }
    main { position:relative; min-width:0; background: linear-gradient(180deg, #ffffff 0%, #fafafa 100%); overflow: hidden; }
    svg { display:block; width:100%; height:100%; cursor:grab; }
    svg.dragging { cursor:grabbing; }
    .toolbar { position:absolute; left:16px; top:16px; display:flex; gap:8px; z-index: 2; }
    .badge {
      position:absolute; right:16px; top:16px; padding:8px 10px;
      border:1px solid var(--border-subtle); border-radius:var(--radius-control);
      background: rgba(255,255,255,.88); color: var(--text-muted); font-size:12px;
      box-shadow: var(--shadow-float); z-index: 2;
    }
    .edge { stroke:#c7ccd6; stroke-opacity:.72; stroke-width:1.45; }
    .edge.focus { stroke:var(--accent); stroke-opacity:.95; stroke-width:2.4; }
    .edge-label { fill:#6b7280; font-size:10px; pointer-events:none; text-anchor:middle; paint-order:stroke; stroke:#fff; stroke-width:4px; }
    .node circle { stroke:#fff; stroke-width:2.4px; cursor:pointer; filter: drop-shadow(0 2px 4px rgba(0,0,0,.12)); }
    .node.center circle { stroke:var(--accent); stroke-width:4px; }
    .node.selected circle { stroke:var(--btn-primary-bg); stroke-width:3px; }
    .node text { fill:var(--text-title); font-size:11px; font-weight:600; text-anchor:middle; pointer-events:none; paint-order:stroke; stroke:#fff; stroke-width:4px; }
    .item { border:1px solid var(--border-subtle); background: var(--surface-muted); border-radius:8px; padding:8px; margin:8px 0; font-size:12px; line-height:1.5; }
    code { color:var(--accent); font-family: ui-monospace, SFMono-Regular, Consolas, monospace; }
    b { color:var(--text-title); font-weight:700; }
    .muted { color:var(--text-muted); }
  </style>
</head>
<body>
  <div class="layout">
    <aside>
      <h1>查询中心图谱</h1>
      <div class="stat">全量节点: <code>__NODE_COUNT__</code></div>
      <div class="stat">全量关系: <code>__EDGE_COUNT__</code></div>
      <div class="hint">输入问题或实体名后，只展示匹配实体及其一跳/二跳邻居。点击图中节点会以该节点为中心重新展开。</div>
      <input id="queryInput" placeholder="例如：LAD-RAG、传统 RAG、图表生成" />
      <select id="hopSelect">
        <option value="1">展开一跳关系</option>
        <option value="2" selected>展开二跳关系</option>
      </select>
      <div class="actions">
        <button id="btnSearch" type="button">查询</button>
        <button id="btnCore" type="button">核心图</button>
      </div>
      <h2>推荐入口</h2>
      <div class="chips" id="chips"></div>
      <h2>节点类型</h2>
      <div class="legend">__NODE_LEGEND__</div>
      <h2>关系类型</h2>
      <div class="legend">__REL_LEGEND__</div>
    </aside>
    <main>
      <div class="toolbar">
        <button id="btnFit" type="button">适配</button>
        <button id="btnReset" type="button">重排</button>
      </div>
      <div class="badge" id="subgraphBadge"></div>
      <svg id="graphSvg"></svg>
    </main>
    <section class="detail" id="detail">
      <h1>当前子图</h1>
      <div class="muted">选择一个入口实体或输入查询。</div>
    </section>
  </div>
  <script>
    const allNodes = __NODES_JSON__;
    const allEdges = __EDGES_JSON__;
    const colors = __COLORS_JSON__;
    const defaultCenter = "__DEFAULT_CENTER__";
    const nodeById = new Map(allNodes.map(n => [n.id, n]));
    const adj = new Map();
    allEdges.forEach(edge => {
      if (!adj.has(edge.source)) adj.set(edge.source, []);
      if (!adj.has(edge.target)) adj.set(edge.target, []);
      adj.get(edge.source).push(edge);
      adj.get(edge.target).push(edge);
    });

    const svg = document.getElementById("graphSvg");
    const detail = document.getElementById("detail");
    const badge = document.getElementById("subgraphBadge");
    const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
    const edgeLayer = document.createElementNS("http://www.w3.org/2000/svg", "g");
    const labelLayer = document.createElementNS("http://www.w3.org/2000/svg", "g");
    const nodeLayer = document.createElementNS("http://www.w3.org/2000/svg", "g");
    g.append(edgeLayer, labelLayer, nodeLayer);
    svg.appendChild(g);

    let width = 1, height = 1;
    let viewNodes = [], viewEdges = [];
    let centerId = defaultCenter;
    let selectedId = null;
    let transform = { x: 0, y: 0, scale: 1 };
    let panning = false, draggingNode = null, last = { x: 0, y: 0 };

    const chipIds = ["deepdoc", "rag", "lad", "knowledge_graph", "question_driven_kg", "chart_generation", "cross_document_qa"];
    const chips = document.getElementById("chips");
    chipIds.filter(id => nodeById.has(id)).forEach(id => {
      const item = document.createElement("span");
      item.className = "chip";
      item.textContent = nodeById.get(id).label;
      item.onclick = () => setCenter(id, Number(document.getElementById("hopSelect").value));
      chips.appendChild(item);
    });

    function subgraphFromCenter(id, hops) {
      const ids = new Set([id]);
      let frontier = new Set([id]);
      for (let step = 0; step < hops; step++) {
        const next = new Set();
        frontier.forEach(nodeId => {
          (adj.get(nodeId) || []).forEach(edge => {
            const other = edge.source === nodeId ? edge.target : edge.source;
            ids.add(other);
            next.add(other);
          });
        });
        frontier = next;
      }
      const nodes = allNodes.filter(node => ids.has(node.id));
      const nodeSet = new Set(nodes.map(node => node.id));
      const edges = allEdges.filter(edge => nodeSet.has(edge.source) && nodeSet.has(edge.target));
      return { nodes, edges };
    }

    function searchBest(query) {
      const q = query.trim().toLowerCase();
      if (!q) return defaultCenter;
      const exact = allNodes.find(node => node.label.toLowerCase() === q || node.id.toLowerCase() === q);
      if (exact) return exact.id;
      const partial = allNodes.find(node => node.label.toLowerCase().includes(q) || node.id.toLowerCase().includes(q));
      return partial ? partial.id : defaultCenter;
    }

    function setCenter(id, hops) {
      centerId = id;
      selectedId = id;
      const sub = subgraphFromCenter(id, hops);
      viewNodes = sub.nodes.map(node => ({ ...node }));
      viewEdges = sub.edges;
      layout();
      render();
      fitView();
      showDetail(nodeById.get(id));
      badge.textContent = `${nodeById.get(id).label} · ${viewNodes.length} nodes · ${viewEdges.length} edges`;
    }

    function showCore() {
      const core = ["deepdoc", "document_parsing", "rag", "lad", "knowledge_graph", "evidence_traceability", "content_generation", "chart_generation", "report_generation"].filter(id => nodeById.has(id));
      const coreSet = new Set(core);
      viewNodes = allNodes.filter(node => coreSet.has(node.id)).map(node => ({ ...node }));
      viewEdges = allEdges.filter(edge => coreSet.has(edge.source) && coreSet.has(edge.target));
      centerId = "deepdoc";
      selectedId = "deepdoc";
      layout();
      render();
      fitView();
      showDetail(nodeById.get(centerId));
      badge.textContent = `核心图 · ${viewNodes.length} nodes · ${viewEdges.length} edges`;
    }

    function layout() {
      const local = new Map(viewNodes.map(node => [node.id, node]));
      viewNodes.forEach((node, index) => {
        const angle = index / Math.max(1, viewNodes.length) * Math.PI * 2;
        const ring = node.id === centerId ? 0 : 180 + (index % 3) * 70;
        node.x = width / 2 + Math.cos(angle) * ring;
        node.y = height / 2 + Math.sin(angle) * ring;
        node.vx = 0; node.vy = 0;
        node.r = node.id === centerId ? 21 : node.type === "Method" ? 16 : 14;
      });
      for (let i = 0; i < 180; i++) {
        viewNodes.forEach((a, ai) => {
          for (let bi = ai + 1; bi < viewNodes.length; bi++) {
            const b = viewNodes[bi];
            let dx = b.x - a.x, dy = b.y - a.y;
            let d2 = dx * dx + dy * dy || 1;
            let d = Math.sqrt(d2);
            let f = Math.min(1600 / d2, 1.8);
            dx /= d; dy /= d;
            a.vx -= dx * f; a.vy -= dy * f; b.vx += dx * f; b.vy += dy * f;
          }
        });
        viewEdges.forEach(edge => {
          const a = local.get(edge.source), b = local.get(edge.target);
          if (!a || !b) return;
          let dx = b.x - a.x, dy = b.y - a.y;
          let d = Math.sqrt(dx * dx + dy * dy) || 1;
          let f = (d - 145) * .016;
          dx /= d; dy /= d;
          a.vx += dx * f; a.vy += dy * f; b.vx -= dx * f; b.vy -= dy * f;
        });
        viewNodes.forEach(node => {
          node.vx += (width / 2 - node.x) * .004;
          node.vy += (height / 2 - node.y) * .004;
          if (node.id === centerId) {
            node.vx += (width / 2 - node.x) * .08;
            node.vy += (height / 2 - node.y) * .08;
          }
          node.x += node.vx; node.y += node.vy; node.vx *= .76; node.vy *= .76;
        });
      }
    }

    function render() {
      const local = new Map(viewNodes.map(node => [node.id, node]));
      edgeLayer.textContent = ""; labelLayer.textContent = ""; nodeLayer.textContent = "";
      viewEdges.forEach(edge => {
        const s = local.get(edge.source), t = local.get(edge.target);
        if (!s || !t) return;
        const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
        line.setAttribute("class", selectedId && (edge.source === selectedId || edge.target === selectedId) ? "edge focus" : "edge");
        line.setAttribute("x1", s.x); line.setAttribute("y1", s.y);
        line.setAttribute("x2", t.x); line.setAttribute("y2", t.y);
        edgeLayer.appendChild(line);
        const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
        label.setAttribute("class", "edge-label");
        label.setAttribute("x", (s.x + t.x) / 2);
        label.setAttribute("y", (s.y + t.y) / 2);
        label.textContent = edge.relation;
        labelLayer.appendChild(label);
      });
      viewNodes.forEach(node => {
        const item = document.createElementNS("http://www.w3.org/2000/svg", "g");
        item.setAttribute("class", `node ${node.id === centerId ? "center" : ""} ${node.id === selectedId ? "selected" : ""}`);
        item.setAttribute("transform", `translate(${node.x},${node.y})`);
        item.dataset.id = node.id;
        const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        circle.setAttribute("r", node.r);
        circle.setAttribute("fill", colors[node.type] || "#64748b");
        item.appendChild(circle);
        const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
        text.setAttribute("y", -(node.r + 8));
        text.textContent = node.label.length > 14 ? `${node.label.slice(0, 13)}...` : node.label;
        item.appendChild(text);
        nodeLayer.appendChild(item);
      });
      applyTransform();
    }

    function showDetail(node) {
      const relations = (adj.get(node.id) || []).filter(edge => viewEdges.includes(edge));
      const evidence = (node.evidence || []).slice(0, 5);
      detail.innerHTML = `
        <h1>${escapeHtml(node.label)}</h1>
        <div><span class="chip">${escapeHtml(node.type)}</span><span class="chip">${escapeHtml(node.id)}</span></div>
        <h2>来源问答</h2>
        ${(node.sourceQaIds || []).map(id => `<div class="item"><code>${escapeHtml(id)}</code></div>`).join("") || "<div class='muted'>无</div>"}
        <h2>当前子图关系</h2>
        ${relations.map(edge => {
          const otherId = edge.source === node.id ? edge.target : edge.source;
          const other = nodeById.get(otherId);
          const arrow = edge.source === node.id ? "→" : "←";
          return `<div class="item"><b>${escapeHtml(edge.relation)}</b> ${arrow} <code>${escapeHtml(other?.label || otherId)}</code></div>`;
        }).join("") || "<div class='muted'>无</div>"}
        <h2>证据 chunk</h2>
        ${evidence.map(ev => `<div class="item"><code>${escapeHtml(ev.chunkId || "")}</code> · page ${escapeHtml(String(ev.pageNo || ""))}<br>${escapeHtml(ev.textPreview || "")}</div>`).join("") || "<div class='muted'>无</div>"}
      `;
    }

    function escapeHtml(value) {
      return String(value).replace(/[&<>"']/g, ch => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]));
    }
    function point(event) { const r = svg.getBoundingClientRect(); return { x: event.clientX - r.left, y: event.clientY - r.top }; }
    function screenToWorld(p) { return { x: (p.x - transform.x) / transform.scale, y: (p.y - transform.y) / transform.scale }; }
    function applyTransform() { g.setAttribute("transform", `translate(${transform.x},${transform.y}) scale(${transform.scale})`); }
    function fitView() {
      if (!viewNodes.length) return;
      const xs = viewNodes.map(n => n.x), ys = viewNodes.map(n => n.y);
      const minX = Math.min(...xs), maxX = Math.max(...xs), minY = Math.min(...ys), maxY = Math.max(...ys);
      const pad = 110;
      transform.scale = Math.max(.25, Math.min(width / (maxX - minX + pad * 2), height / (maxY - minY + pad * 2), 1.5));
      transform.x = width / 2 - ((minX + maxX) / 2) * transform.scale;
      transform.y = height / 2 - ((minY + maxY) / 2) * transform.scale;
      applyTransform();
    }

    svg.addEventListener("mousedown", event => {
      const target = event.target.closest(".node");
      last = point(event);
      if (target) {
        const id = target.dataset.id;
        const node = viewNodes.find(n => n.id === id);
        draggingNode = node;
        selectedId = id;
        showDetail(nodeById.get(id));
        render();
      } else {
        panning = true;
        svg.classList.add("dragging");
      }
    });
    window.addEventListener("mousemove", event => {
      const p = point(event);
      if (draggingNode) {
        const w = screenToWorld(p);
        draggingNode.x = w.x; draggingNode.y = w.y; render();
      } else if (panning) {
        transform.x += p.x - last.x; transform.y += p.y - last.y; applyTransform();
      }
      last = p;
    });
    window.addEventListener("mouseup", () => { draggingNode = null; panning = false; svg.classList.remove("dragging"); });
    svg.addEventListener("dblclick", event => {
      const target = event.target.closest(".node");
      if (!target) return;
      setCenter(target.dataset.id, Number(document.getElementById("hopSelect").value));
    });
    svg.addEventListener("wheel", event => {
      event.preventDefault();
      const p = point(event), before = screenToWorld(p);
      transform.scale = Math.max(.2, Math.min(4, transform.scale * (event.deltaY > 0 ? .9 : 1.1)));
      transform.x = p.x - before.x * transform.scale;
      transform.y = p.y - before.y * transform.scale;
      applyTransform();
    }, { passive:false });

    document.getElementById("btnSearch").onclick = () => setCenter(searchBest(document.getElementById("queryInput").value), Number(document.getElementById("hopSelect").value));
    document.getElementById("queryInput").addEventListener("keydown", event => { if (event.key === "Enter") document.getElementById("btnSearch").click(); });
    document.getElementById("btnCore").onclick = showCore;
    document.getElementById("btnFit").onclick = fitView;
    document.getElementById("btnReset").onclick = () => setCenter(centerId, Number(document.getElementById("hopSelect").value));
    function resize() { const r = svg.getBoundingClientRect(); width = r.width; height = r.height; svg.setAttribute("viewBox", `0 0 ${width} ${height}`); }
    window.addEventListener("resize", () => { resize(); fitView(); });
    resize();
    showCore();
  </script>
</body>
</html>
"""
    html = (
        html.replace("__NODE_COUNT__", str(len(nodes)))
        .replace("__EDGE_COUNT__", str(len(visible_edges)))
        .replace("__NODE_LEGEND__", "".join(f'<span><i style="background:{type_color.get(t, "#64748b")}"></i>{escape(t)} ({count})</span>' for t, count in node_types.most_common()))
        .replace("__REL_LEGEND__", "".join(f"<span>{escape(t)} ({count})</span>" for t, count in rel_types.most_common()))
        .replace("__NODES_JSON__", json.dumps(nodes, ensure_ascii=False))
        .replace("__EDGES_JSON__", json.dumps(visible_edges, ensure_ascii=False))
        .replace("__COLORS_JSON__", json.dumps(type_color, ensure_ascii=False))
        .replace("__DEFAULT_CENTER__", default_center)
    )
    import re as _re

    html = html.replace(
        '<body>\n  <div class="layout">',
        '''<body>
  <div class="app-shell">
  <header class="topbar">
    <div class="brand">
      <div class="brand-icon" aria-hidden="true">◆</div>
      <div>
        <div class="brand-title">DeepDOC</div>
        <div class="brand-subtitle">问题驱动知识图谱</div>
      </div>
    </div>
    <div class="stat">Project KG · Query-centered view</div>
  </header>
  <div class="layout">''',
    ).replace(
        "  </div>\n  <script>",
        "  </div>\n  </div>\n  <script>",
        1,
    )
    html = _re.sub(
        r"<aside>.*?</aside>",
        '''<aside>
      <h1>查询中心图谱</h1>
      <div class="stat">全量节点: <code>__NODE_COUNT__</code></div>
      <div class="stat">全量关系: <code>__EDGE_COUNT__</code></div>
      <div class="hint">输入问题或实体名后，只展示匹配实体及其一跳/二跳邻居。双击图中节点会以该节点为中心重新展开。</div>
      <input id="queryInput" placeholder="例如：LAD-RAG、传统 RAG、图表生成" />
      <select id="hopSelect">
        <option value="1">展开一跳关系</option>
        <option value="2" selected>展开二跳关系</option>
      </select>
      <div class="actions">
        <button id="btnSearch" type="button">查询</button>
        <button id="btnCore" type="button">核心图</button>
      </div>
      <h2>推荐入口</h2>
      <div class="chips" id="chips"></div>
      <h2>节点类型</h2>
      <div class="legend">__NODE_LEGEND__</div>
      <h2>关系类型</h2>
      <div class="legend">__REL_LEGEND__</div>
    </aside>''',
        html,
        count=1,
        flags=_re.S,
    )
    html = html.replace('<button id="btnFit" type="button">閫傞厤</button>', '<button id="btnFit" type="button">适配</button>')
    html = html.replace('<button id="btnReset" type="button">閲嶆帓</button>', '<button id="btnReset" type="button">重排</button>')
    html = _re.sub(
        r'<section class="detail" id="detail">.*?</section>',
        '''<section class="detail" id="detail">
      <h1>当前子图</h1>
      <div class="muted">选择一个入口实体或输入查询。</div>
    </section>''',
        html,
        count=1,
        flags=_re.S,
    )
    html = _re.sub(
        r"function showDetail\(node\) \{.*?\n    function escapeHtml",
        '''function showDetail(node) {
      const relations = (adj.get(node.id) || []).filter(edge => viewEdges.includes(edge));
      const evidence = (node.evidence || []).slice(0, 5);
      detail.innerHTML = `
        <h1>${escapeHtml(node.label)}</h1>
        <div><span class="chip">${escapeHtml(node.type)}</span><span class="chip">${escapeHtml(node.id)}</span></div>
        <h2>来源问答</h2>
        ${(node.sourceQaIds || []).map(id => `<div class="item"><code>${escapeHtml(id)}</code></div>`).join("") || "<div class='muted'>无</div>"}
        <h2>当前子图关系</h2>
        ${relations.map(edge => {
          const otherId = edge.source === node.id ? edge.target : edge.source;
          const other = nodeById.get(otherId);
          const arrow = edge.source === node.id ? "->" : "<-";
          return `<div class="item"><b>${escapeHtml(edge.relation)}</b> ${arrow} <code>${escapeHtml(other?.label || otherId)}</code></div>`;
        }).join("") || "<div class='muted'>无</div>"}
        <h2>证据 chunk</h2>
        ${evidence.map(ev => `<div class="item"><code>${escapeHtml(ev.chunkId || "")}</code> · page ${escapeHtml(String(ev.pageNo || ""))}<br>${escapeHtml(ev.textPreview || "")}</div>`).join("") || "<div class='muted'>无</div>"}
      `;
    }

    function escapeHtml''',
        html,
        count=1,
        flags=_re.S,
    )
    html = (
        html.replace("__NODE_COUNT__", str(len(nodes)))
        .replace("__EDGE_COUNT__", str(len(visible_edges)))
        .replace("__NODE_LEGEND__", "".join(f'<span><i style="background:{type_color.get(t, "#64748b")}"></i>{escape(t)} ({count})</span>' for t, count in node_types.most_common()))
        .replace("__REL_LEGEND__", "".join(f"<span>{escape(t)} ({count})</span>" for t, count in rel_types.most_common()))
    )
    path.write_text(html, encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    chunk_index = load_chunk_index()

    train = [
        {**qa, "evidence": enrich_evidence(qa["evidence"], chunk_index)}
        for qa in TRAIN_QA
    ]
    test = [
        {**qa, "evidence": enrich_evidence(qa["evidence"], chunk_index)}
        for qa in TEST_QA
    ]
    graph = build_graph(TRAIN_QA, chunk_index)
    results = evaluate_tests(graph, TEST_QA, chunk_index)

    write_json(OUT_DIR / "kg_qa_train.json", train)
    write_json(OUT_DIR / "kg_qa_test.json", test)
    write_json(OUT_DIR / "kg_question_driven_kg.json", graph)
    write_json(OUT_DIR / "kg_test_integration_report.json", results)
    write_report(OUT_DIR / "kg_test_integration_report.md", graph, results)
    write_query_centered_preview(OUT_DIR / "kg_graph_preview.html", graph)

    print(f"written: {OUT_DIR}")
    print(f"train={len(train)} test={len(test)} nodes={graph['metadata']['nodeCount']} edges={graph['metadata']['edgeCount']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
