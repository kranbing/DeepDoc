# Backend Notes

This backend is still anchored by `backend/main.py`, but the first extraction pass moves frequently changed QA logic into focused modules.

## Current module split

- `backend/main.py`
  Thin FastAPI entry, route wiring, project/workspace orchestration, OCR entrypoints, file serving, and document lifecycle endpoints.
- `backend/clients/deepseek_client.py`
  DeepSeek API key loading, HTTP request handling, and JSON response extraction.
- `backend/services/qa_service.py`
  QA prompt assembly, chunk-context normalization, overview-first vs evidence-first policy, and session compaction payload shaping.
- `backend/services/chunk_store.py`
  Persisted OCR/layout chunk storage and neighbor lookup helpers.
- `backend/services/vector_store.py`
  Project vector index build/update/search.
- `backend/services/overview_service.py`
  Single-document overview generation and persistence.
- `backend/services/project_store.py`
  Project/document file layout helpers and JSON read/write utilities.

## QA request flow

1. Route `/api/projects/{project_id}/docs/{doc_id}/ask-selection` lives in `main.py`.
2. Route loads:
   - manual selection from `now_conversation`
   - auto context from `chunkContext`
   - document overview from `overview.json`
   - session compaction / recent turns
3. `backend/services/qa_service.py` decides prompt mode:
   - manual selection -> `evidence-first`
   - auto context only -> `overview-first`, chunks are supplementary
   - no chunks -> overview/conversation only
4. `backend/clients/deepseek_client.py` sends the request to DeepSeek.

## Where to edit

- Change DeepSeek request details:
  `backend/clients/deepseek_client.py`
- Change QA prompt strategy or chunk-context rules:
  `backend/services/qa_service.py`
- Change session persistence shape:
  `backend/main.py`
- Change overview generation:
  `backend/services/overview_service.py`
- Change retrieval/chunk indexing:
  `backend/services/vector_store.py`

## Next safe extraction targets

- Session storage helpers from `main.py` -> `backend/services/session_service.py`
- QA routes from `main.py` -> `backend/api/qa.py`
- Pydantic request/response models -> `backend/schemas.py`
