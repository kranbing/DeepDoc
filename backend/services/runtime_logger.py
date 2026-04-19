from __future__ import annotations

import json
import logging
from contextvars import ContextVar
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict

from backend.services.paths import ROOT


_REQUEST_ID_CTX: ContextVar[str] = ContextVar("request_id", default="")

_LOG_DIR = ROOT / "backend" / "logs"
_APP_LOG_FILE = _LOG_DIR / "backend.log"
_EVENT_LOG_FILE = _LOG_DIR / "events.jsonl"
_ERROR_LOG_FILE = _LOG_DIR / "errors.jsonl"

_LOGGER_NAME = "deepdoc.backend"
_IS_CONFIGURED = False


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _redact_payload(value: Any) -> Any:
    if isinstance(value, dict):
        redacted: Dict[str, Any] = {}
        for key, item in value.items():
            key_lower = str(key).lower()
            if any(token in key_lower for token in ("api_key", "token", "secret", "password", "authorization")):
                redacted[key] = "***"
            else:
                redacted[key] = _redact_payload(item)
        return redacted
    if isinstance(value, list):
        return [_redact_payload(item) for item in value]
    if isinstance(value, str) and len(value) > 4096:
        return value[:4096] + "...(truncated)"
    return value


def _append_jsonl(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(payload, ensure_ascii=False) + "\n")


def configure_backend_logging(level: int = logging.INFO) -> None:
    global _IS_CONFIGURED
    if _IS_CONFIGURED:
        return

    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(_LOGGER_NAME)
    logger.setLevel(level)
    logger.propagate = False

    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    file_handler = RotatingFileHandler(
        _APP_LOG_FILE,
        encoding="utf-8",
        maxBytes=10 * 1024 * 1024,
        backupCount=3,
    )
    file_handler.setFormatter(fmt)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(fmt)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    _IS_CONFIGURED = True


def get_backend_logger() -> logging.Logger:
    configure_backend_logging()
    return logging.getLogger(_LOGGER_NAME)


def set_request_id(request_id: str) -> None:
    _REQUEST_ID_CTX.set(str(request_id or ""))


def clear_request_id() -> None:
    _REQUEST_ID_CTX.set("")


def current_request_id() -> str:
    return _REQUEST_ID_CTX.get()


def log_event(event: str, *, level: str = "INFO", **fields: Any) -> None:
    logger = get_backend_logger()
    payload: Dict[str, Any] = {
        "ts": utc_now(),
        "level": level.upper(),
        "event": event,
        "requestId": str(fields.pop("requestId", "") or current_request_id()),
    }
    for key, value in fields.items():
        payload[key] = _redact_payload(value)

    _append_jsonl(_EVENT_LOG_FILE, payload)
    if payload["level"] in {"ERROR", "CRITICAL"}:
        _append_jsonl(_ERROR_LOG_FILE, payload)

    line = json.dumps(payload, ensure_ascii=False)
    if payload["level"] == "DEBUG":
        logger.debug(line)
    elif payload["level"] == "WARNING":
        logger.warning(line)
    elif payload["level"] in {"ERROR", "CRITICAL"}:
        logger.error(line)
    else:
        logger.info(line)
