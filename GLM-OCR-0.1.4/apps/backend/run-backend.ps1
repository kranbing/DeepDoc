# 在 apps/backend 目录启动 FastAPI（勿在仓库根目录执行）
# 用法：cd apps\backend  ;  .\run-backend.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path "app\main.py")) {
    Write-Host "错误：请在 apps\backend 目录下执行本脚本。" -ForegroundColor Red
    exit 1
}

if (Get-Command uv -ErrorAction SilentlyContinue) {
    Write-Host "使用 uv run uvicorn ..." -ForegroundColor Cyan
    uv sync
    uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
} else {
    Write-Host "未检测到 uv，使用 pip + python -m uvicorn ..." -ForegroundColor Cyan
    pip install -e .
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
}
