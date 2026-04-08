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
# maas sibling entrypoint (reads MaaS API settings from config.yaml/.env; no --api-key required)
python .\run_ocr_pipeline_maas.py --input .\example\ocr_demo.png

# selfhosted local test entry (reads API host/port from local config.yaml)
python .\run_ocr_pipeline_selfhosted.py --input .\example\ocr_demo.png

# keep pipeline runnable when local OCR service is temporarily unavailable
python .\run_ocr_pipeline_selfhosted.py --input .\example\ocr_demo.png --enable-mock-fallback

# fully local mock mode (no OCR service required)
python .\run_ocr_pipeline.py --input .\example\ocr_demo.png --mode mock --mock-noisy

# use real OCR first, fall back to mock when OCR fails
python .\run_ocr_pipeline.py --input .\example\ocr_demo.png --mode selfhosted --enable-mock-fallback
```

Notes:

- The maas entry reads `pipeline.maas` (`api_key/api_url/model`).
- The selfhosted entry reads `pipeline.ocr_api` (`api_host/api_port/model`).
- Both sibling entrypoints do not require passing `--api-key`.
- Config lookup order: current `config.yaml` -> `test/config.yaml` -> `GLM-OCR-0.1.4/glmocr/config.yaml`.

Compatibility:

- `run_ocr_pipeline.py` remains available as a generic `--mode` entrypoint.

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
