# 使用自托管 vLLM 对 paper.png 做分块解析（layout + OCR），结果写入 examples/output
# 依赖：Docker 中 OCR/vLLM 已启动且可访问；默认 http://127.0.0.1:8080
#
# 若端口不是 8080，先设置再运行，例如：
#   $env:GLMOCR_OCR_API_PORT = "8000"
#   .\parse_paper_to_output.ps1

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path $PSScriptRoot -Parent
Set-Location $repoRoot

if (-not $env:GLMOCR_OCR_API_HOST) { $env:GLMOCR_OCR_API_HOST = "127.0.0.1" }
if (-not $env:GLMOCR_OCR_API_PORT) { $env:GLMOCR_OCR_API_PORT = "8080" }

Write-Host "OCR API: http://$($env:GLMOCR_OCR_API_HOST):$($env:GLMOCR_OCR_API_PORT)"
Write-Host "Input:   examples/source/paper.png"
Write-Host "Output:  examples/output"
Write-Host ""

python -m glmocr parse "examples/source/paper.png" --mode selfhosted -o "examples/output" --log-level INFO
