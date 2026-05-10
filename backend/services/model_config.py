from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class ModelConfig:
    mode: str
    model: str = "deepseek-chat"
    temperature: float = 0.2
    top_p: float = 0.9
    max_tokens: int = 768
    timeout_seconds: int = 120
    max_retries: int = 2

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


TASK_MODEL_CONFIGS: Dict[str, ModelConfig] = {
    "fact_qa": ModelConfig(mode="fact_stable", temperature=0.1, top_p=0.8, max_tokens=384),
    "local_evidence_qa": ModelConfig(mode="local_evidence_stable", temperature=0.1, top_p=0.8, max_tokens=512),
    "multi_evidence_qa": ModelConfig(mode="multi_evidence_balanced", temperature=0.2, top_p=0.9, max_tokens=900),
    "method_qa": ModelConfig(mode="method_detailed", temperature=0.2, top_p=0.9, max_tokens=1100),
    "comparison_qa": ModelConfig(mode="comparison_structured", temperature=0.25, top_p=0.9, max_tokens=1100),
    "dataset_qa": ModelConfig(mode="dataset_precise", temperature=0.1, top_p=0.85, max_tokens=650),
}


PARAMETER_TEST_MODES: Dict[str, ModelConfig] = {
    "stable": ModelConfig(mode="stable", temperature=0.1, top_p=0.8, max_tokens=512),
    "balanced": ModelConfig(mode="balanced", temperature=0.2, top_p=0.9, max_tokens=768),
    "exploratory": ModelConfig(mode="exploratory", temperature=0.35, top_p=0.95, max_tokens=1100),
}


def model_config_for_task(task_type: str) -> ModelConfig:
    return TASK_MODEL_CONFIGS.get(str(task_type or ""), PARAMETER_TEST_MODES["balanced"])
