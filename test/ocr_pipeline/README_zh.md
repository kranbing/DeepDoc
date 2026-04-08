# OCR测试与质量评估管道

本文件夹包含一个可运行的OCR测试管道，具备以下功能：

- 支持图像/PDF输入处理
- OCR适配器抽象层
- 后处理（阅读顺序排序、行合并、段落合并）
- 无真实标签（No-GT）质量评分
- 多策略重试机制
- 结构化输出与性能统计
- 可选错误区域可视化

## 快速开始

在 test 目录下执行：

```powershell
# maas 本地测试入口（默认从 config.yaml/.env 读取 MaaS API 配置，不需要 --api-key）
python .\run_ocr_pipeline_maas.py --input .\example\ocr_demo.png

# selfhosted 本地测试入口
python .\run_ocr_pipeline_selfhosted.py --input .\example\ocr_demo.png

# 若本地 OCR 服务暂不可用，可开启 mock 回退保证流程可跑通
python .\run_ocr_pipeline_selfhosted.py --input .\example\ocr_demo.png --enable-mock-fallback
```

说明：

- maas 入口读取 `pipeline.maas`（如 `api_key/api_url/model`）配置。
- selfhosted 入口读取 `pipeline.ocr_api`（如 `api_host/api_port/model`）配置。
- 两个入口均默认不需要传 `--api-key`。
- 程序会按顺序查找配置文件：当前目录 `config.yaml` -> `test/config.yaml` -> `GLM-OCR-0.1.4/glmocr/config.yaml`。

兼容说明：

- `run_ocr_pipeline.py` 仍可继续使用（通用入口，支持 `--mode` 选择）。

## 主要模块

- adapters.py：OCR适配器接口及GLM-OCR适配器
- pipeline.py：端到端流程编排
- postprocess.py：排序与合并逻辑
- quality.py：无真实标签评分及问题检测
- retry_strategies.py：增强/本地/PDF重试策略
- visualization.py：边界框错误可视化输出
- custom_adapter_template.py：自定义OCR后端集成模板