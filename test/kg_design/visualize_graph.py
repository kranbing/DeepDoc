"""
Knowledge Graph Visualization Generator.

Reads kg_graph.json and produces:
  - graph_preview.html (standalone interactive visualization)
  - graph_preview.md (markdown table summary)
"""

import json
import os
import sys
from pathlib import Path
from collections import Counter

# Project root
ROOT = Path(__file__).resolve().parent.parent.parent
TEST_DIR = ROOT / "test"
OUTPUT_DIR = TEST_DIR / "kg_output"

ENTITY_COLORS = {
    "Document": "#4e79a7",
    "Section": "#59a14f",
    "Chunk": "#86bcb6",
    "Method": "#e15759",
    "Dataset": "#f28e2c",
    "Metric": "#edc948",
    "Concept": "#76b7b2",
    "Task": "#b07aa1",
    "Tool": "#ff9da7",
    "Author": "#9c755f",
    "Organization": "#bab0ac",
}


def load_graph(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_html_preview(graph: dict, output_path: Path) -> None:
    """Generate a standalone HTML file with D3.js force-directed graph."""
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    metadata = graph.get("metadata", {})

    # Build index for edges
    node_ids = {n["id"] for n in nodes}
    valid_edges = [e for e in edges if e.get("source_id") in node_ids and e.get("target_id") in node_ids]

    # Assign index to each node for D3
    id_to_idx = {n["id"]: i for i, n in enumerate(nodes)}
    for e in valid_edges:
        e["source_idx"] = id_to_idx[e["source_id"]]
        e["target_idx"] = id_to_idx[e["target_id"]]

    nodes_json = json.dumps(nodes, ensure_ascii=False)
    edges_json = json.dumps(valid_edges, ensure_ascii=False)
    colors_json = json.dumps(ENTITY_COLORS)

    stats = {
        "total_nodes": len(nodes),
        "total_edges": len(valid_edges),
        "type_counts": dict(Counter(n.get("type", "Unknown") for n in nodes)),
    }
    stats_json = json.dumps(stats)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DeepDoc Knowledge Graph</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0d1117; color: #c9d1d9; overflow: hidden; }}
#container {{ display: flex; height: 100vh; }}
#sidebar {{ width: 280px; background: #161b22; border-right: 1px solid #30363d; padding: 16px; overflow-y: auto; flex-shrink: 0; }}
#sidebar h2 {{ font-size: 16px; margin-bottom: 12px; color: #58a6ff; }}
#sidebar .stat {{ margin: 4px 0; font-size: 13px; }}
#sidebar .stat span {{ color: #58a6ff; font-weight: 600; }}
.legend {{ margin-top: 16px; }}
.legend-item {{ display: flex; align-items: center; margin: 4px 0; font-size: 12px; }}
.legend-dot {{ width: 10px; height: 10px; border-radius: 50%; margin-right: 8px; flex-shrink: 0; }}
#search-box {{ width: 100%; padding: 6px 10px; background: #0d1117; border: 1px solid #30363d; color: #c9d1d9; border-radius: 6px; font-size: 13px; margin-bottom: 12px; }}
#graph-area {{ flex: 1; position: relative; }}
svg {{ width: 100%; height: 100%; }}
.node-circle {{ cursor: pointer; stroke: #0d1117; stroke-width: 1.5px; }}
.node-label {{ font-size: 10px; fill: #c9d1d9; pointer-events: none; text-anchor: middle; }}
.edge-line {{ stroke: #30363d; stroke-width: 1px; stroke-opacity: 0.6; }}
#tooltip {{ position: absolute; background: #1c2128; border: 1px solid #30363d; border-radius: 8px; padding: 10px 14px; font-size: 12px; pointer-events: none; display: none; max-width: 300px; z-index: 10; }}
#tooltip .tt-name {{ font-weight: 600; color: #58a6ff; margin-bottom: 4px; }}
#tooltip .tt-type {{ color: #8b949e; margin-bottom: 6px; }}
#tooltip .tt-desc {{ color: #c9d1d9; line-height: 1.4; }}
#edge-labels {{ position: absolute; top: 10px; right: 10px; background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 8px 12px; font-size: 11px; }}
</style>
</head>
<body>
<div id="container">
  <div id="sidebar">
    <h2>Knowledge Graph</h2>
    <div id="stats"></div>
    <input type="text" id="search-box" placeholder="Search entities...">
    <div class="legend" id="legend"></div>
    <div id="edge-labels"></div>
  </div>
  <div id="graph-area">
    <svg id="graph-svg"></svg>
    <div id="tooltip"></div>
  </div>
</div>
<script src="https://d3js.org/d3.v7.min.js"></script>
<script>
const nodesData = {nodes_json};
const edgesData = {edges_json};
const COLORS = {colors_json};
const stats = {stats_json};

// Stats
const statsDiv = document.getElementById('stats');
statsDiv.innerHTML = `<div class="stat">Nodes: <span>${{stats.total_nodes}}</span></div><div class="stat">Edges: <span>${{stats.total_edges}}</span></div>`;
const typeCounts = stats.type_counts;
const legendDiv = document.getElementById('legend');
for (const [type, color] of Object.entries(COLORS)) {{
  if (typeCounts[type]) {{
    legendDiv.innerHTML += `<div class="legend-item"><div class="legend-dot" style="background:${{color}}"></div>${{type}} (${{typeCounts[type]}})</div>`;
  }}
}}

// Edge types
const edgeTypes = [...new Set(edgesData.map(e => e.relation))];
const edgeColors = d3.scaleOrdinal(d3.schemeTableau10).domain(edgeTypes);
document.getElementById('edge-labels').innerHTML = '<b>Relations:</b><br>' + edgeTypes.map(t => `<span style="color:${{edgeColors(t)}}">${{t}}</span>`).join(', ');

const svg = d3.select('#graph-svg');
const width = document.getElementById('graph-area').clientWidth;
const height = document.getElementById('graph-area').clientHeight;
svg.attr('viewBox', [0, 0, width, height]);

const g = svg.append('g');
svg.call(d3.zoom().scaleExtent([0.1, 8]).on('zoom', (e) => g.attr('transform', e.transform)));

const simulation = d3.forceSimulation(nodesData)
  .force('link', d3.forceLink(edgesData).id(d => d.id).distance(100))
  .force('charge', d3.forceManyBody().strength(-200))
  .force('center', d3.forceCenter(width / 2, height / 2))
  .force('collision', d3.forceCollide().radius(20));

const link = g.append('g').selectAll('line').data(edgesData).join('line')
  .attr('class', 'edge-line')
  .attr('stroke', d => edgeColors(d.relation));

const node = g.append('g').selectAll('circle').data(nodesData).join('circle')
  .attr('class', 'node-circle')
  .attr('r', d => d.type === 'Document' ? 12 : d.type === 'Section' ? 8 : 6)
  .attr('fill', d => COLORS[d.type] || '#8b949e')
  .call(d3.drag().on('start', dragStarted).on('drag', dragged).on('end', dragEnded));

const label = g.append('g').selectAll('text').data(nodesData).join('text')
  .attr('class', 'node-label')
  .attr('dy', -12)
  .text(d => d.name && d.name.length > 20 ? d.name.substring(0, 18) + '...' : d.name);

const tooltip = document.getElementById('tooltip');
node.on('mouseover', (e, d) => {{
  tooltip.style.display = 'block';
  tooltip.innerHTML = `<div class="tt-name">${{d.name}}</div><div class="tt-type">${{d.type}}</div>${{d.description ? `<div class="tt-desc">${{d.description}}</div>` : ''}}`;
}})
.on('mousemove', (e) => {{
  tooltip.style.left = (e.pageX + 12) + 'px';
  tooltip.style.top = (e.pageY - 12) + 'px';
}})
.on('mouseout', () => {{ tooltip.style.display = 'none'; }});

simulation.on('tick', () => {{
  link.attr('x1', d => d.source.x).attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x).attr('y2', d => d.target.y);
  node.attr('cx', d => d.x).attr('cy', d => d.y);
  label.attr('x', d => d.x).attr('y', d => d.y);
}});

function dragStarted(e, d) {{ if (!e.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; }}
function dragged(e, d) {{ d.fx = e.x; d.fy = e.y; }}
function dragEnded(e, d) {{ if (!e.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; }}

// Search
document.getElementById('search-box').addEventListener('input', function() {{
  const q = this.value.toLowerCase();
  node.attr('opacity', d => q === '' ? 1 : d.name.toLowerCase().includes(q) ? 1 : 0.1);
  label.attr('opacity', d => q === '' ? 0.7 : d.name.toLowerCase().includes(q) ? 1 : 0);
  link.attr('stroke-opacity', q === '' ? 0.6 : 0.05);
}});
</script>
</body>
</html>"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[visualize] HTML preview written to {output_path}")


def generate_markdown_preview(graph: dict, output_path: Path) -> None:
    """Generate a markdown table summary of the graph."""
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    metadata = graph.get("metadata", {})

    type_counts = Counter(n.get("type", "Unknown") for n in nodes)
    rel_counts = Counter(e.get("relation", "Unknown") for e in edges)

    lines = ["# Knowledge Graph Preview\n"]
    lines.append(f"**Documents:** {metadata.get('doc_count', 'N/A')}")
    lines.append(f"**Total Nodes:** {len(nodes)}")
    lines.append(f"**Total Edges:** {len(edges)}")
    lines.append(f"**Generated:** {metadata.get('generated_at', 'N/A')}\n")

    lines.append("## Entity Types\n")
    lines.append("| Type | Count |")
    lines.append("|------|-------|")
    for t, c in type_counts.most_common():
        lines.append(f"| {t} | {c} |")

    lines.append("\n## Relation Types\n")
    lines.append("| Relation | Count |")
    lines.append("|----------|-------|")
    for r, c in rel_counts.most_common():
        lines.append(f"| {r} | {c} |")

    lines.append("\n## Sample Entities (first 20)\n")
    lines.append("| ID | Type | Name |")
    lines.append("|----|------|------|")
    for n in nodes[:20]:
        lines.append(f"| {n['id']} | {n.get('type', '')} | {n.get('name', '')[:50]} |")

    lines.append("\n## Sample Relations (first 20)\n")
    lines.append("| Source | Relation | Target |")
    lines.append("|--------|----------|--------|")
    for e in edges[:20]:
        lines.append(f"| {e.get('source_id', '')} | {e.get('relation', '')} | {e.get('target_id', '')} |")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[visualize] Markdown preview written to {output_path}")


def main():
    graph_path = OUTPUT_DIR / "kg_graph.json"
    if not graph_path.exists():
        print(f"[visualize] Graph file not found: {graph_path}")
        print("[visualize] Run run_kg_pipeline.py first to generate the graph.")
        sys.exit(1)

    graph = load_graph(graph_path)
    generate_html_preview(graph, OUTPUT_DIR / "graph_preview.html")
    generate_markdown_preview(graph, OUTPUT_DIR / "graph_preview.md")


if __name__ == "__main__":
    main()
