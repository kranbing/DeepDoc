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
# OCR 统一入口（--mode 选择 maas / selfhosted / mock）
python .\run_ocr_pipeline.py --input .\example\ocr_demo.png --mode maas

# selfhosted 模式
python .\run_ocr_pipeline.py --input .\example\ocr_demo.png --mode selfhosted

# 若本地 OCR 服务暂不可用，可开启 mock 回退保证流程可跑通
python .\run_ocr_pipeline.py --input .\example\ocr_demo.png --mode selfhosted --enable-mock-fallback

# Excel 解析入口（输出 QA 友好的结构化 chunks）
python .\run_excel_pipeline.py --input .\example\demo_table.xlsx
```

说明：

- OCR 统一入口通过 `--mode` 切换实现。
- `--mode maas` 读取 `pipeline.maas`（如 `api_key/api_url/model`）配置。
- `--mode selfhosted` 读取 `pipeline.ocr_api`（如 `api_host/api_port/model`）配置。
- 默认不需要传 `--api-key`。
- 程序会按顺序查找配置文件：当前目录 `config.yaml` -> `test/config.yaml` -> `GLM-OCR-0.1.4/glmocr/config.yaml`。


## 主要模块

- adapters.py：OCR适配器接口及GLM-OCR适配器
- pipeline.py：端到端流程编排
- postprocess.py：排序与合并逻辑
- quality.py：无真实标签评分及问题检测
- retry_strategies.py：增强/本地/PDF重试策略
- visualization.py：边界框错误可视化输出
- custom_adapter_template.py：自定义OCR后端集成模板
- excel_adapter.py：Excel 适配器（读取 workbook/sheet/cell）
- excel_postprocess.py：Excel chunk 生成与质量评估

## Excel Chunk 结构

Excel 解析输出遵循可用于 QA 的 chunk 结构，核心字段示例：

```json
{
	"type": "excel_chunk",
	"sheet": "Sheet1",
	"range": "A2:D21",
	"headers": ["日期", "品类", "数量", "金额"],
	"rows": [
		{"row_index": 2, "values": {"日期": "2026-04-01", "品类": "A", "数量": 12, "金额": 329.5}}
	],
	"text": "工作表: Sheet1\n范围: A2:D21\n...",
	"position": {"sheet": "Sheet1", "row_start": 2, "row_end": 21, "col_start": 1, "col_end": 4},
	"structure": {"row_count": 20, "col_count": 4, "has_header": true}
}
```