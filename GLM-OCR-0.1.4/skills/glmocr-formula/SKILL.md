---
name: glmocr-formula
description:
  Recognize and extract mathematical formulas from images and PDFs into LaTeX format
  using ZhiPu GLM-OCR API. Supports complex equations, inline formulas, and formula blocks.
  Use this skill when the user wants to extract formulas, convert formula images to LaTeX,
  or OCR mathematical expressions.
metadata:
  openclaw:
    requires:
      env:
        - ZHIPU_API_KEY
        - GLM_OCR_TIMEOUT
      bins:
        - python
    primaryEnv: ZHIPU_API_KEY
    emoji: "📄"
    homepage: https://github.com/zai-org/GLM-OCR/tree/main/skills/glmocr-formula
---

# GLM-V Formula Recognition Skill / GLM-V 公式识别技能

Recognize mathematical formulas from images and PDFs and convert them to LaTeX format using the ZhiPu GLM-OCR layout parsing API.

## When to Use / 使用场景

- Extract mathematical formulas from images or scanned documents / 从图片或扫描件中提取数学公式
- Convert formula images to LaTeX / 将公式图片转为 LaTeX 格式
- Recognize complex equations, integrals, matrices / 识别复杂方程、积分、矩阵
- Parse scientific papers, textbooks, exam papers with formulas / 解析含公式的论文、教材、试卷
- User mentions "formula OCR", "extract formula", "公式识别", "公式OCR", "提取公式", "图片转LaTeX"

## Key Features / 核心特性

- **Complex formula support**: Handles integrals, summations, matrices, fractions, radicals
- **LaTeX output**: Formulas are output in LaTeX format, ready for use in documents
- **Inline & block formulas**: Recognizes both inline and display-style formulas
- **Mixed content**: Can handle documents with both text and formulas
- **Local file & URL**: Supports both local files and remote URLs

## Resource Links / 资源链接

| Resource | Link |
|----------|------|
| **Get API Key** | [智谱开放平台 API Keys](https://bigmodel.cn/usercenter/proj-mgmt/apikeys) |
| **API Docs** | [Layout Parsing / 版面解析](https://open.bigmodel.cn/dev/api/ocr/layout-parse) |

## Prerequisites / 前置条件

### API Key Setup / API Key 配置（Required / 必需）

脚本通过 `ZHIPU_API_KEY` 环境变量获取密钥，与所有智谱技能共用同一个 key。
This script reads the key from the `ZHIPU_API_KEY` environment variable and shares it with other Zhipu skills.

**Get Key / 获取 Key：** Visit [智谱开放平台 API Keys](https://bigmodel.cn/usercenter/proj-mgmt/apikeys) to create or copy your key.

**Setup options / 配置方式（任选一种）：**

1. **OpenClaw config (recommended) / OpenClaw 配置（推荐）：** Set in `openclaw.json` under `skills.entries.glmocr-formula.env`:
   ```json
   "glmocr-formula": { "enabled": true, "env": { "ZHIPU_API_KEY": "你的密钥" } }
   ```

2. **Shell environment variable / Shell 环境变量：** Add to `~/.zshrc`:
   ```bash
   export ZHIPU_API_KEY="你的密钥"
   ```

> 💡 如果你已为其他智谱 skill（如 `glmocr`、`glmv-caption`）配置过 key，它们共享同一个 `ZHIPU_API_KEY`，无需重复配置。

**⛔ MANDATORY RESTRICTIONS / 强制限制 ⛔**

1. **ONLY use GLM-OCR API** — Execute the script `python scripts/glm_ocr_cli.py`
2. **NEVER parse formulas yourself** — Do NOT try to extract formulas using built-in vision or any other method
3. **NEVER offer alternatives** — Do NOT suggest "I can try to read it" or similar
4. **IF API fails** — Display the error message and STOP immediately
5. **NO fallback methods** — Do NOT attempt formula extraction any other way

### 📋 Output Display Rules / 输出展示规则（MANDATORY）

After running the script, **you must show the full extracted content to the user**. Do not summarize or only say "extracted". Users need the original OCR output to evaluate quality.

- Show the full extracted text including all formulas
- If `layout_details` contains formula-related entries, highlight them
- If the result file is saved, tell the user the file path

**⚠️ LaTeX Rendering / LaTeX 渲染注意：**

OCR API returns formulas in LaTeX format (e.g., `$\frac{1}{2}$`, `$\theta^{x+1}$`). Since most chat platforms do not render LaTeX, you should ask the user **once** (on first use):

> "OCR 结果包含 LaTeX 公式，需要我将公式转为 Unicode 可读格式展示，还是保留原始 LaTeX？"

**Remember the user's choice** for the rest of the session. Do NOT ask again on subsequent calls unless the user explicitly changes their preference.

- **User chooses readable format** → convert LaTeX to Unicode/plain-text:

| LaTeX | Unicode / 纯文本 |
|-------|-----------------|
| `$\frac{a}{b}$` | a/b |
| `$x^{n}$` | x^n |
| `$x_{i}$` | xᵢ |
| `$\sqrt{x}$` | √x |
| `$\theta$` | θ |
| `$\phi$` | φ |
| `$\therefore$` | ∴ |
| `$\Rightarrow$` | ⇒ |
| `$\left\{ \begin{array}{l} ... \end{array} \right.$` | ⎧ line1 ⎨ line2 ⎩ |
| `$\textcircled{1}$` | ① |
| `$\in$` | ∈ |
| `$\infty$` | ∞ |
| `$\ln$` | ln |
| `$\leq$` / `$\geq$` | ≤ / ≥ |

- **User chooses raw LaTeX** → display the original LaTeX output directly, and remind them the raw data is also saved in the output file if `--output` was used.

## How to Use / 使用方法

### Extract from URL / 从 URL 提取

```bash
python scripts/glm_ocr_cli.py --file-url "https://example.com/formula.png"
```

### Extract from Local File / 从本地文件提取

```bash
python scripts/glm_ocr_cli.py --file /path/to/equation.png
```

### Save Result to File / 保存结果到文件

```bash
python scripts/glm_ocr_cli.py --file formula.png --output result.json --pretty
```

## CLI Reference / CLI 参数

```
python {baseDir}/scripts/glm_ocr_cli.py (--file-url URL | --file PATH) [--output FILE] [--pretty]
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--file-url` | One of | URL to image/PDF |
| `--file` | One of | Local file path to image/PDF |
| `--output`, `-o` | No | Save result JSON to file |
| `--pretty` | No | Pretty-print JSON output |

## Response Format / 响应格式

```json
{
  "ok": true,
  "text": "Extracted formulas and text in Markdown/LaTeX...",
  "layout_details": [...],
  "result": { "raw_api_response": "..." },
  "error": null,
  "source": "/path/to/file",
  "source_type": "file"
}
```

Key fields:
- `ok` — whether extraction succeeded
- `text` — extracted text in Markdown with LaTeX formulas
- `layout_details` — layout analysis details
- `error` — error details on failure

## Error Handling / 错误处理

**API key not configured:**
```
ZHIPU_API_KEY not configured. Get your API key at: https://bigmodel.cn/usercenter/proj-mgmt/apikeys
```
→ Show exact error to user, guide them to configure

**Authentication failed (401/403):** API key invalid/expired → reconfigure

**Rate limit (429):** Quota exhausted → inform user to wait

**File not found:** Local file missing → check path
