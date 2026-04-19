from __future__ import annotations

import argparse
import json

from ocr_pipeline.unified_batch import UnifiedBatchConfig, run_unified_batch


def build_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Unified batch indexing for PDF/image/XLSX/DOCX")
    parser.add_argument("--input", required=True, help="Input file path or directory path")
    parser.add_argument("--output-dir", default="./output/pipeline_unified", help="Batch output directory")
    parser.add_argument("--batch-id", default=None, help="Optional batch id")
    parser.add_argument("--recurse", action="store_true", help="Recurse when input is a directory")
    parser.add_argument("--continue-on-error", action="store_true", help="Continue processing when one document fails")

    parser.add_argument("--mode", default="maas", choices=["maas", "selfhosted", "mock"], help="OCR backend mode")
    parser.add_argument("--api-key", default=None, help="API key for cloud mode")
    parser.add_argument("--config-path", default=None, help="glmocr config path")
    parser.add_argument("--env-file", default=None, help="Path to .env")
    parser.add_argument("--enable-mock-fallback", action="store_true", help="Use mock adapter when primary OCR fails")
    parser.add_argument("--mock-noisy", action="store_true", help="Generate noisy mock OCR output for robustness testing")

    parser.add_argument("--score-threshold", type=float, default=0.7, help="Retry trigger threshold")
    parser.add_argument("--final-score-threshold", type=float, default=0.85, help="Final score retry threshold")
    parser.add_argument("--structure-score-threshold", type=float, default=0.8, help="Structure score retry threshold")
    parser.add_argument("--quality-weight", type=float, default=0.7, help="Weight of quality_score in final_score")
    parser.add_argument("--structure-weight", type=float, default=0.3, help="Weight of structure_score in final_score")
    parser.add_argument("--max-retries", type=int, default=3, help="Max retry attempts per page")
    parser.add_argument("--pdf-dpi", type=int, default=200, help="PDF render DPI")
    parser.add_argument("--retry-pdf-dpi", type=int, default=280, help="PDF retry render DPI")
    parser.add_argument("--no-viz", action="store_true", help="Disable error visualization output")

    parser.add_argument("--max-rows-per-chunk", type=int, default=20, help="Maximum rows in each Excel chunk")
    parser.add_argument("--header-search-rows", type=int, default=6, help="Rows used for Excel header inference")
    return parser.parse_args()


def main() -> int:
    args = build_args()
    config = UnifiedBatchConfig(
        input_path=args.input,
        output_dir=args.output_dir,
        batch_id=args.batch_id,
        recurse=args.recurse,
        continue_on_error=args.continue_on_error,
        mode=args.mode,
        api_key=args.api_key,
        config_path=args.config_path,
        env_file=args.env_file,
        enable_mock_fallback=args.enable_mock_fallback,
        mock_noisy=args.mock_noisy,
        score_threshold=args.score_threshold,
        final_score_threshold=args.final_score_threshold,
        structure_score_threshold=args.structure_score_threshold,
        quality_weight=args.quality_weight,
        structure_weight=args.structure_weight,
        max_retries=args.max_retries,
        pdf_dpi=args.pdf_dpi,
        retry_pdf_dpi=args.retry_pdf_dpi,
        no_viz=args.no_viz,
        max_rows_per_chunk=args.max_rows_per_chunk,
        header_search_rows=args.header_search_rows,
    )

    result = run_unified_batch(config)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    failed = int((result.get("summary") or {}).get("failed") or 0)
    aborted = bool((result.get("summary") or {}).get("aborted"))
    if aborted:
        return 3
    if failed > 0:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
