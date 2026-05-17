# GLM OCR - 智能文档处理服务

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![uv](https://img.shields.io/badge/uv-Enabled-brightgreen.svg)](https://github.com/astral-sh/uv)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

基于 FastAPI 的异步 OCR 文档处理系统，支持 PDF 文档的智能识别、版面分析和结构化输出。

</div>

## ✨ 功能特性

### 核心功能
- 🚀 **异步任务处理** - 基于 FastAPI 和 asyncio 的高性能异步架构
- 📄 **多格式支持** - 支持 PDF、图片等多种文档格式
- 🔍 **智能版面分析** - 自动识别文本、表格、公式、图片等版面元素
- 📝 **多种输出格式** - 支持 Markdown、JSON 等结构化输出
- 🔄 **任务队列管理** - 内置任务队列和优先级调度
- 📊 **实时进度跟踪** - 实时查看任务处理进度和状态
- 🔁 **自动重试机制** - 任务失败自动重试，提高可靠性
- 📈 **分布式锁支持** - 支持多 Worker 并发处理

### 技术亮点
- ⚡ **高性能** - 使用 uv 包管理器，依赖安装速度提升 10-100 倍
- 🏗️ **模块化设计** - 清晰的分层架构，易于扩展
- 🎨 **统一响应格式** - 标准化的 API 响应结构
- 🐳 **Docker 支持** - 提供 Dockerfile，一键部署
- 📋 **完整的 API 文档** - 自动生成的 Swagger/OpenAPI 文档

## 📋 系统架构

```
glm-ocr/
├── backend/
│   ├── api/              # API 路由层
│   │   └── tasks.py      # 任务相关接口
│   ├── core/             # 核心业务逻辑
│   │   ├── flows/        # 处理流程
│   │   ├── steps/        # 处理步骤
│   │   ├── task_manager.py   # 任务管理器
│   │   └── worker.py     # 工作进程
│   ├── models/           # 数据模型
│   ├── repository/       # 数据访问层
│   ├── schemas/          # Pydantic 模型
│   └── utils/            # 工具函数
├── data/                 # 数据目录
├── docs/                 # 文档
├── scripts/              # 脚本工具
├── Dockerfile            # Docker 配置
└── pyproject.toml        # 项目配置
```

### 处理流程

```
┌─────────────┐
│  上传文件    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ PDF转图片   │  20%
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 版面分析+OCR│  65%
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  结果合并   │  15%
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  返回结果    │
└─────────────┘
```

## 🚀 快速开始

### 环境要求

- Python 3.12+
- SQLite (默认) 或其他支持的数据库

### 安装 uv

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 安装依赖

```bash
# 使用 uv 安装依赖
uv sync

```

### 配置环境变量

创建 `.env` 文件（可选）：

```bash
# 基础配置
APP_NAME=OCR Task System
DEBUG=False
HOST=0.0.0.0
PORT=8000

# 数据库
DATABASE_URL=sqlite+aiosqlite:///./tasks.db

# 输出目录
OUTPUT_DIR=./data

# Worker 配置
WORKER_COUNT=5
TASK_TIMEOUT=3600
```

### 启动服务

```bash
# 方式1：使用 uv
# 请在 apps/backend 目录下执行（勿在 GLM-OCR 仓库根目录执行，否则会找不到模块 app）
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 方式2：直接运行
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

访问 API 文档：http://localhost:8000/docs

## 📖 API 使用指南

### 统一响应格式

所有 API 响应遵循统一格式：

```json
{
  "success": true,
  "data": { ... },
  "message": "操作成功",
  "error_code": null
}
```

### 接口列表

#### 1. 提交任务

```bash
curl -X POST http://localhost:8000/tasks/upload \
  -F "file=@document.pdf" \
  -F "processing_mode=pipeline" \
  -F "priority=2" \
  -F "custom_url=http://your-ocr-service"
```

**响应示例：**
```json
{
  "success": true,
  "data": {
    "task_id": "123e4567-e89b-12d3-a456-426614174000",
    "document_id": "987fcdeb-51a2-43f1-a456-426614174000",
    "status": "pending",
    "processing_mode": "pipeline",
    "priority": 2,
    "created_at": "2024-01-21T12:00:00+00:00"
  },
  "message": "Task submitted successfully"
}
```

#### 2. 查询任务状态

```bash
curl http://localhost:8000/tasks/{task_id}
```

**响应示例：**
```json
{
  "success": true,
  "data": {
    "task_id": "123e4567-e89b-12d3-a456-426614174000",
    "status": "completed",
    "progress": 100.0,
    "current_step": "result_merge",
    "created_at": "2024-01-21T12:00:00+00:00",
    "completed_at": "2024-01-21T12:05:30+00:00",
    "result": {
      "metadata": { ... },
      "full_markdown": "# Document\n\nContent...",
      "layout": [ ... ]
    }
  },
  "message": "Task status retrieved successfully"
}
```

#### 3. 列出任务

```bash
curl "http://localhost:8000/tasks/?status=completed&limit=10"
```

#### 4. 取消任务

```bash
curl -X DELETE http://localhost:8000/tasks/{task_id}
```

## 🐳 Docker 部署

### 构建镜像

```bash
docker build -t glm-ocr:latest .
```

### 运行容器

```bash
docker run -d \
  --name glm-ocr \
  -p 8000:8000 \
  -v $(pwd)/data:/backend/data \
  -e WORKER_COUNT=5 \
  glm-ocr:latest
```


## 🛠️ 开发指南

### 添加新的处理流程

1. 在 `backend/core/flows/` 创建新的流程类
2. 继承 `TaskProcessingFlow`
3. 实现 `process()` 方法
4. 在 `__init__.py` 中注册流程

```python
from backend.core.flows.base import TaskProcessingFlow, FlowFactory

class MyCustomFlow(TaskProcessingFlow):
    async def process(self) -> Dict[str, Any]:
        # 实现处理逻辑
        pass

# 注册流程
FlowFactory.register_flow("custom", MyCustomFlow)
```


### 添加依赖

```bash
# 添加生产依赖
uv add httpx

# 添加开发依赖
uv add --dev pytest

```

## 📦 配置说明

主要配置项位于 `backend/utils/config.py`：

| 配置项 | 说明 | 默认值 |
|-------|------|--------|
| `APP_NAME` | 应用名称 | OCR Task System |
| `HOST` | 监听地址 | 0.0.0.0 |
| `PORT` | 监听端口 | 8000 |
| `DATABASE_URL` | 数据库连接 | sqlite+aiosqlite:///./tasks.db |
| `OUTPUT_DIR` | 输出目录 | ./data |
| `WORKER_COUNT` | Worker 数量 | 5 |
| `TASK_TIMEOUT` | 任务超时(秒) | 3600 |
| `MAX_CONCURRENT_TASKS` | 最大并发任务 | 5 |

## 🔍 故障排查

### 常见问题

**Q: 任务一直处于 pending 状态？**
A: 检查 Worker 是否正常启动，查看日志确认是否有错误。

**Q: OCR 处理失败？**
A: 检查 OCR 服务配置，确认 `custom_url` 参数正确。

**Q: 文件上传失败？**
A: 检查输出目录权限，确保应用有写入权限。

### 日志查看

```bash
# 查看应用日志
docker logs glm-ocr -f

# 查看特定级别的日志
LOG_LEVEL=DEBUG uv run uvicorn app.main:app
```

## 📚 相关文档

- [UV 包管理器使用指南](docs/UV_GUIDE.md)
- [API 文档](http://localhost:8000/docs)
- [项目架构文档](docs/ARCHITECTURE.md)

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 👥 作者与致谢

- 开发团队：GLM OCR Team
- 感谢所有贡献者的支持！

---

<div align="center">

**[⬆ 返回顶部](#glm-ocr---智能文档处理服务)**

Made with ❤️ by GLM OCR Team

</div>
