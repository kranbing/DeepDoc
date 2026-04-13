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

## 生成 Figma 设计稿

本仓库提供一个简单的 Figma 开发插件，用于一键生成 DeepDOC 的基础设计稿（Landing + Workspace 桌面 Frame，外加 Tokens 参考区）：

1. Figma Desktop：`Plugins` -> `Development` -> `Import plugin from manifest...`
2. 选择：[figma/deepdoc-design-generator/manifest.json](./figma/deepdoc-design-generator/manifest.json)
3. 运行：`Plugins` -> `Development` -> `DeepDOC Design Generator`
