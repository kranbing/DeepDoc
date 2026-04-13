from __future__ import annotations

from pathlib import Path
from typing import Optional

from .adapters import FailoverOCRAdapter, GlmOcrAdapter, MockOcrAdapter
from .pipeline import OCRPipeline, PipelineConfig
from .types import PipelineResult


def resolve_default_config_path(explicit_path: Optional[str]) -> Optional[str]:
    """Resolve config path with local-first lookup for test convenience."""
    if explicit_path:
        return explicit_path

    repo_root = Path(__file__).resolve().parents[2]
    candidates = [
        Path.cwd() / "config.yaml",
        repo_root / "test" / "config.yaml",
        repo_root / "GLM-OCR-0.1.4" / "glmocr" / "config.yaml",
    ]
    for path in candidates:
        if path.is_file():
            return str(path)
    return None


def run_pipeline(
    *,
    input_path: str,
    output_dir: str = "./output/pipeline",
    doc_id: Optional[str] = None,
    mode: str = "maas",
    api_key: Optional[str] = None,
    config_path: Optional[str] = None,
    env_file: Optional[str] = None,
    enable_mock_fallback: bool = False,
    mock_noisy: bool = False,
    score_threshold: float = 0.7,
    final_score_threshold: float = 0.85,
    structure_score_threshold: float = 0.8,
    quality_weight: float = 0.7,
    structure_weight: float = 0.3,
    max_retries: int = 3,
    pdf_dpi: int = 200,
    retry_pdf_dpi: int = 280,
    no_viz: bool = False,
) -> PipelineResult:
    resolved_config = resolve_default_config_path(config_path)

    if mode == "mock":
        adapter = MockOcrAdapter(noisy=mock_noisy)
    else:
        try:
            adapter = GlmOcrAdapter(
                mode=mode,
                api_key=api_key,
                config_path=resolved_config,
                env_file=env_file,
            )
        except Exception:
            if not enable_mock_fallback:
                raise
            adapter = MockOcrAdapter(noisy=mock_noisy)
        else:
            if enable_mock_fallback:
                adapter = FailoverOCRAdapter(adapter, MockOcrAdapter(noisy=mock_noisy))

    try:
        pipeline = OCRPipeline(
            adapter=adapter,
            config=PipelineConfig(
                score_threshold=score_threshold,
                final_score_threshold=final_score_threshold,
                structure_score_threshold=structure_score_threshold,
                quality_weight=quality_weight,
                structure_weight=structure_weight,
                max_retries=max_retries,
                pdf_dpi=pdf_dpi,
                retry_pdf_dpi=retry_pdf_dpi,
                save_visualization=(not no_viz),
                output_dir=output_dir,
            ),
        )
        return pipeline.process_document(input_path, doc_id=doc_id)
    finally:
        adapter.close()