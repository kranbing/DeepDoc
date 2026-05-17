# Knowledge Graph Construction Pipeline

## Pipeline Overview

```
[Document Data] --> [Entity Extraction] --> [Relation Extraction] --> [Cleaning] --> [Graph Storage] --> [Query & Visualization]
     |                    |                       |                      |                |                    |
  lad_chunk.json    Section titles         Co-occurrence          Dedup entities     JSON store         Query API
  manifest.json     Key terms              Pattern matching       Merge similar      (neo4j optional)   HTML preview
                    Model names            LLM-based RE           Filter noise       Graph JSON         Search interface
                    Method names
```

## Step-by-Step Flow

### Step 1: Document Reading
- Input: `lad_chunk.json` files from `test/8-lad_rag_test/data/documents/`
- Each file contains structured chunks with section info, headings, and text
- Also read `qasper_lad_manifest.json` for corpus-level metadata

### Step 2: Entity Extraction
- **Rule-based extraction**:
  - Section headings -> Section entities
  - Technical terms (capitalized phrases, acronyms) -> Concept/Method entities
  - Known dataset names (pattern matching) -> Dataset entities
  - Known metric names -> Metric entities
- **LLM-based extraction** (via DeepSeek API):
  - Send chunk text to LLM with structured prompt
  - Extract entities as JSON with type, name, description, confidence

### Step 3: Relation Extraction
- **Co-occurrence based**:
  - Entities in same chunk/section -> potential relations
  - Use LLM to classify relation type
- **Pattern-based**:
  - "X uses Y" -> USES relation
  - "X evaluated on Y" -> EVALUATES_ON relation
  - "X based on Y" -> BASED_ON relation
- **Structural**:
  - Section hierarchy -> CONTAINS relations
  - Document-section -> CONTAINS relations

### Step 4: Cleaning
- Remove duplicate entities (normalize names, case-insensitive matching)
- Merge similar entities (edit distance, substring matching)
- Filter short/noise entities (< 3 chars, common stopwords)
- Filter low-confidence relations (< 0.3)
- Remove self-loops and trivial relations

### Step 5: Graph Storage
- Primary: JSON file storage (`kg_graph.json`)
- Schema: `{nodes: [...], edges: [...], metadata: {...}}`
- Optional: Neo4j interface (stub only, no hard dependency)

### Step 6: Query
- Entity lookup by name (fuzzy match)
- One-hop relation query
- Two-entity path query
- Keyword-based candidate retrieval

### Step 7: Visualization
- HTML page with force-directed graph (D3.js via CDN)
- Color-coded by entity type
- Interactive: hover for details, click to expand
- Export as standalone HTML file

## Configuration

| Parameter | Value | Description |
|-----------|-------|-------------|
| `CHUNK_BATCH_SIZE` | 5 | Chunks per LLM batch |
| `MIN_ENTITY_LEN` | 3 | Minimum entity name length |
| `MIN_CONFIDENCE` | 0.3 | Minimum confidence threshold |
| `DEDUP_THRESHOLD` | 0.85 | Similarity threshold for merging |
| `MAX_ENTITIES_PER_DOC` | 200 | Cap per document |
