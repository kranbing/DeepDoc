# 使用 LLaMA-Factory 微调 GLM-OCR

本教程介绍如何使用 [LLaMA-Factory](https://github.com/hiyouga/LLaMA-Factory) 对 GLM-OCR 模型进行微调，涵盖环境安装、数据准备、训练启动等步骤，本教程将以**全参微调**和 **LoRA 微调**两种方式为例介绍。

## 目录

- [使用 LLaMA-Factory 微调 GLM-OCR](#使用-llama-factory-微调-glm-ocr)
  - [目录](#目录)
  - [0. 前言](#0-前言)
  - [1. 安装 LLaMA-Factory](#1-安装-llama-factory)
  - [2. 下载模型](#2-下载模型)
  - [3. 准备数据集](#3-准备数据集)
    - [3.1 数据格式](#31-数据格式)
    - [3.2 放置数据集](#32-放置数据集)
    - [3.3 注册数据集](#33-注册数据集)
    - [3.4 Prompt 设置](#34-prompt-设置)
  - [4. 训练配置](#4-训练配置)
    - [4.1 全参微调](#41-全参微调)
    - [4.2 LoRA 微调](#42-lora-微调)
  - [5. 启动训练](#5-启动训练)
  - [6. 关键参数说明](#6-关键参数说明)
  - [常见问题](#常见问题)

## 0. 前言

本教程仅展示**最小可用**的训练流程；如遇到配置相关的各类问题或需要对训练流程中的各项配置进行自定义，请优先查阅 LLaMA-Factory 官方文档。

[https://llamafactory.readthedocs.io/zh-cn/latest/index.html](https://llamafactory.readthedocs.io/zh-cn/latest/index.html)

## 1. 安装 LLaMA-Factory

```bash
git clone --depth 1 https://github.com/hiyouga/LLaMA-Factory.git
cd LLaMA-Factory
pip install -e .
pip install -r requirements/metrics.txt
```

验证安装：

```bash
llamafactory-cli version
```

由于当前 LLaMA-Factory 仓库默认依赖的 transformers 库的版本为 5.0.0，该版本暂时不支持 GLM-OCR 模型，因此在安装完成 LLaMA-Factory 后需要手动更新 transformers 库的版本：

```bash
pip install --upgrade transformers
```

## 2. 下载模型

从 HuggingFace 或 ModelScope 下载 GLM-OCR：

```bash
# 方式 A：HuggingFace
hf download zai-org/GLM-OCR --local-dir /path/to/GLM-OCR

# 方式 B：ModelScope
modelscope download --model ZhipuAI/GLM-OCR --local_dir /path/to/GLM-OCR
```

> **Tips:** 此步骤可以跳过，直接在 YAML 训练配置中设置 `model_name_or_path: zai-org/GLM-OCR`，开始训练时将会自动下载模型权重。

## 3. 准备数据集

### 3.1 数据格式

LLaMA-Factory 的多模态 SFT 使用 **ShareGPT** 格式。每条样本的格式示例如下：

```json
[
  {
    "messages": [
      {
        "role": "user",
        "content": "<image>Code Generation:"
      },
      {
        "role": "assistant",
        "content": "```rdkit\nC1=CC=CC=C1\n```"
      }
    ],
    "images": [
      "cosyn_chemical/example.png"
    ]
  }
]
```

**注意事项：**
- 文本中的每个 `<image>` 标记对应 `images` 列表中的一张图片，**数量必须严格一致**。
- 图片路径**相对于** LLaMA-Factory 仓库的 `data/` 目录。
- `role` 只能是 `user` 或 `assistant`。

**示例数据集：**
- 在本教程的同级目录下放置了 `cosyn_chemical` 文件夹与 `cosyn_chemical.json` 文件，分别保存了示例数据集的图像文件与 ShareGPT 格式数据集文件。接下来的教程将以该示例数据集为例进行训练，您可以组织自己的训练数据为与示例数据一致的格式进行替换。

### 3.2 放置数据集

将数据集 JSON 文件和图像文件夹移动到 LLaMA-Factory 仓库的 `data/` 目录下：

```
LLaMA-Factory/
└── data/
    ├── cosyn_chemical.json          # 数据集文件
    └── cosyn_chemical/              # 图像文件夹
        ├── a0596db5-...png
        ├── 1a79d55f-...png
        └── ...
```

### 3.3 注册数据集

编辑 LLaMA-Factory 仓库中的 `data/dataset_info.json`，添加如下格式的数据集条目以在训练过程中加载数据：

```json
"cosyn_chemical": {
  "file_name": "cosyn_chemical.json",
  "formatting": "sharegpt",
  "columns": {
    "messages": "messages",
    "images": "images"
  },
  "tags": {
    "role_tag": "role",
    "content_tag": "content",
    "user_tag": "user",
    "assistant_tag": "assistant"
  }
}
```
### 3.4 Prompt 设置

在 GLM-OCR 训练过程中，我们预定义的三种识别任务及其 Prompt 对应如下：

- 文本识别： `Text Recognition:`
- 表格识别： `Table Recognition:`
- 公式识别： `Formula Recognition:`

若您想要通过继续训练进一步提升以上三种识别任务的能力，建议保持文本 Prompt 与预定义一致，并将图像放置在文本 Prompt 之前，例如 `<image>Text Recognition:` ；若您想要通过训练提升模型在以上三种识别任务之外的新任务上的能力，则您可以通过自定义 Prompt 进行训练。


## 4. 训练配置

本目录下提供了两个示例 YAML 配置文件：

| 配置文件 | 微调方式 | 单卡显存需求 |
|---|---|---|
| [`glm_ocr_full_sft.yaml`](glm_ocr_full_sft.yaml) | 全参微调 | ≥ 24 GB |
| [`glm_ocr_lora_sft.yaml`](glm_ocr_lora_sft.yaml) | LoRA 微调 | ≥ 8 GB |

您可以参考 LLaMA-Factory 官方文档对 YAML 配置文档的参数进行对应的修改。


### 4.1 全参微调

```yaml
### model
model_name_or_path: zai-org/GLM-OCR   # 或本地路径: /path/to/GLM-OCR
trust_remote_code: true

### method
stage: sft
do_train: true
finetuning_type: full
freeze_vision_tower: true              # 冻结 CogViT 视觉编码器
freeze_multi_modal_projector: true     # 冻结 MLP
freeze_language_model: false           # 只训练语言模型

### dataset
dataset: cosyn_chemical                # 数据集名称
template: glm_ocr
cutoff_len: 2048
max_samples: 1000
preprocessing_num_workers: 16

### output
output_dir: saves/glm-ocr/full/sft
logging_steps: 10
save_steps: 500
plot_loss: true
overwrite_output_dir: true

### train
per_device_train_batch_size: 4
gradient_accumulation_steps: 2
learning_rate: 1.0e-5
num_train_epochs: 3
lr_scheduler_type: cosine
warmup_ratio: 0.1
bf16: true
```

### 4.2 LoRA 微调

```yaml
### model
model_name_or_path: zai-org/GLM-OCR   # 或本地路径: /path/to/GLM-OCR
trust_remote_code: true

### method
stage: sft
do_train: true
finetuning_type: lora
lora_rank: 8
lora_target: all

### dataset
dataset: cosyn_chemical
template: glm_ocr
cutoff_len: 2048
max_samples: 1000
preprocessing_num_workers: 16

### output
output_dir: saves/glm-ocr/lora/sft
logging_steps: 10
save_steps: 500
plot_loss: true
overwrite_output_dir: true

### train
per_device_train_batch_size: 4
gradient_accumulation_steps: 4
learning_rate: 1.0e-4
num_train_epochs: 3
lr_scheduler_type: cosine
warmup_ratio: 0.1
bf16: true
```

## 5. 启动训练

**单卡训练：**

```bash
DISABLE_VERSION_CHECK=1 CUDA_VISIBLE_DEVICES=0 \
  llamafactory-cli train path/to/glm_ocr_full_sft.yaml
```

**多卡训练：**

```bash
DISABLE_VERSION_CHECK=1 FORCE_TORCHRUN=1 NNODES=1 NPROC_PER_NODE=8 \
  llamafactory-cli train path/to/glm_ocr_full_sft.yaml
```

LLaMA-Factory 会默认使用所有可用 CUDA 设备，因此您可以通设置 `CUDA_VISIBILE_DEVICES` 环境变量来控制使用哪些CUDA设备。另外您需要将上述命令行中的 `path/to/glm_ocr_full_sft.yaml` 修改为您的训练配置文件路径。训练结束后，checkpoint 会保存到 YAML 中指定的 `output_dir`。

## 6. 关键参数说明

| 参数 | 说明 |
|---|---|
| `model_name_or_path` | HuggingFace 模型 ID 或本地模型目录路径 |
| `template` | GLM-OCR 必须设为 `glm_ocr` |
| `finetuning_type` | `full` 全参微调，`lora` LoRA 微调 |
| `freeze_vision_tower` | 是否冻结视觉编码器（建议 `true`） |
| `freeze_multi_modal_projector` | 是否冻结跨模态连接器（全参微调时建议 `true`） |
| `max_samples` | 从数据集中随机采样 N 条；不设置则使用全部数据 |
| `lora_rank` | LoRA 秩；越大容量越强但显存占用越大（建议值为 8） |
| `lora_target` | LoRA 作用模块；`all` 表示所有线性层 |
| `learning_rate` | 全参微调建议 1e-5，LoRA 建议 1e-4 |

## 常见问题

**Q: 需要多少显存？**

GLM-OCR 是一个轻量的 0.9B 参数模型。LoRA 微调在单张具有 8 GB 显存的显卡上即可运行；全参微调需要约 24 GB。更大的 batch size 或更长的序列长度可以使用 DeepSpeed ZeRO-2/3。

**Q: 可以用自己的 OCR 数据集吗？**

当然可以！按上述 ShareGPT 格式准备数据，在 `dataset_info.json` 中注册，然后修改 YAML 配置中的 `dataset` 字段即可。

**Q: 训练完成后如何合并 LoRA 权重？**

```bash
llamafactory-cli export \
  --model_name_or_path zai-org/GLM-OCR \
  --adapter_name_or_path saves/glm-ocr/lora/sft \
  --template glm_ocr \
  --export_dir saves/glm-ocr/lora/sft/merged \
  --trust_remote_code true
```

**Q: 应该选全参微调还是 LoRA？**

- **LoRA**：训练速度快、显存占用低，适合数据量适中的领域适配场景。
- **全参微调**：当数据量充足且算力充裕时，效果通常更好。

