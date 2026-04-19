from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class OCRBlock:
    index: int
    label: str
    content: str
    bbox_2d: List[int]
    page: int = 1
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "index": self.index,
            "label": self.label,
            "content": self.content,
            "bbox_2d": self.bbox_2d,
        }
        if self.meta:
            data.update(self.meta)
        return data


@dataclass
class Line:
    text: str
    bbox_2d: List[int]
    block_indices: List[int]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "bbox_2d": self.bbox_2d,
            "block_indices": self.block_indices,
        }


@dataclass
class PageResult:
    page: int
    text: str
    lines: List[Line]
    paragraphs: List[str]
    blocks: List[OCRBlock]
    quality_score: float
    structure_score: float
    final_score: float
    issues: List[str]
    structure_issues: List[str]
    metrics: Dict[str, Any]
    structure_metrics: Dict[str, Any]
    retry_count: int = 0
    duration_sec: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "page": self.page,
            "text": self.text,
            "lines": [line.to_dict() for line in self.lines],
            "paragraphs": self.paragraphs,
            "blocks": [block.to_dict() for block in self.blocks],
            "quality_score": round(float(self.quality_score), 4),
            "structure_score": round(float(self.structure_score), 4),
            "final_score": round(float(self.final_score), 4),
            "issues": self.issues,
            "structure_issues": self.structure_issues,
            "metrics": self.metrics,
            "structure_metrics": self.structure_metrics,
            "retry_count": self.retry_count,
            "duration_sec": round(float(self.duration_sec), 4),
        }


@dataclass
class QualityResult:
    score: float
    issues: List[str]
    metrics: Dict[str, Any]


@dataclass
class StructureResult:
    score: float
    issues: List[str]
    metrics: Dict[str, Any]


@dataclass
class PipelineResult:
    doc_id: str
    pages: List[PageResult]
    stats: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "pages": [page.to_dict() for page in self.pages],
            "stats": self.stats,
        }
