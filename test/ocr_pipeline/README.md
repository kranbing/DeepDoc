# OCR Test & Quality Pipeline

This folder contains a runnable OCR test pipeline with:

- Input handling for image/PDF
- OCR adapter abstraction
- Post-processing (reading-order sort, line merge, paragraph merge)
- No-GT quality scoring
- Structure scoring (format/title/paragraph/reading-order risks)
- Multi-strategy retry
- Structured output and performance stats
- Optional error-region visualization
- Mock fallback adapter for offline pipeline testing

## Quick Start

From `test` directory:

```powershell
# Unified OCR entrypoint (select maas / selfhosted / mock via --mode)
python .\run_ocr_pipeline.py --input .\example\ocr_demo.png --mode maas

# selfhosted mode
python .\run_ocr_pipeline.py --input .\example\ocr_demo.png --mode selfhosted

# keep pipeline runnable when local OCR service is temporarily unavailable
python .\run_ocr_pipeline.py --input .\example\ocr_demo.png --mode selfhosted --enable-mock-fallback

# Excel parsing entrypoint (outputs QA-friendly structured chunks)
python .\run_excel_pipeline.py --input .\example\demo_table.xlsx

# fully local mock mode (no OCR service required)
python .\run_ocr_pipeline.py --input .\example\ocr_demo.png --mode mock --mock-noisy

# use real OCR first, fall back to mock when OCR fails
python .\run_ocr_pipeline.py --input .\example\ocr_demo.png --mode selfhosted --enable-mock-fallback
```

Notes:

- The OCR entrypoint switches behavior via `--mode`.
- `--mode maas` reads `pipeline.maas` (`api_key/api_url/model`).
- `--mode selfhosted` reads `pipeline.ocr_api` (`api_host/api_port/model`).
- Passing `--api-key` is optional.
- Config lookup order: current `config.yaml` -> `test/config.yaml` -> `GLM-OCR-0.1.4/glmocr/config.yaml`.

## Scoring

- `quality_score`: no-GT quality score using char/line/block/garbled/empty/overlap metrics
- `structure_score`: structure health score
	- HTML tag pollution or markdown+HTML mixed content
	- heading anomalies (`##` repeated in one line, heading not separated)
	- paragraph anomalies (too long, missing punctuation)
	- dual-column reading-order risk
- `final_score = 0.7 * quality_score + 0.3 * structure_score`

Retry trigger:

- `final_score < 0.85` OR `structure_score < 0.8`

## Main Modules

- `adapters.py`: OCR adapter interface and GLM-OCR adapter
- `pipeline.py`: end-to-end orchestration
- `postprocess.py`: sorting and merging logic
- `quality.py`: no-GT score and issue detection
- `structure_quality.py`: structure score and structural issue detection
- `retry_strategies.py`: enhancement/local/PDF retries
- `visualization.py`: bbox error visualization output
- `adapters.py`: GLM adapter + mock adapter + failover adapter
- `custom_adapter_template.py`: integration template for custom OCR backends
- `excel_adapter.py`: Excel adapter (workbook/sheet/cell reader)
- `excel_postprocess.py`: Excel chunk builder and quality checks

## Excel Chunk Schema

Example:

```json
{
	"type": "excel_chunk",
	"sheet": "Sheet1",
	"range": "A2:D21",
	"headers": ["Date", "Category", "Quantity", "Amount"],
	"rows": [
		{"row_index": 2, "values": {"Date": "2026-04-01", "Category": "A", "Quantity": 12, "Amount": 329.5}}
	],
	"text": "Sheet: Sheet1\nRange: A2:D21\n...",
	"position": {"sheet": "Sheet1", "row_start": 2, "row_end": 21, "col_start": 1, "col_end": 4},
	"structure": {"row_count": 20, "col_count": 4, "has_header": true}
}
```
