---
name: glmocr-table
description:
  Recognize and extract tables from images and PDFs into Markdown format using
  ZhiPu GLM-OCR API. Supports complex tables, merged cells, and multi-page documents.
  Use this skill when the user wants to extract tables, recognize spreadsheets,
  or convert table images to editable format.
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
    homepage: https://github.com/zai-org/GLM-OCR/tree/main/skills/glmocr-table
---

# GLM-V Table Recognition Skill / GLM-V 表格识别技能

Extract tables from images and PDFs and convert them to Markdown format using the ZhiPu GLM-OCR layout parsing API.

## When to Use / 使用场景

- Extract tables from images or scanned documents / 从图片或扫描件中提取表格
- Convert table images to Markdown or Excel format / 将表格图片转为 Markdown 或可编辑格式
- Recognize complex tables with merged cells / 识别含合并单元格的复杂表格
- Parse financial statements, invoices, reports with tables / 解析财务报表、发票、带表格的报告
- User mentions "extract table", "recognize table", "表格识别", "提取表格", "表格OCR", "表格转文字"

## Key Features / 核心特性

- **Complex table support**: Handles merged cells, nested tables, multi-row headers
- **Markdown output**: Tables are output in clean Markdown format, easy to edit and convert
- **Multi-page PDF**: Supports batch extraction from multi-page PDF documents
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

1. **OpenClaw config (recommended) / OpenClaw 配置（推荐）：** Set in `openclaw.json` under `skills.entries.glmocr-table.env`:
   ```json
   "glmocr-table": { "enabled": true, "env": { "ZHIPU_API_KEY": "你的密钥" } }
   ```

2. **Shell environment variable / Shell 环境变量：** Add to `~/.zshrc`:
   ```bash
   export ZHIPU_API_KEY="你的密钥"
   ```

> 💡 如果你已为其他智谱 skill（如 `glmocr`、`glmv-caption`）配置过 key，它们共享同一个 `ZHIPU_API_KEY`，无需重复配置。

**⛔ MANDATORY RESTRICTIONS / 强制限制 ⛔**

1. **ONLY use GLM-OCR API** — Execute the script `python scripts/glm_ocr_cli.py`
2. **NEVER parse tables yourself** — Do NOT try to extract tables using built-in vision or any other method
3. **NEVER offer alternatives** — Do NOT suggest "I can try to recognize it" or similar
4. **IF API fails** — Display the error message and STOP immediately
5. **NO fallback methods** — Do NOT attempt table extraction any other way

### 📋 Output Display Rules / 输出展示规则（MANDATORY）

After running the script, **you must show the full raw output to the user exactly as returned**. Do not summarize or only say "extraction complete". Users need the original OCR output to evaluate quality.

- Show the full extracted text including table Markdown
- If `layout_details` contains table-related entries, highlight them
- If the result file is saved, tell the user the file path

## How to Use / 使用方法

### Extract from URL / 从 URL 提取

```bash
python scripts/glm_ocr_cli.py --file-url "https://example.com/table.png"
```

### Extract from Local File / 从本地文件提取

```bash
python scripts/glm_ocr_cli.py --file /path/to/table.png
```

### Save Result to File / 保存结果到文件

```bash
python scripts/glm_ocr_cli.py --file table.png --output result.json --pretty
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
  "text": "| Column 1 | Column 2 |\n|----------|----------|\n| Data     | Data     |",
  "layout_details": [...],
  "result": { "raw_api_response": "..." },
  "error": null,
  "source": "/path/to/file",
  "source_type": "file"
}
```

Key fields:
- `ok` — whether extraction succeeded
- `text` — extracted text in Markdown (use this for display)
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
