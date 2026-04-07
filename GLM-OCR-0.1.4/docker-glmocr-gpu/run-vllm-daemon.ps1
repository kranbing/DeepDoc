# GLM-OCR vLLM 后台常驻容器（关闭 PowerShell 窗口后仍继续跑，除非手动 docker stop）
# 用法：在脚本所在目录执行  .\run-vllm-daemon.ps1
# 按需修改下面变量

$ContainerName = "glmocr-vllm"
$Image = "vllm/vllm-openai:nightly"
$HostPort = 8080
$HfCacheHost = "D:\docker_cache\hf"   # 宿主机 HuggingFace 缓存目录，不存在请先创建

# —— 省显存（KV 与上下文长度强相关；仍 OOM 可再降 MaxModelLen 或 GpuMemUtil）——
$MaxModelLen = 8192                 # 默认可达 131072，显存不够务必改小：4096 / 2048
$GpuMemUtil = 0.75                  # 单卡显存占用比例，可试 0.65～0.85
$MaxNumSeqs = 4                     # 并发序列数上限，越小越省显存

# 若已有同名容器，先删再建（避免名字冲突）
$exists = docker ps -aq -f "name=^/${ContainerName}$"
if ($exists) {
    Write-Host "正在删除旧容器: $ContainerName"
    docker rm -f $ContainerName 2>$null
}

docker run -d `
  --name $ContainerName `
  --gpus all `
  --shm-size 16g `
  --restart unless-stopped `
  -p "${HostPort}:8080" `
  -e HTTP_PROXY= -e HTTPS_PROXY= -e http_proxy= -e https_proxy= `
  -e NO_PROXY=* `
  -e HF_ENDPOINT=https://hf-mirror.com `
  -v "${HfCacheHost}:/root/.cache/huggingface" `
  $Image `
  zai-org/GLM-OCR `
  --allowed-local-media-path / `
  --port 8080 `
  --max-model-len $MaxModelLen `
  --gpu-memory-utilization $GpuMemUtil `
  --max-num-seqs $MaxNumSeqs `
  --served-model-name glm-ocr

if ($LASTEXITCODE -eq 0) {
    Write-Host "已后台启动: $ContainerName  端口 http://127.0.0.1:${HostPort}"
    Write-Host "查看日志: docker logs -f $ContainerName"
    Write-Host "停止:     docker stop $ContainerName"
    Write-Host "再启动:   docker start $ContainerName"
} else {
    Write-Host "启动失败，请根据上方 docker 报错排查。"
}
