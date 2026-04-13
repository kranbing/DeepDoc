#!/usr/bin/env python3
"""通过本机 vLLM :8080（/v1/chat/completions）对 PDF 做 GLM-OCR。

vLLM 不接受整份 PDF，只能传图片；本脚本用 pypdfium2 逐页渲染为 PNG 再请求。

用法（在已安装 glmocr 或 pip install pypdfium2 的环境中）:
  python test_vllm_pdf.py --pdf "D:/path/to/file.pdf"
  python test_vllm_pdf.py --pdf "D:/path/to/file.pdf" --base-url http://127.0.0.1:8080 --model glm-ocr
  python test_vllm_pdf.py --pdf file.pdf --max-pages 3

依赖: pypdfium2（与仓库根 pyproject 中 glmocr 依赖一致）
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path


def _need_pypdfium2():
    try:
        import pypdfium2 as pdfium  # noqa: F401

        return pdfium
    except ImportError:
        print(
            "缺少 pypdfium2。请在 GLM-OCR 仓库根执行: pip install pypdfium2",
            file=sys.stderr,
        )
        raise SystemExit(1)


def pdf_pages_to_png_bytes(pdf_path: Path, max_pages: int | None, scale: float) -> list[bytes]:
    pdfium = _need_pypdfium2()
    doc = pdfium.PdfDocument(str(pdf_path))
    n = len(doc)
    limit = n if max_pages is None else min(n, max_pages)
    out: list[bytes] = []
    for i in range(limit):
        page = doc[i]
        bitmap = page.render(scale=scale)
        pil = bitmap.to_pil()
        buf = io.BytesIO()
        pil.save(buf, format="PNG")
        out.append(buf.getvalue())
    return out


def build_payload(png_bytes: bytes, model: str, max_tokens: int, temperature: float) -> bytes:
    b64 = base64.b64encode(png_bytes).decode("ascii")
    data_url = f"data:image/png;base64,{b64}"
    body = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": data_url}},
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


def post_ocr(
    base_url: str, png_bytes: bytes, model: str, max_tokens: int, temperature: float, timeout: int
) -> str:
    url = base_url.rstrip("/") + "/v1/chat/completions"
    payload = build_payload(png_bytes, model, max_tokens, temperature)
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
    data = json.loads(raw)
    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError(f"无 choices 字段: {raw[:2000]}")
    return (choices[0].get("message") or {}).get("content", "") or ""


def main() -> int:
    here = Path(__file__).resolve().parent
    p = argparse.ArgumentParser(description="PDF → 逐页 PNG → vLLM GLM-OCR (8080)")
    p.add_argument("--pdf", type=Path, required=True, help="PDF 绝对或相对路径")
    p.add_argument("--base-url", default="http://127.0.0.1:8080", help="vLLM 地址")
    p.add_argument("--model", default="glm-ocr", help="与 --served-model-name 一致")
    p.add_argument("--max-tokens", type=int, default=4096)
    p.add_argument("--temperature", type=float, default=0.1)
    p.add_argument("--max-pages", type=int, default=None, help="最多处理页数，默认全部")
    p.add_argument(
        "--scale",
        type=float,
        default=2.0,
        help="渲染缩放（越大越清晰，请求越慢）",
    )
    p.add_argument("--timeout", type=int, default=600, help="单页请求超时秒数")
    p.add_argument(
        "--output-dir",
        type=Path,
        default=here / "output",
        help="合并 Markdown 输出目录",
    )
    p.add_argument("--output", type=Path, default=None, help="合并结果完整路径")
    args = p.parse_args()

    pdf_path = args.pdf.expanduser().resolve()
    if not pdf_path.is_file():
        print(f"找不到 PDF: {pdf_path}", file=sys.stderr)
        return 1

    print(f"PDF: {pdf_path}")
    pages = pdf_pages_to_png_bytes(pdf_path, args.max_pages, args.scale)
    print(f"共 {len(pages)} 页，POST {args.base_url}/v1/chat/completions …\n")

    sections: list[str] = []
    for idx, png in enumerate(pages, start=1):
        print(f"--- 第 {idx}/{len(pages)} 页 ---")
        try:
            md = post_ocr(
                args.base_url,
                png,
                args.model,
                args.max_tokens,
                args.temperature,
                args.timeout,
            )
        except urllib.error.HTTPError as e:
            print(f"HTTP {e.code}: {e.reason}", file=sys.stderr)
            print(e.read().decode("utf-8", errors="replace"), file=sys.stderr)
            return 1
        except urllib.error.URLError as e:
            print(f"连接失败: {e.reason}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"请求失败: {e}", file=sys.stderr)
            return 1
        sections.append(f"## Page {idx}\n\n{md.strip()}\n")

    merged = "\n\n".join(sections)
    print("\n========== 合并预览（前 2000 字符）==========")
    print(merged[:2000] + ("…" if len(merged) > 2000 else ""))

    out_dir = args.output_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.output is not None:
        out_file = args.output.resolve()
        out_file.parent.mkdir(parents=True, exist_ok=True)
    else:
        out_file = out_dir / f"{pdf_path.stem}_ocr.md"
    out_file.write_text(merged, encoding="utf-8")
    print(f"\n已保存: {out_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
