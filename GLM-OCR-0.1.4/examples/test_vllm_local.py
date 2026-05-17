#!/usr/bin/env python3
"""测试本地 vLLM 部署的 GLM-OCR（OpenAI 兼容 /v1/chat/completions）。

用法（在仓库根目录或 examples 目录下）:
  python test_vllm_local.py
  python test_vllm_local.py --image source/code.png
  python test_vllm_local.py --output-dir output
  python test_vllm_local.py --base-url http://127.0.0.1:8080 --model glm-ocr

默认图片: examples/source/code.png
默认结果: examples/output/<图片主名>_ocr.md

依赖: 仅标准库（urllib），无需 pip install requests。
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path


def build_payload(image_path: Path, model: str, max_tokens: int, temperature: float) -> bytes:
    data = image_path.read_bytes()
    mime = "image/png"
    if image_path.suffix.lower() in (".jpg", ".jpeg"):
        mime = "image/jpeg"
    elif image_path.suffix.lower() == ".webp":
        mime = "image/webp"
    b64 = base64.b64encode(data).decode("ascii")
    data_url = f"data:{mime};base64,{b64}"

    body = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": data_url},
                    },
                    {
                        "type": "text",
                        "text": (
                            "Recognize the text in the image and output in Markdown format. "
                            "Preserve the original layout (headings/paragraphs/tables/formulas). "
                            "Do not fabricate content that does not exist in the image."
                        ),
                    },
                ],
            }
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    return json.dumps(body, ensure_ascii=False).encode("utf-8")


def main() -> int:
    here = Path(__file__).resolve().parent
    default_img = here / "source" / "code.png"

    p = argparse.ArgumentParser(description="测试本地 GLM-OCR (vLLM OpenAI API)")
    p.add_argument(
        "--image",
        type=Path,
        default=default_img,
        help=f"图片路径（默认: {default_img}",
    )
    p.add_argument(
        "--base-url",
        default="http://127.0.0.1:8080",
        help="vLLM 服务地址，无尾部斜杠",
    )
    p.add_argument("--model", default="glm-ocr", help="与 --served-model-name 一致")
    p.add_argument("--max-tokens", type=int, default=4096)
    p.add_argument("--temperature", type=float, default=0.1)
    p.add_argument(
        "--output-dir",
        type=Path,
        default=here / "output",
        help="识别结果 Markdown 保存目录（默认: examples/output）",
    )
    p.add_argument(
        "--output",
        type=Path,
        default=None,
        help="结果文件完整路径；不指定则用 <output-dir>/<图片主名>_ocr.md",
    )
    args = p.parse_args()

    if not args.image.is_file():
        print(f"找不到图片: {args.image}", file=sys.stderr)
        return 1

    url = args.base_url.rstrip("/") + "/v1/chat/completions"
    payload = build_payload(
        args.image, args.model, args.max_tokens, args.temperature
    )

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )

    print(f"POST {url}")
    print(f"图片: {args.image.resolve()}")
    print("请求中（大图可能较慢）…\n")

    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.reason}", file=sys.stderr)
        err_body = e.read().decode("utf-8", errors="replace")
        print(err_body, file=sys.stderr)
        return 1
    except urllib.error.URLError as e:
        print(f"连接失败: {e.reason}", file=sys.stderr)
        return 1

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        print("响应非 JSON:", raw[:2000], file=sys.stderr)
        return 1

    # 打印完整 JSON（便于调试）；只要正文可看 choices
    choices = data.get("choices") or []
    if choices:
        content = (choices[0].get("message") or {}).get("content", "")
        print("========== 识别结果 (content) ==========")
        print(content)
        print("\n========== 完整 JSON（节选 usage）==========")
        print(json.dumps({"usage": data.get("usage"), "model": data.get("model")}, ensure_ascii=False, indent=2))

        out_dir = args.output_dir.resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        if args.output is not None:
            out_file = args.output.resolve()
            out_file.parent.mkdir(parents=True, exist_ok=True)
        else:
            out_file = out_dir / f"{args.image.stem}_ocr.md"

        out_file.write_text(content, encoding="utf-8")
        print(f"\n已保存 Markdown: {out_file}")

        meta_path = out_file.parent / f"{out_file.stem}_meta.json"
        meta_path.write_text(
            json.dumps(
                {"usage": data.get("usage"), "model": data.get("model"), "image": str(args.image.resolve())},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"已保存元数据: {meta_path}")
    else:
        print(json.dumps(data, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
