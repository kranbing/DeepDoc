# Knowledge Extraction Report

**Generated:** 2026-05-17T14:05:53.137526
**Documents Processed:** 1

## Entity Extraction Statistics

| Metric | Value |
|--------|-------|
| Raw entities extracted | 855 |
| After cleaning | 231 |
| Removed (noise + duplicates) | 624 |
| Dedup rate | 73.0% |

### Entity Type Distribution

| Type | Count |
|------|-------|
| Chunk | 381 |
| Section | 213 |
| Concept | 101 |
| Method | 19 |
| Metric | 4 |
| Task | 2 |
| Dataset | 2 |
| Document | 1 |

### Extraction Source Distribution

| Source | Count |
|--------|-------|
| unknown | 492 |
| rule_section | 103 |
| rule_capitalized | 45 |
| rule_acronym | 33 |
| rule_chinese_tech | 16 |
| llm | 12 |
| rule_cn_en_pair | 9 |
| rule_quoted | 4 |
| rule_known_metric | 4 |
| rule_known_dataset | 2 |
| rule_capitalized,llm | 2 |
| rule_paren_acronym | 1 |

## Relation Extraction Statistics

| Metric | Value |
|--------|-------|
| Raw relations extracted | 567 |
| After cleaning | 514 |
| Removed (low quality) | 53 |

### Relation Type Distribution

| Type | Count |
|------|-------|
| CONTAINS | 489 |
| COMPARES_WITH | 23 |
| ACHIEVES | 2 |

## Per-Document Results

| Doc ID | Entities | Relations |
|--------|----------|-----------|
| pdf_e21a5d3f | 723 | 514 |
