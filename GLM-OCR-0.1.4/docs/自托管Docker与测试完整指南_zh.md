# GLM-OCR 自托管：Docker（GPU）+ 模型下载 + 测试完整指南

本文档汇总 **Windows + Docker Desktop + NVIDIA GPU** 下 **GLM-OCR（vLLM）** 从构建镜像、拉取模型、启动服务到 **整页 OCR** 与 **SDK 版面分块** 的实操步骤与常见问题。

---

## 目录

1. [前置条件](#1-前置条件)
2. [构建自定义镜像](#2-构建自定义镜像)
3. [Docker 镜像加速（可选）](#3-docker-镜像加速可选)
4. [启动 vLLM 服务（GPU）](#4-启动-vllm-服务gpu)
5. [模型下载与缓存](#5-模型下载与缓存)
6. [验证服务是否就绪](#6-验证服务是否就绪)
7. [Python 直连 API 测试（整页 OCR）](#7-python-直连-api-测试整页-ocr)
8. [SDK 流水线：版面分块 + 输出](#8-sdk-流水线版面分块--输出)
9. [版面模型 PP-DocLayout（分块必备）](#9-版面模型-pp-doclayout分块必备)
10. [故障排查速查](#10-故障排查速查)

---

## 1. 前置条件

- **Windows 10/11**，已安装 **Docker Desktop**（启用 **WSL2 后端** 更稳）。
- **NVIDIA 显卡驱动** 正常；Docker 能使用 GPU（`docker run --gpus all` 可用）。
- 磁盘空间：镜像 + GLM-OCR 权重 +（可选）版面模型，建议预留 **30GB+**。
- **PowerShell** 执行策略允许运行脚本（如需要）：`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`。

---

## 2. 构建自定义镜像

仓库内 **`docker-glmocr-gpu/Dockerfile`** 基于 **`vllm/vllm-openai:v0.17.1`**，并在镜像内升级 **`transformers` / `huggingface_hub`**，以兼容 GLM-OCR 远程模型代码。

在项目根目录 **`GLM-OCR-0.1.4\docker-glmocr-gpu`** 下执行：

```powershell
cd "D:\你的路径\GLM-OCR-0.1.4\docker-glmocr-gpu"

docker build `
  --build-arg PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple `
  --no-cache `
  -t vllm-glmocr-gpu:patched-v17 .
```

说明：

- **`PIP_INDEX_URL`**：只影响镜像内 **pip**，不影响 **`FROM`** 拉基础镜像。
- 拉 **`vllm/vllm-openai`** 需访问 Docker Hub；若慢，见下一节 **registry-mirrors**（在 Docker Desktop → Settings → Docker Engine 配置）。

---

## 3. Docker 镜像加速（可选）

在 **Docker Desktop → Settings → Docker Engine** 中合并 `registry-mirrors`（示例，按网络情况删减）：

```json
"registry-mirrors": [
  "https://docker.m.daocloud.io",
  "https://docker.imgdb.de"
]
```

保存并 **Apply & restart**。恢复默认直连 Docker Hub 时删除 `registry-mirrors` 或置空。

---

## 4. 启动 vLLM 服务（GPU）

### 4.1 重要：`vllm/vllm-openai` 镜像的启动方式

官方 **`vllm/vllm-openai`** 镜像 **入口已包含 `vllm serve`**。容器参数应直接写 **模型与选项**，**不要再写一层 `vllm serve`**，否则会出现 `unrecognized arguments: serve ...`。

正确示例（模型名为 **位置参数** `zai-org/GLM-OCR`，服务名 **`glm-ocr`** 与 SDK 配置一致）：

```text
zai-org/GLM-OCR --allowed-local-media-path / --port 8080 --served-model-name glm-ocr ...
```

### 4.2 显存紧张时的参数

`max_model_len` 默认可能很大，**KV 显存**占用高。可限制：

- `--max-model-len`：如 `8192`，仍 OOM 再试 `4096` / `2048`
- `--gpu-memory-utilization`：如 `0.75`
- `--max-num-seqs`：如 `4`

### 4.3 容器内访问 Hugging Face（避免 Connection refused）

若宿主机设置了 **指向 `127.0.0.1` 的代理**，在容器内会连到**容器自己**，常导致 **`[Errno 111] Connection refused`**。启动时建议 **清空代理环境变量**，并可选设置国内 HF 镜像：

```text
-e HTTP_PROXY= -e HTTPS_PROXY= -e http_proxy= -e https_proxy=
-e NO_PROXY=*
-e HF_ENDPOINT=https://hf-mirror.com
```

### 4.4 后台常驻容器（不要 `--rm`）

需要 **关闭终端后仍运行**，使用：

- **`-d`**：后台
- **`--name`**：固定名称便于管理
- **`--restart unless-stopped`**：可选，开机自启
- **不要**加 **`--rm`**（否则停止即删容器）

### 4.5 一键脚本（推荐）

编辑并执行 **`docker-glmocr-gpu/run-vllm-daemon.ps1`**（可改 **`HfCacheHost`**、端口、`MaxModelLen` 等）。

等价的手动命令示例（注意：**无** `vllm serve` 前缀）：

```powershell
docker run -d `
  --name glmocr-vllm `
  --gpus all `
  --shm-size 16g `
  --restart unless-stopped `
  -p 8080:8080 `
  -e HTTP_PROXY= -e HTTPS_PROXY= -e http_proxy= -e https_proxy= `
  -e NO_PROXY=* `
  -e HF_ENDPOINT=https://hf-mirror.com `
  -v D:\docker_cache\hf:/root/.cache/huggingface `
  vllm-glmocr-gpu:patched-v17 `
  zai-org/GLM-OCR `
  --allowed-local-media-path / `
  --port 8080 `
  --max-model-len 8192 `
  --gpu-memory-utilization 0.75 `
  --max-num-seqs 4 `
  --served-model-name glm-ocr
```

首次启动会 **下载模型**，需较长时间；查看日志：

```powershell
docker logs -f glmocr-vllm
```

### 4.6 容器名冲突

若提示 **`container name ... is already in use`**：

```powershell
docker rm -f glmocr-vllm
```

或改用新名字 **`--name glmocr-vllm-2`**。

### 4.7 PowerShell 与 `speculative-config`（可选）

若需 **MTP 投机解码**，JSON 在 PowerShell 中易因引号出错。可暂 **省略** `--speculative-config`；若必须加，建议用 **CMD** 或 **`curl.exe`** 同文档说明，或使用 **`--%`** 停止解析（见 PowerShell 文档）。

---

## 5. 模型下载与缓存

- **GLM-OCR 权重**：首次启动 vLLM 时从 Hugging Face 拉取；挂载 **`-v 宿主机目录:/root/.cache/huggingface`** 可复用缓存、避免重复下载。
- **版面模型**（仅 **`glmocr parse` 开 layout 时需要）：见 [§9](#9-版面模型-pp-doclayout分块必备)。

---

## 6. 验证服务是否就绪

模型加载完成前，`curl` 可能出现 **`Empty reply from server`**，属正常现象，请 **看日志** 是否已监听。

```powershell
curl.exe http://127.0.0.1:8080/v1/models
```

应返回 JSON，且包含 **`glm-ocr`**（与 **`--served-model-name`** 一致）。

---

## 7. Python 直连 API 测试（整页 OCR）

仓库 **`examples/test_vllm_local.py`**：对 **`examples/source/code.png`** 发 **`/v1/chat/completions`**，将识别结果保存到 **`examples/output/<主文件名>_ocr.md`**。

```powershell
cd "D:\你的路径\GLM-OCR-0.1.4\examples"
python test_vllm_local.py
```

参数说明：`--base-url`、`--model glm-ocr`、`--image` 等见脚本内 `--help`。

**说明**：此方式为 **整页一次识别**，**不包含** SDK 的版面分块 JSON。

---

## 8. SDK 流水线：版面分块 + 输出

### 8.1 安装（含 PyTorch、版面依赖）

在 **`GLM-OCR-0.1.4`** 根目录：

```powershell
pip install -e ".[selfhosted]"
```

### 8.2 配置

确保 **`glmocr/config.yaml`** 中：

- **`pipeline.maas.enabled: false`**
- **`pipeline.ocr_api.api_host` / `api_port`** 指向本机 vLLM（如 **`127.0.0.1:8080`**）
- **`pipeline.ocr_api.model: glm-ocr`**
- **`pipeline.enable_layout: true`**（需要分块时）

### 8.3 运行解析

```powershell
cd "D:\你的路径\GLM-OCR-0.1.4"
$env:HF_ENDPOINT = "https://hf-mirror.com"
glmocr parse examples/source/code.png --output examples/output --mode selfhosted --config glmocr/config.yaml --layout-device cpu
```

- **`--layout-device cpu`**：版面模型跑在 CPU，**单卡 GPU 已被 Docker 中 vLLM 占用**时常用；若显存充足或多卡，可改为 **`cuda`** 或 **`cuda:1`**。

### 8.4 输出（每个输入一个子目录）

典型包含：

- **`*.md`**：Markdown 全文
- **`*.json`**：分块结构（`bbox_2d`、`polygon`、`content` 等）
- **`layout_vis/`**：版面可视化图（未加 `--no-layout-vis` 时）

也可使用 **`examples/run_layout_parse.ps1`** 预置环境变量。

---

## 9. 版面模型 PP-DocLayout（分块必备）

首次启用 layout 需下载 **`PaddlePaddle/PP-DocLayoutV3_safetensors`**（约 **133MB** 权重 + 配置）。

### 9.1 依赖

```powershell
pip install -U huggingface_hub hf_xet safetensors "transformers>=5.3.0"
```

大文件常依赖 **`hf_xet`**；若 **`Fetching 5 files` 中途失败**，先装 **`hf_xet`** 再重试。

### 9.2 代码行为（本仓库已增强）

- 使用 **`snapshot_download`** 到 **`%USERPROFILE%\.cache\glmocr\...`**，**`local_dir_use_symlinks=False`**，减轻 Windows 下 HF 缓存 symlink 导致的不完整下载。
- 加载权重时使用 **`use_safetensors=True`**（Hub 上 **无** `pytorch_model.bin`）。

### 9.3 环境变量

| 变量 | 含义 |
|------|------|
| **`HF_ENDPOINT`** | 如 `https://hf-mirror.com`，国内访问 HF |
| **`GLMOCR_LAYOUT_MODEL_DIR`** | 版面模型**本地目录**（已手动下载完整快照时） |
| **`GLMOCR_LAYOUT_SNAPSHOT_DIR`** | 自定义自动下载目录（可选） |
| **`GLMOCR_LAYOUT_DEVICE`** | `cpu` / `cuda` / `cuda:1` |

### 9.4 完全手动下载（最稳）

```powershell
$env:HF_ENDPOINT = "https://hf-mirror.com"
huggingface-cli download PaddlePaddle/PP-DocLayoutV3_safetensors --local-dir "D:\models\PP-DocLayoutV3_safetensors"
```

确认目录内有 **`model.safetensors`**（体积约百 MB）后：

```powershell
$env:GLMOCR_LAYOUT_MODEL_DIR = "D:\models\PP-DocLayoutV3_safetensors"
```

或在 **`glmocr/config.yaml`** 的 **`pipeline.layout.model_dir`** 中填写该路径。

### 9.5 务必使用源码安装 SDK

若修改了本仓库中的 **`glmocr/layout/layout_detector.py`**，需：

```powershell
pip install -e ".[selfhosted]"
```

否则可能仍使用旧版已安装包，导致行为不一致。

---

## 10. 故障排查速查

| 现象 | 可能原因 | 处理 |
|------|----------|------|
| `unrecognized arguments: serve` | 在 **`vllm-openai`** 镜像后又写了 **`vllm serve`** | 去掉 **`vllm serve`**，只保留模型与参数（见 §4.1） |
| `Connection refused` 访问 HF | 容器内代理指向 **127.0.0.1** | 清空 **`HTTP(S)_PROXY`**，设 **`HF_ENDPOINT`** |
| `curl` 52 Empty reply | 模型仍在加载 | **`docker logs -f`** 等到就绪后再请求 |
| `pytorch_model.bin` / 无法加载权重 | 仅缓存了小文件、**safetensors 未下全** | 装 **`hf_xet`**，删坏缓存后重下；或 §9.4 手动下载 |
| `Fetching 5 files` 卡住或失败 | 大文件 + 网络 / 无 **xet** | **`pip install hf_xet`**，换 **`HF_ENDPOINT`** |
| 容器名冲突 | 同名容器已存在 | **`docker rm -f glmocr-vllm`** 或换名 |
| 显存 OOM | KV 过大或双模型抢 GPU | 降低 **`--max-model-len`**；版面用 **`--layout-device cpu`** |

---

## 附录：输入 / 输出能力摘要

**输入（SDK）**：本地图片 / PDF、目录、HTTP(S) URL、`file://`、**data URI**（base64）。  
**输出（SDK + layout）**：**Markdown** + **分块 JSON**（`bbox_2d`、`polygon`、`content` 等）+ 可选 **layout 可视化图**。  
**仅调用 vLLM HTTP API**：返回 **单段 Markdown 文本**（无 SDK 分块 JSON）。

更详细说明见主 **`README_zh.md`**。

---

## 11. 网页前端 + FastAPI（可选）

仓库 **`apps/frontend`**（React）+ **`apps/backend`**（FastAPI）组成完整 Web UI，**不直接**连 vLLM，而是通过 **`python -m glmocr.server`**（`/glmocr/parse`，端口默认 **5002**）走完整流水线。

**依赖链**：`Docker vLLM :8080` → **`glmocr.server :5002`** →  **`FastAPI :8000`** → **`Vite 前端 :3006`**（`/api` 代理到 8000）。

1. 按上文启动 **vLLM** 容器，并保证 **`glmocr/config.yaml`** 里 **`ocr_api`** 指向 **`127.0.0.1:8080`**、`maas.enabled: false`。
2. 安装：`pip install -e ".[selfhosted,server]"`（在 **`GLM-OCR-0.1.4`** 根目录）。
3. 后端环境变量：复制 **`apps/backend/.env.example`** 为 **`.env`**，可按需修改 **`LAYOUT_OCR_URL`**（默认 **`http://127.0.0.1:5002/glmocr/parse`**）。
4. **必须在 `apps/backend` 目录**启动 Uvicorn（该目录的 `pyproject.toml` 才包含 **`app`** 包；在仓库根目录执行会报 **`No module named 'app'`**）：
   ```powershell
   cd "...\GLM-OCR-0.1.4\apps\backend"
   uv sync
   uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
   或执行 **`.\run-backend.ps1`**（同目录）。
5. 在 **`apps`** 目录执行 **`.\start-web-stack.ps1`** 查看说明；加 **`-Launch`** 可尝试自动新开窗口启动中间层、后端、前端（需已安装 **uv** 或 **Python**、**pnpm**）。

前端开发地址：**`http://127.0.0.1:3006`**；API 文档：**`http://127.0.0.1:8000/docs`**。

---

*文档对应仓库路径：`docs/自托管Docker与测试完整指南_zh.md`*
