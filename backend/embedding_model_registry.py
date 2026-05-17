from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List


@dataclass(frozen=True)
class EmbeddingModelSpec:
    key: str
    model_name: str
    description: str
    query_prefix: str = ""
    document_prefix: str = ""


_MODEL_SPECS = {
    "current": EmbeddingModelSpec(
        key="current",
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        description="Historical DeepDoc baseline embedding model",
    ),
    "bge": EmbeddingModelSpec(
        key="bge",
        model_name="BAAI/bge-small-zh-v1.5",
        description="BGE small Chinese retrieval embedding model",
        query_prefix="为这个句子生成表示以用于检索相关文章：",
    ),
    "text2vec": EmbeddingModelSpec(
        key="text2vec",
        model_name="shibing624/text2vec-base-chinese",
        description="Chinese sentence embedding model from text2vec",
    ),
}

_DEEPDOC_DEFAULT_MODEL_KEY = "bge"


def project_local_model_dir() -> str:
    return "models"


def local_model_candidate_paths() -> List[str]:
    # Prefer project-internal local model directory first, then Hugging Face model name.
    return [
        str(("models/BAAI/bge-small-zh-v1.5")),
        str(("models/bge-small-zh-v1.5")),
    ]


def list_model_keys() -> List[str]:
    return sorted(_MODEL_SPECS.keys())


def get_model_spec(model_key: str) -> EmbeddingModelSpec:
    key = str(model_key).strip().lower()
    if key not in _MODEL_SPECS:
        raise ValueError(f"Unsupported model: {model_key}")
    return _MODEL_SPECS[key]


def resolve_model_keys(requested: Iterable[str]) -> List[str]:
    keys = [str(item).strip().lower() for item in requested if str(item).strip()]
    if not keys:
        return list_model_keys()
    invalid = [key for key in keys if key not in _MODEL_SPECS]
    if invalid:
        raise ValueError(f"Unsupported models: {', '.join(invalid)}. Available: {', '.join(list_model_keys())}")
    return keys


def deepdoc_default_model_spec() -> EmbeddingModelSpec:
    return get_model_spec(_DEEPDOC_DEFAULT_MODEL_KEY)


def deepdoc_default_model_name() -> str:
    return deepdoc_default_model_spec().model_name


def prepare_query_texts(model_key: str, texts: Iterable[str]) -> List[str]:
    spec = get_model_spec(model_key)
    prefix = spec.query_prefix
    return [f"{prefix}{str(text or '').strip()}" if prefix else str(text or '').strip() for text in texts]


def prepare_document_texts(model_key: str, texts: Iterable[str]) -> List[str]:
    spec = get_model_spec(model_key)
    prefix = spec.document_prefix
    return [f"{prefix}{str(text or '').strip()}" if prefix else str(text or '').strip() for text in texts]
