param(
    [string]$ContainerName = "glmocr-vllm",
    [string]$Image = "vllm-glmocr-gpu:patched-v17",
    [int]$HostPort = 8080,
    [string]$HfCacheHost = "D:\docker_cache\hf",
    [int]$MaxModelLen = 8192,
    [double]$GpuMemUtil = 0.7,
    [int]$MaxNumSeqs = 1,
    [string]$Dtype = "float16",
    [switch]$EnableRestartPolicy
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "Starting GLM-OCR vLLM container with conservative memory settings..." -ForegroundColor Cyan
Write-Host "max-model-len=$MaxModelLen gpu-memory-utilization=$GpuMemUtil max-num-seqs=$MaxNumSeqs dtype=$Dtype"

if (!(Test-Path -LiteralPath $HfCacheHost)) {
    New-Item -ItemType Directory -Force -Path $HfCacheHost | Out-Null
}

$exists = docker ps -aq -f "name=^/${ContainerName}$"
if ($exists) {
    Write-Host "Removing old container: $ContainerName"
    docker rm -f $ContainerName | Out-Null
}

$restartPolicy = if ($EnableRestartPolicy) { "unless-stopped" } else { "no" }

$dockerArgs = @(
    "run",
    "-d",
    "--name", $ContainerName,
    "--gpus", "all",
    "--shm-size", "16g",
    "--restart", $restartPolicy,
    "-p", "${HostPort}:8080",
    "-e", "HTTP_PROXY=",
    "-e", "HTTPS_PROXY=",
    "-e", "http_proxy=",
    "-e", "https_proxy=",
    "-e", "NO_PROXY=*",
    "-e", "HF_ENDPOINT=https://hf-mirror.com",
    "-v", "${HfCacheHost}:/root/.cache/huggingface",
    $Image,
    "zai-org/GLM-OCR",
    "--allowed-local-media-path", "/",
    "--port", "8080",
    "--max-model-len", "$MaxModelLen",
    "--gpu-memory-utilization", "$GpuMemUtil",
    "--max-num-seqs", "$MaxNumSeqs",
    "--dtype", $Dtype,
    "--enforce-eager",
    "--served-model-name", "glm-ocr"
)

Write-Host ("docker " + ($dockerArgs -join " ")) -ForegroundColor DarkGray
docker @dockerArgs

if ($LASTEXITCODE -eq 0) {
    Write-Host "Started in background: $ContainerName at http://127.0.0.1:${HostPort}" -ForegroundColor Green
    Write-Host "View logs: docker logs -f $ContainerName"
    Write-Host "Stop:      docker stop $ContainerName"
    Write-Host "Start:     docker start $ContainerName"
} else {
    Write-Host "Start failed, please check docker error output above." -ForegroundColor Red
    exit $LASTEXITCODE
}
