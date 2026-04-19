# DeepDoc

本地文档工作台（前端静态页 + FastAPI 后端，单进程同时提供页面与 API）。

## 启动

在 **仓库根目录**：

```bash
pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8765 --reload
```

浏览器打开：**http://127.0.0.1:8765**

（`--reload` 仅开发时使用；部署可去掉。）

PDF 解析依赖 GLM-OCR：默认连本机 OCR 服务（如 Docker 内 vLLM，常见为 `127.0.0.1:8080`）；用智谱云端时设置 `GLMOCR_MODE=maas` 与 `ZHIPU_API_KEY`。

如需国内源/镜像下载依赖或模型，可按需设置：

```powershell
$env:HF_ENDPOINT="https://hf-mirror.com"
# 可选：pip 国内镜像（临时生效）
pip install -r backend/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 第七周总结

本周完成了 RAG 全链路在系统中的接入，提问时已可以直接调用现有 RAG 能力，形成从检索、上下文组织到模型生成的完整链路。同时，基于全链路的最优参数测试也已实现，并完成了相关结果评估。

当前 RAG 已经封装为独立模块，支持通过统一接口进行调用，因此可以直接使用 Postman 进行接口测试，验证查询与问答可用性。RAG 提示词也已完成书写与优化，包含文章概要、选块及邻近块信息（可选）、历史概述以及 RAG 检索结果，用于提升回答的准确性与稳定性。

此外，系统已经明确添加了 log 记录，RAG 提问链路也已接入日志，能够记录请求、耗时以及模型调用等关键信息，便于后续调试、排查与性能分析。


