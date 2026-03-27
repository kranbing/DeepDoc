# 自托管 + 版面分块：先保证能下载/加载 PP-DocLayoutV3_safetensors
# 用法（在 PowerShell 中）:
#   cd "D:\AI\创新设计\deep-doc\GLM-OCR-0.1.4\examples"
#   .\run_layout_parse.ps1
#
# 若已手动下载版面模型到本地目录，编辑下面 $LayoutModelLocal 为实际路径后取消注释相关行。

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

# 国内/不稳定网络：走 HF 镜像（与 Docker 里 HF 类似）
$env:HF_ENDPOINT = "https://hf-mirror.com"
# 若曾设代理导致 10054，可先清空（按需保留 host.docker.internal 那类）
$env:HTTP_PROXY = ""
$env:HTTPS_PROXY = ""
$env:http_proxy = ""
$env:https_proxy = ""

# 版面模型放 CPU，单卡留给 Docker 里的 vLLM（可选）
$env:GLMOCR_LAYOUT_DEVICE = "cpu"

# 若已用 huggingface-cli / 脚本把模型下到本地，设为文件夹路径（含 preprocessor_config.json 等）
# $env:GLMOCR_LAYOUT_MODEL_DIR = "D:\models\PP-DocLayoutV3_safetensors"

glmocr parse examples/source/code.png `
  --output examples/output `
  --mode selfhosted `
  --config glmocr/config.yaml `
  --layout-device cpu
