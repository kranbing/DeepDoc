FROM vllm/vllm-openai:v0.17.1

# 可选：构建时用 --build-arg 临时指定 pip 源（不影响 FROM 拉取，只影响下面 pip）
# 例：docker build --build-arg PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple ...
ARG PIP_INDEX_URL=https://pypi.org/simple

# Keep transformers/hf_hub new enough for GLM-OCR remote model code.
RUN pip install --no-cache-dir -i "${PIP_INDEX_URL}" -U "transformers>=5.3.0,<6" "huggingface_hub>=1.7.2,<2"

