from __future__ import annotations

import json
import os
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
    temperature: float = 0.2,
) -> Dict[str, Any]:
    api_key = deepseek_api_key(root)
    if not api_key:
        raise HTTPException(status_code=503, detail="未配置 DEEPSEEK_API_KEY 或 backend/.deepseek_api_key")
    body = {
        "model": "deepseek-chat",
        "temperature": temperature,
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
    try:
        with urlrequest.urlopen(request, timeout=120) as response:
            raw = json.loads(response.read().decode("utf-8"))
    except urlerror.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise HTTPException(status_code=502, detail=f"DeepSeek API 错误: {detail[:400]}") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"DeepSeek 请求失败: {exc!s}") from exc

    try:
        message = raw["choices"][0]["message"]["content"]
        return extract_json_object(str(message))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"DeepSeek 返回解析失败: {exc!s}") from exc
