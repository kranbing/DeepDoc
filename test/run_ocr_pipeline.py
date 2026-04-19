from __future__ import annotations

import argparse
import json

from ocr_pipeline.runner import run_pipeline


def build_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="OCR test and quality-evaluation pipeline")
    parser.add_argument("--input", required=True, help="Input image or PDF path")
    parser.add_argument("--output-dir", default="./output/pipeline", help="Output directory")
    parser.add_argument("--doc-id", default=None, help="Optional document id")

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

    return parser.parse_args()


def main() -> int:
    args = build_args()

    result = run_pipeline(
        input_path=args.input,
        output_dir=args.output_dir,
        doc_id=args.doc_id,
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
    )
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
