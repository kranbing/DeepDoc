# Fine-tuning GLM-OCR with LLaMA-Factory

This guide walks you through fine-tuning the GLM-OCR model using [LLaMA-Factory](https://github.com/hiyouga/LLaMA-Factory), covering environment setup, data preparation, and training launch. This document demonstrates two approaches: **Full fine-tuning** and **LoRA fine-tuning**.

## Table of Contents

- [Fine-tuning GLM-OCR with LLaMA-Factory](#fine-tuning-glm-ocr-with-llama-factory)
  - [Table of Contents](#table-of-contents)
  - [0. Introduction](#0-introduction)
  - [1. Install LLaMA-Factory](#1-install-llama-factory)
  - [2. Download the Model](#2-download-the-model)
  - [3. Prepare the Dataset](#3-prepare-the-dataset)
    - [3.1 Dataset Format](#31-dataset-format)
    - [3.2 Place the Dataset](#32-place-the-dataset)
    - [3.3 Register the Dataset](#33-register-the-dataset)
    - [3.4 Prompt Settings](#34-prompt-settings)
  - [4. Training Configuration](#4-training-configuration)
    - [4.1 Full Fine-tuning](#41-full-fine-tuning)
    - [4.2 LoRA Fine-tuning](#42-lora-fine-tuning)
  - [5. Launch Training](#5-launch-training)
  - [6. Key Parameters Explained](#6-key-parameters-explained)
  - [FAQ](#faq)

## 0. Introduction

This tutorial only demonstrates the **minimal viable** training workflow. For configuration-related issues or customization of training parameters, please refer to the official LLaMA-Factory documentation first.

[https://llamafactory.readthedocs.io/en/latest/index.html](https://llamafactory.readthedocs.io/en/latest/index.html)

## 1. Install LLaMA-Factory

```bash
git clone --depth 1 https://github.com/hiyouga/LLaMA-Factory.git
cd LLaMA-Factory
pip install -e .
pip install -r requirements/metrics.txt
```

Verify the installation:

```bash
llamafactory-cli version
```

Since the current LLaMA-Factory repository depends on transformers version 5.0.0 by default, which does not yet support GLM-OCR, you need to manually upgrade the transformers library after installing LLaMA-Factory:

```bash
pip install --upgrade transformers
```

## 2. Download the Model

Download GLM-OCR from HuggingFace or ModelScope:

```bash
# Option A: HuggingFace
hf download zai-org/GLM-OCR --local-dir /path/to/GLM-OCR

# Option B: ModelScope
modelscope download --model ZhipuAI/GLM-OCR --local_dir /path/to/GLM-OCR
```

> **Tips:** This step can be skipped. You can directly set `model_name_or_path: zai-org/GLM-OCR` in the YAML training config, and the model weights will be automatically downloaded when training starts.

## 3. Prepare the Dataset

### 3.1 Dataset Format

LLaMA-Factory uses the **ShareGPT** format for multimodal SFT datasets. Each sample should follow this format:

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

**Notes:**
- Each `<image>` tag in the text corresponds to one entry in the `images` list. The count **must match exactly**.
- Image paths are **relative to** the `data/` directory of the LLaMA-Factory repository.
- `role` can only be `user` or `assistant`.

**Example Dataset:**
- The `cosyn_chemical` folder and `cosyn_chemical.json` file are placed in the same directory as this tutorial, containing example image files and the ShareGPT format dataset file respectively. The following tutorial will use this example dataset for training. You can organize your own training data in the same format as the example data for replacement.

### 3.2 Place the Dataset

Move the dataset JSON file and image folder into the `data/` directory of the LLaMA-Factory repository:

```
LLaMA-Factory/
└── data/
    ├── cosyn_chemical.json          # the dataset file
    └── cosyn_chemical/              # the image folder
        ├── a0596db5-...png
        ├── 1a79d55f-...png
        └── ...
```

### 3.3 Register the Dataset

Edit `data/dataset_info.json` in the LLaMA-Factory repository and add the following dataset entry to load the data during training:

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

### 3.4 Prompt Settings

During GLM-OCR training, we have three predefined recognition tasks and their corresponding prompts:

- Text Recognition: `Text Recognition:`
- Table Recognition: `Table Recognition:`
- Formula Recognition: `Formula Recognition:`

If you want to further improve the model's capability on the above three recognition tasks through continued training, it is recommended to keep the text prompts consistent with the predefined ones and place the image before the text prompt, e.g., `<image>Text Recognition:`. If you want to improve the model's capability on new tasks beyond the above three through training, you can train with custom prompts.

## 4. Training Configuration

Two example YAML config files are provided under this directory:

| Config File | Method | Single GPU VRAM |
|---|---|---|
| [`glm_ocr_full_sft.yaml`](glm_ocr_full_sft.yaml) | Full fine-tuning | ≥ 24 GB |
| [`glm_ocr_lora_sft.yaml`](glm_ocr_lora_sft.yaml) | LoRA fine-tuning | ≥ 8 GB |

You can refer to the official LLaMA-Factory documentation to modify the parameters in the YAML config files accordingly.

### 4.1 Full Fine-tuning

```yaml
### model
model_name_or_path: zai-org/GLM-OCR   # or local path: /path/to/GLM-OCR
trust_remote_code: true

### method
stage: sft
do_train: true
finetuning_type: full
freeze_vision_tower: true              # freeze the CogViT vision encoder
freeze_multi_modal_projector: true     # freeze the MLP
freeze_language_model: false           # only train the language model

### dataset
dataset: cosyn_chemical                # dataset name
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

### 4.2 LoRA Fine-tuning

```yaml
### model
model_name_or_path: zai-org/GLM-OCR   # or local path: /path/to/GLM-OCR
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

## 5. Launch Training

**Single GPU:**

```bash
DISABLE_VERSION_CHECK=1 CUDA_VISIBLE_DEVICES=0 \
  llamafactory-cli train path/to/glm_ocr_full_sft.yaml
```

**Multi-GPU (DeepSpeed ZeRO-2):**

```bash
DISABLE_VERSION_CHECK=1 FORCE_TORCHRUN=1 NNODES=1 NPROC_PER_NODE=8 \
  llamafactory-cli train path/to/glm_ocr_full_sft.yaml
```

**With a custom DeepSpeed config:**

```bash
DISABLE_VERSION_CHECK=1 FORCE_TORCHRUN=1 NNODES=1 NPROC_PER_NODE=8 \
  llamafactory-cli train path/to/glm_ocr_full_sft.yaml \
  --deepspeed examples/deepspeed/ds_z2_config.json
```

LLaMA-Factory uses all available CUDA devices by default, so you can control which GPUs are used by setting the `CUDA_VISIBLE_DEVICES` environment variable. Also, remember to replace `path/to/glm_ocr_full_sft.yaml` in the command above with the path to your training configuration file. After training finishes, the checkpoint will be saved to the `output_dir` specified in the YAML file.


## 6. Key Parameters Explained

| Parameter | Description |
|---|---|
| `model_name_or_path` | HuggingFace model ID or local model directory path |
| `template` | Must be set to `glm_ocr` for GLM-OCR |
| `finetuning_type` | `full` for full fine-tuning, `lora` for LoRA fine-tuning |
| `freeze_vision_tower` | Whether to freeze the vision encoder (recommended `true`) |
| `freeze_multi_modal_projector` | Whether to freeze the cross-modal connector (recommended `true` for full SFT) |
| `max_samples` | Randomly sample N examples from the dataset; omit to use all data |
| `lora_rank` | LoRA rank; higher values mean more capacity but more VRAM usage (recommended: 8) |
| `lora_target` | Modules to apply LoRA to; `all` applies to all linear layers |
| `learning_rate` | Recommended 1e-5 for full fine-tuning, 1e-4 for LoRA |

## FAQ

**Q: How much VRAM do I need?**

GLM-OCR is a compact 0.9B parameter model. LoRA fine-tuning can run on a single GPU with 8 GB VRAM; full fine-tuning requires ~24 GB. For larger batch sizes or longer sequence lengths, use DeepSpeed ZeRO-2/3.

**Q: Can I use my own OCR dataset?**

Yes! Prepare your data in the ShareGPT format shown above, register it in `dataset_info.json`, and update the `dataset` field in the YAML config.

**Q: How do I merge LoRA weights after training?**

```bash
llamafactory-cli export \
  --model_name_or_path zai-org/GLM-OCR \
  --adapter_name_or_path saves/glm-ocr/lora/sft \
  --template glm_ocr \
  --export_dir saves/glm-ocr/lora/sft/merged \
  --trust_remote_code true
```

**Q: Should I use full fine-tuning or LoRA?**

- **LoRA**: Faster training, lower VRAM usage, suitable for domain adaptation with moderate data.
- **Full fine-tuning**: Generally better results when you have abundant data and sufficient compute.
