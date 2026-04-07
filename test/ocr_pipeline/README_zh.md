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
python .\run_ocr_pipeline.py --input .\example\ocr_demo.png --mode maas --api-key <YOUR_KEY>
```

## 主要模块

- adapters.py：OCR适配器接口及GLM-OCR适配器
- pipeline.py：端到端流程编排
- postprocess.py：排序与合并逻辑
- quality.py：无真实标签评分及问题检测
- retry_strategies.py：增强/本地/PDF重试策略
- visualization.py：边界框错误可视化输出
- custom_adapter_template.py：自定义OCR后端集成模板