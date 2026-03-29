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
