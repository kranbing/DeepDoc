from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional
from urllib import error as urlerror
from urllib import request as urlrequest

from fastapi import HTTPException


def deepseek_api_key(root: Path) -> Optional[str]:
    key = (os.environ.get("DEEPSEEK_API_KEY") or "").strip()
    if key:
        return key
    local = root / "backend" / ".deepseek_api_key"
    if local.is_file():
        try:
            text = local.read_text(encoding="utf-8").strip()
        except OSError:
            return None
        return text or None
    return None


def extract_json_object(text: str) -> Dict[str, Any]:
    raw = (text or "").strip()
    if not raw:
        raise ValueError("empty response")
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    start = raw.find("{")
    end = raw.rfind("}")
    if start >= 0 and end > start:
        data = json.loads(raw[start : end + 1])
        if isinstance(data, dict):
            return data
    raise ValueError("no valid json object found")


def deepseek_chat_json(
    root: Path,
    system_prompt: str,
    user_prompt: str,
    *,
    model: str = "deepseek-chat",
    temperature: float = 0.2,
    top_p: float = 0.9,
    max_tokens: int = 768,
    timeout_seconds: int = 120,
    max_retries: int = 2,
) -> Dict[str, Any]:
    api_key = deepseek_api_key(root)
    if not api_key:
        raise HTTPException(status_code=503, detail="Missing DEEPSEEK_API_KEY or backend/.deepseek_api_key")

    body = {
        "model": model,
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    request = urlrequest.Request(
        "https://api.deepseek.com/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    raw: Dict[str, Any] = {}
    attempts = max(1, int(max_retries or 0) + 1)
    for attempt in range(attempts):
        try:
            with urlrequest.urlopen(request, timeout=max(1, int(timeout_seconds or 120))) as response:
                raw = json.loads(response.read().decode("utf-8"))
            break
        except urlerror.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            status = int(getattr(exc, "code", 0) or 0)
            retryable = status == 429 or 500 <= status < 600
            if retryable and attempt < attempts - 1:
                time.sleep(min(8.0, 0.8 * (2**attempt)))
                continue
            raise HTTPException(status_code=502, detail=f"DeepSeek API error status={status}: {detail[:400]}") from exc
        except TimeoutError as exc:
            if attempt < attempts - 1:
                time.sleep(min(8.0, 0.8 * (2**attempt)))
                continue
            raise HTTPException(status_code=504, detail=f"DeepSeek request timeout after {timeout_seconds}s") from exc
        except Exception as exc:
            if attempt < attempts - 1:
                time.sleep(min(8.0, 0.8 * (2**attempt)))
                continue
            raise HTTPException(status_code=502, detail=f"DeepSeek request failed: {exc!s}") from exc

    try:
        message = raw["choices"][0]["message"]["content"]
        if not str(message or "").strip():
            raise ValueError("empty model content")
        return extract_json_object(str(message))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"DeepSeek response parse failed: {exc!s}") from exc
