from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def setup_logger(
    log_dir: Path,
    name: str = "ocr_pipeline",
    level: int = logging.INFO,
    file_name: str = "pipeline.log",
) -> logging.Logger:
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    log_path = (log_dir / file_name).resolve()
    has_file_handler = any(
        isinstance(handler, logging.FileHandler)
        and Path(getattr(handler, "baseFilename", "")).resolve() == log_path
        for handler in logger.handlers
    )
    if not has_file_handler:
        fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(fmt)
        logger.addHandler(file_handler)

    has_stream_handler = any(
        isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler)
        for handler in logger.handlers
    )
    if not has_stream_handler:
        fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(fmt)
        logger.addHandler(stream_handler)

    return logger


class StatusEventLogger:
    """Append-only JSONL event logger for document status transitions."""

    def __init__(self, output_file: Path) -> None:
        self.output_file = output_file
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

    def log_event(
        self,
        *,
        doc_id: str,
        status: str,
        stage: str,
        source_format: str,
        message: str,
        payload: Dict[str, Any] | None = None,
    ) -> None:
        event: Dict[str, Any] = {
            "updatedAt": _utc_now(),
            "docId": doc_id,
            "status": status,
            "stage": stage,
            "sourceFormat": source_format,
            "message": message,
        }
        if isinstance(payload, dict) and payload:
            event["payload"] = payload
        with self.output_file.open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(event, ensure_ascii=False) + "\n")


def setup_status_event_logger(log_dir: Path, file_name: str = "status_events.jsonl") -> StatusEventLogger:
    return StatusEventLogger(log_dir / file_name)
