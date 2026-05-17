"""
Entity Extractor Module (Member 1)

Extracts entities from document chunks using:
  1. Rule-based patterns (headings, acronyms, technical terms)
  2. LLM-based extraction via DeepSeek API
"""

import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib import request as urlrequest, error as urlerror

ROOT = Path(__file__).resolve().parent.parent.parent

# Known entity patterns
KNOWN_DATASETS = {
    "squad", "squadv2", "squad 2", "msmarco", "natural questions", "triviaqa",
    "quasar", "searchqa", "hotpotqa", "narrativeqa", "qasper", "duorc",
    "race", "multirc", "record", "wmt", "iwslt", "opus", "commoncrawl",
    "bookscorpus", "wikipedia", "imagenet", "coco", "mnist", "cifar",
    "glue", "superglue", "blimp", "hellaswag", "arc", "mmlu", "hellaswag",
}

KNOWN_METRICS = {
    "f1", "exact match", "em", "bleu", "rouge", "rouge-l", "meteor",
    "bleu-1", "bleu-2", "bleu-3", "bleu-4", "accuracy", "precision",
    "recall", "perplexity", "wer", "cer", "map", "ndcg", "mrr",
    "bertscore", "bleurt",
}

KNOWN_METHODS = {
    "bert", "gpt", "gpt-2", "gpt-3", "gpt-4", "transformer", "transformers",
    "lstm", "gru", "rnn", "cnn", "attention", "self-attention",
    "roberta", "xlnet", "albert", "distilbert", "electra", "deberta",
    "t5", "bart", "pegasus", "mbart", "xlm-roberta", "xlm",
    "word2vec", "glove", "fasttext", "elmo", "ulmfit",
    "seq2seq", "encoder-decoder", "pointer-generator", "copynet",
    "beam search", "greedy decoding", "nucleus sampling",
    "knowledge graph", "knowledge graph completion",
    "faiss", "tf-idf", "bm25", "bm25f",
    "rag", "retrieval-augmented generation",
}

ACRONYM_PATTERN = re.compile(r'\b[A-Z]{2,6}\b')
CAPITALIZED_PHRASE = re.compile(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b')
QUOTED_TERM = re.compile(r'"([^"]{2,50})"')
PAREN_ACRONYM = re.compile(r'([A-Z][a-zA-Z\s]{2,30})\s*\(([A-Z]{2,6})\)')

# Chinese-aware patterns
CHINESE_TECH_TERM = re.compile(r'(?:深度学习|机器学习|自然语言处理|计算机视觉|知识图谱|向量数据库|大语言模型|注意力机制|卷积神经网络|循环神经网络|生成对抗网络|强化学习|迁移学习|预训练|微调|嵌入|分词|词向量|特征提取|模型训练|模型推理|数据增强|批归一化|Dropout|损失函数|优化器|学习率|梯度下降|反向传播|超参数|验证集|测试集|训练集|过拟合|欠拟合|正则化|注意力|编码器|解码器|自监督|对比学习|多模态|端到端)')
CHINESE_QUOTED = re.compile(r'[""「」]([^""「」]{2,30})[""「」]')
CHINESE_PAREN_TERM = re.compile(r'([一-鿿]{2,15})\s*[（(]\s*([A-Za-z][\w\-]*)\s*[）)]')

STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "dare", "ought",
    "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
    "as", "into", "through", "during", "before", "after", "above", "below",
    "between", "out", "off", "over", "under", "again", "further", "then",
    "once", "here", "there", "when", "where", "why", "how", "all", "both",
    "each", "few", "more", "most", "other", "some", "such", "no", "nor",
    "not", "only", "own", "same", "so", "than", "too", "very", "just",
    "because", "but", "and", "or", "if", "while", "this", "that", "these",
    "those", "it", "its", "we", "our", "you", "your", "they", "their",
    "he", "she", "his", "her", "which", "what", "who", "whom",
    "figure", "table", "section", "equation", "paper", "work", "approach",
    "method", "model", "result", "results", "data", "set", "task",
    "also", "however", "therefore", "thus", "furthermore", "moreover",
    "e.g", "i.e", "etc", "vs", "ie", "eg",
}


def _get_deepseek_api_key() -> Optional[str]:
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if key:
        return key
    key_file = ROOT / "backend" / ".deepseek_api_key"
    if key_file.is_file():
        return key_file.read_text(encoding="utf-8").strip() or None
    return None


def _llm_extract_entities(text: str, section_title: str = "", api_key: str = "") -> List[Dict[str, Any]]:
    """Use DeepSeek API to extract entities from text."""
    if not api_key:
        api_key = _get_deepseek_api_key()
    if not api_key:
        return []

    system_prompt = (
        "You are an information extraction system. Extract named entities from the given text. "
        "Return a JSON object with key 'entities' containing a list. Each entity has: "
        "'name' (string, use the ORIGINAL language of the text — if Chinese, keep Chinese), "
        "'type' (one of: Method, Dataset, Metric, Concept, Task, Tool, Author, Organization), "
        "'description' (brief description, max 50 chars, same language as entity name). "
        "Focus on: model names, algorithms, datasets, metrics, technical concepts, tasks, tools/frameworks, "
        "project names, system names, technical terms. "
        "Do NOT include generic words like '模型', '数据', '方法', 'model', 'data', 'method'. "
        "Return ONLY valid JSON, no markdown."
    )

    user_prompt = f"Section: {section_title}\n\nText:\n{text[:2000]}"

    body = {
        "model": "deepseek-chat",
        "temperature": 0.1,
        "max_tokens": 1024,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    try:
        req = urlrequest.Request(
            "https://api.deepseek.com/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        with urlrequest.urlopen(req, timeout=60) as resp:
            raw = json.loads(resp.read().decode("utf-8"))

        message = raw.get("choices", [{}])[0].get("message", {}).get("content", "")
        data = json.loads(message) if message.strip().startswith("{") else {}
        entities = data.get("entities", [])

        result = []
        for ent in entities:
            name = str(ent.get("name", "")).strip()
            etype = str(ent.get("type", "Concept")).strip()
            desc = str(ent.get("description", "")).strip()
            if name and len(name) >= 2:
                result.append({
                    "name": name,
                    "type": etype if etype in {
                        "Method", "Dataset", "Metric", "Concept",
                        "Task", "Tool", "Author", "Organization"
                    } else "Concept",
                    "description": desc[:100],
                    "confidence": 0.8,
                    "source": "llm",
                })
        return result

    except Exception as e:
        print(f"[entity_extractor] LLM extraction failed: {e}")
        return []


def extract_entities_rule_based(text: str, section_title: str = "") -> List[Dict[str, Any]]:
    """Extract entities using rule-based patterns."""
    entities = []

    # 1. Parenthesized acronyms: "Long Short Term Memory (LSTM)"
    for match in PAREN_ACRONYM.finditer(text):
        full_name = match.group(1).strip()
        acronym = match.group(2).strip()
        entities.append({
            "name": full_name,
            "type": "Method",
            "description": f"Acronym: {acronym}",
            "confidence": 0.9,
            "source": "rule_paren_acronym",
        })

    # 2. Acronyms (2-6 uppercase letters)
    for match in ACRONYM_PATTERN.finditer(text):
        word = match.group()
        if word not in STOPWORDS and len(word) >= 2:
            lower = word.lower()
            if lower in KNOWN_DATASETS:
                etype = "Dataset"
            elif lower in KNOWN_METRICS:
                etype = "Metric"
            elif lower in KNOWN_METHODS:
                etype = "Method"
            else:
                etype = "Concept"
            entities.append({
                "name": word,
                "type": etype,
                "description": "",
                "confidence": 0.7,
                "source": "rule_acronym",
            })

    # 3. Capitalized phrases (proper nouns)
    for match in CAPITALIZED_PHRASE.finditer(text):
        phrase = match.group().strip()
        if len(phrase) >= 4 and phrase.lower() not in STOPWORDS:
            entities.append({
                "name": phrase,
                "type": "Concept",
                "description": "",
                "confidence": 0.5,
                "source": "rule_capitalized",
            })

    # 4. Quoted terms
    for match in QUOTED_TERM.finditer(text):
        term = match.group(1).strip()
        if len(term) >= 3 and term.lower() not in STOPWORDS:
            entities.append({
                "name": term,
                "type": "Concept",
                "description": "",
                "confidence": 0.6,
                "source": "rule_quoted",
            })

    # 5. Known datasets in text (case-insensitive)
    text_lower = text.lower()
    for ds in KNOWN_DATASETS:
        if ds in text_lower:
            # Find the actual casing in text
            idx = text_lower.index(ds)
            actual = text[idx:idx + len(ds)]
            entities.append({
                "name": actual,
                "type": "Dataset",
                "description": "",
                "confidence": 0.85,
                "source": "rule_known_dataset",
            })

    # 6. Known metrics in text
    for met in KNOWN_METRICS:
        if met in text_lower:
            idx = text_lower.index(met)
            actual = text[idx:idx + len(met)]
            entities.append({
                "name": actual,
                "type": "Metric",
                "description": "",
                "confidence": 0.85,
                "source": "rule_known_metric",
            })

    # 7. Section title as Section entity
    if section_title and len(section_title.strip()) >= 2:
        entities.append({
            "name": section_title.strip(),
            "type": "Section",
            "description": "",
            "confidence": 1.0,
            "source": "rule_section",
        })

    # 8. Chinese technical terms
    for match in CHINESE_TECH_TERM.finditer(text):
        term = match.group()
        entities.append({
            "name": term,
            "type": "Concept",
            "description": "",
            "confidence": 0.8,
            "source": "rule_chinese_tech",
        })

    # 9. Chinese quoted terms: "xxx" or "xxx"
    for match in CHINESE_QUOTED.finditer(text):
        term = match.group(1).strip()
        if len(term) >= 2:
            entities.append({
                "name": term,
                "type": "Concept",
                "description": "",
                "confidence": 0.6,
                "source": "rule_chinese_quoted",
            })

    # 10. Chinese terms with English parenthetical: 知识图谱(Knowledge Graph)
    for match in CHINESE_PAREN_TERM.finditer(text):
        cn_term = match.group(1).strip()
        en_term = match.group(2).strip()
        if len(cn_term) >= 2:
            entities.append({
                "name": cn_term,
                "type": "Method",
                "description": f"English: {en_term}",
                "confidence": 0.85,
                "source": "rule_cn_en_pair",
            })

    return entities


def extract_entities_from_chunk(
    chunk: Dict[str, Any],
    use_llm: bool = True,
    api_key: str = "",
) -> List[Dict[str, Any]]:
    """Extract entities from a single chunk dict."""
    text = chunk.get("normalizedContent") or chunk.get("content") or chunk.get("cleanText") or ""
    section = chunk.get("sectionTitle") or chunk.get("headingText") or ""
    doc_id = chunk.get("docId", "")
    chunk_id = chunk.get("chunkId", "")

    if not text.strip():
        return []

    # Rule-based extraction
    rule_entities = extract_entities_rule_based(text, section)

    # LLM-based extraction
    llm_entities = []
    if use_llm:
        llm_entities = _llm_extract_entities(text, section, api_key)

    # Merge and add metadata
    all_entities = rule_entities + llm_entities
    for ent in all_entities:
        ent["source_doc_id"] = doc_id
        ent["source_chunk_id"] = chunk_id
        ent["source_section"] = section
        ent["id"] = f"ent_{doc_id}_{chunk_id}_{hash(ent['name'].lower()) % 100000:05d}"

    return all_entities


def extract_entities_from_document(
    chunks: List[Dict[str, Any]],
    use_llm: bool = True,
    api_key: str = "",
    max_llm_calls: int = 20,
    llm_batch_size: int = 3,
) -> List[Dict[str, Any]]:
    """Extract entities from all chunks of a document."""
    all_entities = []
    llm_calls = 0

    for i, chunk in enumerate(chunks):
        # Always run rule-based
        entities = extract_entities_from_chunk(chunk, use_llm=False)
        all_entities.extend(entities)

        # LLM for selected chunks (first N per batch)
        if use_llm and llm_calls < max_llm_calls and i % llm_batch_size == 0:
            llm_ents = extract_entities_from_chunk(chunk, use_llm=True, api_key=api_key)
            all_entities.extend(llm_ents)
            llm_calls += 1
            if llm_calls % 5 == 0:
                print(f"  [entity_extractor] LLM calls: {llm_calls}/{max_llm_calls}")

    return all_entities
