# Knowledge Graph Schema Design

## 1. Entity Types

| Type | Description | Example |
|------|-------------|---------|
| `Document` | Source document (paper) | "Data Collection for Interactive Learning" |
| `Section` | Document section/chapter | "Introduction", "Methodology" |
| `Method` | Algorithm, model, or approach | "BERT", "Transformer", "LSTM" |
| `Dataset` | Dataset or corpus | "Qasper", "SQuAD", "MSMARCO" |
| `Metric` | Evaluation metric | "F1", "BLEU", "ROUGE", "Exact Match" |
| `Concept` | Key concept or term | "attention mechanism", "transfer learning" |
| `Task` | NLP task or problem | "question answering", "machine translation" |
| `Tool` | Framework or library | "PyTorch", "TensorFlow", "FAISS" |
| `Author` | Paper author (if extractable) | "Vaswani et al." |
| `Organization` | Research org or company | "Google", "OpenAI", "Tsinghua" |

## 2. Relation Types

| Relation | Description | Example |
|----------|-------------|---------|
| `CONTAINS` | Parent contains child | Document CONTAINS Section |
| `PROPOSES` | Entity proposes method/concept | Paper PROPOSES Model |
| `USES` | Entity uses another | Method USES Dataset |
| `EVALUATES_ON` | Evaluated on dataset/metric | Method EVALUATES_ON Dataset |
| `ACHIEVES` | Achieves metric value | Method ACHIEVES Metric |
| `BASED_ON` | Built upon another | Method BASED_ON Method |
| `BELONGS_TO` | Belongs to category | Dataset BELONGS_TO Task |
| `DEPENDS_ON` | Dependency | Method DEPENDS_ON Tool |
| `COMPARES_WITH` | Comparison relation | Method COMPARES_WITH Method |
| `PART_OF` | Part-whole relation | Concept PART_OF Concept |

## 3. Node Properties

### Common Properties
- `id`: Unique identifier (string)
- `type`: Entity type (string)
- `name`: Display name (string)
- `description`: Optional description (string)
- `source_doc_id`: Source document ID (string)
- `source_chunk_id`: Source chunk ID where extracted (string)
- `confidence`: Extraction confidence 0.0-1.0 (float)

### Type-Specific Properties
- **Document**: `abstract`, `doc_type`, `year`
- **Section**: `level`, `section_path`
- **Method**: `category` (model/algorithm/architecture)
- **Dataset**: `domain`, `size`
- **Metric**: `direction` (higher-is-better / lower-is-better)

## 4. Edge Properties

- `source_id`: Source node ID
- `target_id`: Target node ID
- `relation`: Relation type
- `weight`: Confidence weight 0.0-1.0 (float)
- `evidence`: Source text supporting this relation (string)
- `source_chunk_id`: Chunk where relation was extracted

## 5. Data Source Fields

All entities and relations trace back to:
- `docId`: Document identifier
- `chunkId`: Chunk identifier
- `sectionId`: Section identifier
- `sectionPathText`: Section path for context
- `normalizedContent`: Clean text used for extraction
