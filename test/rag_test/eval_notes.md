# RAG 初始评估记录模板

## 评估目标
- 使用 `rag_test/testset.json` 中的基础测试集，评估当前 RAG 问答的初始效果。
- 重点关注事实类、定义类、流程类问题的稳定性。
- 对错误回答、不完整回答、幻觉回答、证据引用错误进行记录分析。

## 建议评估流程
1. 逐条读取测试问题。
2. 记录系统回答。
3. 与 `gold_answer` 比对，判断是否正确。
4. 重点分析以下问题：
   - 是否答非所问
   - 是否遗漏关键要点
   - 是否引用了错误 chunk
   - 是否过度依赖概览而忽略文档证据
   - 是否对流程/指标类问题出现数值错误
5. 将典型错误整理为可复现样本，便于后续优化 prompt、召回和 chunk 策略。

## 建议记录字段
- `id`
- `question`
- `gold_answer`
- `model_answer`
- `is_correct`
- `error_type`
- `root_cause`
- `suggested_fix`
- `notes`

## 典型错误分类
- `retrieval_miss` 召回不到关键证据
- `evidence_confusion` 证据片段混淆
- `over_summary` 过度依赖概览导致细节丢失
- `hallucination` 生成了文档中不存在的信息
- `citation_error` 引用了错误或无效 chunk
- `format_error` JSON 或结构化输出不稳定

## 当前建议
- 先做一轮小规模人工评估，记录 20 条左右。
- 再根据错误类型优先优化召回和上下文拼装。
