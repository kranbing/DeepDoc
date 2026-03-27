# GLM-OCR 网页栈一键启动说明（Windows PowerShell）
# 架构：Docker vLLM(8080) → glmocr.server(5002) → FastAPI(8000) → Vite 前端(3006)
#
# 前置：
#   1) 已 pip install -e ".[selfhosted,server]"（在 GLM-OCR-0.1.4 根目录）
#   2) 已安装 Node 18+ 与 pnpm 8+
#   3) Docker 中 vLLM 已在 8080 提供 glm-ocr（见 docs/自托管Docker与测试完整指南_zh.md）
#   4) glmocr/config.yaml 中 maas.enabled=false，ocr_api 指向 127.0.0.1:8080
#
# 用法：在 apps 目录执行  .\start-web-stack.ps1
#       或加 -Launch 会在新窗口启动 OCR 中间层、后端、前端（需已装依赖）

param(
    [switch]$Launch
)

$ErrorActionPreference = "Stop"
$AppsDir = $PSScriptRoot
$RepoRoot = Split-Path -Parent $AppsDir
Set-Location $AppsDir

Write-Host "仓库根目录: $RepoRoot" -ForegroundColor Cyan
Write-Host @"

=== 手动启动顺序（推荐开 3 个终端 + Docker）===

[1] Docker 已运行 vLLM 容器，映射 8080（略）

[2] OCR 中间层（Flask，对接 vLLM 与版面）
    cd `"$RepoRoot`"
    `$env:HF_ENDPOINT = 'https://hf-mirror.com'
    python -m glmocr.server --config glmocr/config.yaml
    # 默认 http://127.0.0.1:5002/glmocr/parse

[3] FastAPI 后端（必须在 apps\backend 目录，否则会 ModuleNotFoundError: app）
    cd `"$($AppsDir)\backend`"
    copy .env.example .env   # 首次：按需编辑 LAYOUT_OCR_URL
    uv sync                  # 若已装 uv；否则: pip install -e .
    uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
    # 或: .\run-backend.ps1
    # 无 uv 时: pip install -e . ; python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
    # 文档: http://127.0.0.1:8000/docs

[4] 前端（开发）
    cd `"$($AppsDir)\frontend`"
    pnpm install
    pnpm dev
    # 浏览器: http://127.0.0.1:3006 （Vite 把 /api 代理到 8000）

"@ -ForegroundColor Yellow

if (-not $Launch) {
    Write-Host "仅显示说明。若要尝试自动新开窗口启动 [2][3][4]，请执行: .\start-web-stack.ps1 -Launch" -ForegroundColor Green
    exit 0
}

function Start-OcrServer {
    Start-Process powershell -WorkingDirectory $RepoRoot -ArgumentList @(
        "-NoExit", "-Command",
        "`$env:HF_ENDPOINT='https://hf-mirror.com'; python -m glmocr.server --config glmocr/config.yaml"
    )
}
function Start-Backend {
    $be = Join-Path $AppsDir "backend"
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        Start-Process powershell -WorkingDirectory $be -ArgumentList @(
            "-NoExit", "-Command", "uv sync; uv run uvicorn app.main:app --host 0.0.0.0 --port 8000"
        )
    } else {
        Start-Process powershell -WorkingDirectory $be -ArgumentList @(
            "-NoExit", "-Command", "pip install -e .; python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
        )
    }
}
function Start-Frontend {
    $fe = Join-Path $AppsDir "frontend"
    Start-Process powershell -WorkingDirectory $fe -ArgumentList @(
        "-NoExit", "-Command", "pnpm dev"
    )
}

Write-Host "正在新开窗口：glmocr.server、FastAPI、Vite …" -ForegroundColor Green
Start-OcrServer
Start-Sleep -Seconds 2
Start-Backend
Start-Sleep -Seconds 2
Start-Frontend
Write-Host "完成。请确认 Docker vLLM 已在运行。" -ForegroundColor Green
