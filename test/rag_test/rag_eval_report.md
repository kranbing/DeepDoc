# RAG 评估报告

- 源文件：rag_eval_report.partial.json
- 测试集：testset.json
- 生成时间：2026-04-19 14:33:12

## 汇总

| Strategy | TOPK | Total | Answer Chunk Hit | Answer Similarity | Key Fact F1 | Groundedness | Avg Retrieved |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| rag_300_100 | 1 | 20 | 0.7000 | 0.2005 | 0.2500 | 0.0000 | 1.00 |
| rag_300_100 | 3 | 20 | 0.6500 | 0.2541 | 0.2366 | 0.0000 | 3.00 |
| rag_300_100 | 5 | 20 | 0.8500 | 0.2779 | 0.3211 | 0.0000 | 5.00 |
| rag_500_100 | 1 | 20 | 0.7000 | 0.1761 | 0.2764 | 0.0000 | 1.00 |
| rag_500_100 | 3 | 20 | 0.5500 | 0.2227 | 0.2441 | 0.0000 | 2.85 |
| rag_500_100 | 5 | 20 | 0.8500 | 0.2648 | 0.2788 | 0.0000 | 5.00 |
| semantic_78_600_900_160 | 1 | 20 | 0.7000 | 0.2181 | 0.2166 | 0.0000 | 1.00 |
| semantic_78_600_900_160 | 3 | 20 | 0.6000 | 0.2260 | 0.2119 | 0.0000 | 2.85 |
| semantic_78_600_900_160 | 5 | 20 | 0.8500 | 0.2830 | 0.3086 | 0.0000 | 5.00 |

## 样本

### q001 | rag_500_100 | top_k=1
- 问题：项目名称是什么？
- 标准答案：项目名称是 DeepDoc-文档理解与多源数据整合的知识服务平台。
- 模型答案：The project name is DeepDoc-文档理解与多源数据整合的知识服务平台. This information is clearly stated in the document overview, which shows '项目名称： DeepDoc-文档理解与多源数据整合的知识服务平台' as part of the course design project details.
- Answer Chunk Hit：0 | Similarity：0.2525 | Key Fact F1：0.5 | Groundedness：0.0
- cited_chunk_ids：无

### q002 | rag_500_100 | top_k=1
- 问题：项目成员有哪些？
- 标准答案：项目成员包括于智通、韩显、樊亦简。
- 模型答案：根据提供的文档信息，项目成员包括：于智通（学号2023112369）、韩显（学号2023112312）、樊亦简（学号2023112311）。指导教师为郭东明和马冲。
- Answer Chunk Hit：1 | Similarity：0.3333 | Key Fact F1：1.0 | Groundedness：0.0
- cited_chunk_ids：rag_500_100_0113

### q003 | rag_500_100 | top_k=1
- 问题：指导教师是谁？
- 标准答案：指导教师是郭东明、马冲。
- 模型答案：根据提供的文档概述，指导教师是郭东明和马冲。然而，没有在检索到的具体文本块中找到直接证据来确认这一点，因为所选块（rag_500_100_0084）讨论的是技术层（表示与存储层、检索与推理层），不包含指导教师信息。
- Answer Chunk Hit：0 | Similarity：0.1887 | Key Fact F1：1.0 | Groundedness：0.0
- cited_chunk_ids：无

### q004 | rag_500_100 | top_k=1
- 问题：开题日期是什么时候？
- 标准答案：开题日期是2026年3月20日。
- 模型答案：根据提供的文档内容，无法确定开题的具体日期。文档中只提到了“西南交通大学本科开题报告（课程设计）”，但没有包含具体的开题日期信息。
- Answer Chunk Hit：1 | Similarity：0.1111 | Key Fact F1：0.0 | Groundedness：0.0
- cited_chunk_ids：rag_500_100_0124

### q005 | rag_500_100 | top_k=1
- 问题：文档中对项目背景问题的核心表述是什么？
- 标准答案：核心问题是数字化进程带来了海量非结构化文档，但在将这些分散数据转化为可用知识资产时，仍面临多层面的关键问题。
- 模型答案：The provided evidence is insufficient to determine the core expression of the project background problem in the document. The available chunk [rag_500_100_0139] discusses future work directions and conclusions, but does not describe the background problem itself.
- Answer Chunk Hit：0 | Similarity：0.0 | Key Fact F1：0.0 | Groundedness：0.0
- cited_chunk_ids：无

### q006 | rag_500_100 | top_k=1
- 问题：项目要解决的四个关键问题是什么？
- 标准答案：四个关键问题分别是内容提取准确性问题、长文档理解问题、多源异构数据融合问题、场景化应用适配问题。
- 模型答案：根据提供的证据，无法确定项目要解决的四个关键问题。提供的文档块[rag_500_100_0139]只提到了后续工作的几个方面（如优化OCR、提升检索能力、增强内容可信度等），但没有明确列出项目最初要解决的四个关键问题。document_overview部分也只包含项目标题、成员等基本信息，没有涉及具体问题。
- Answer Chunk Hit：0 | Similarity：0.1514 | Key Fact F1：0.2 | Groundedness：0.0
- cited_chunk_ids：无

### q007 | rag_500_100 | top_k=1
- 问题：项目的四个创新点分别是什么？
- 标准答案：四个创新点是端到端文档内容提取、布局感知与动态检索、基于知识图谱的多源语义关联与融合、多源异构文档融合与自动表格生成。
- 模型答案：根据提供的文档片段，项目的四个创新点包括：1) 基于深度学习的端到端的文档内容提取技术。然而，该片段只列出了第一个创新点，未完整展示所有四个创新点。因此，证据不足，无法确定其余三个创新点具体是什么。
- Answer Chunk Hit：1 | Similarity：0.1958 | Key Fact F1：0.2 | Groundedness：0.0
- cited_chunk_ids：rag_500_100_0016

### q008 | rag_500_100 | top_k=1
- 问题：第2章研究现状从哪四个维度展开？
- 标准答案：从视觉文档理解、文字识别方法、文档布局分析、RAG检索问答四个维度展开。
- 模型答案：根据提供的证据，无法回答“第2章研究现状从哪四个维度展开？”这个问题。提供的文档片段（rag_500_100_0015）来自第1章（1.4创新点分析），讨论了项目的创新点从四个层面展开，但未涉及第2章研究现状的具体维度。
- Answer Chunk Hit：0 | Similarity：0.124 | Key Fact F1：0.2 | Groundedness：0.0
- cited_chunk_ids：无

### q009 | rag_500_100 | top_k=1
- 问题：文档解析模块包含哪些核心子功能？
- 标准答案：文档解析模块包括多格式文档上传、端到端文档解析、复杂元素识别、低质量图像增强、解析结果预览。
- 模型答案：根据提供的文档片段，文档解析模块被提及为系统五大核心模块之一，但该片段没有详细说明其包含的具体子功能。因此，无法从当前证据中确定文档解析模块包含哪些核心子功能。
- Answer Chunk Hit：1 | Similarity：0.1207 | Key Fact F1：0.0 | Groundedness：0.0
- cited_chunk_ids：rag_500_100_0039

### q010 | rag_500_100 | top_k=1
- 问题：检索问答模块的核心功能有哪些？
- 标准答案：检索问答模块包括文档结构分析、布局感知分块、向量索引构建、语义检索、动态重排序、答案生成与溯源、多轮对话。
- 模型答案：根据文档，检索问答模块的核心功能包括：1. 采用混合检索策略，结合基于向量相似度的语义检索和基于关键词匹配的BM25检索，以提高检索召回率与准确率。2. 实施动态检索策略，根据查询内容和上下文信息对候选文档分块进行动态选择，并在必要时引入结构信息（如文档图关系）进行增强检索。3. 基于大语言模型（LLM）对检索结果进行整合与推理，生成最终回答，包括上下文构建、提示词设计以及模型调用（本地部署或API调用）。这些功能属于检索与推理层，是系统实现智能问答的关键环节。
- Answer Chunk Hit：1 | Similarity：0.1581 | Key Fact F1：0.1429 | Groundedness：0.0
- cited_chunk_ids：rag_500_100_0085

### q011 | rag_500_100 | top_k=1
- 问题：系统的五大核心模块是什么？
- 标准答案：五大核心模块是文档解析模块、检索问答模块、知识图谱模块、表格生成模块、应用交互模块。
- 模型答案：根据提供的文档内容，系统功能被划分为五大核心模块，但具体模块名称未在检索到的文本中详细列出。检索到的内容仅提到系统功能划分为五大核心模块，并参考图3-1，但未提供模块的具体名称或描述。
- Answer Chunk Hit：1 | Similarity：0.2459 | Key Fact F1：0.1667 | Groundedness：0.0
- cited_chunk_ids：rag_500_100_0039

### q012 | rag_500_100 | top_k=1
- 问题：文档解析响应时间的目标是多少？
- 标准答案：对于10页以内文档，解析响应时间目标是不超过10秒。
- 模型答案：The document does not contain information about the target response time for document parsing. The provided chunk [rag_500_100_0104] only mentions project division and design implementation time, without specifying performance metrics like response time targets.
- Answer Chunk Hit：0 | Similarity：0.0323 | Key Fact F1：0.3333 | Groundedness：0.0
- cited_chunk_ids：无

### q013 | rag_500_100 | top_k=1
- 问题：问答响应时间目标是多少？
- 标准答案：问答响应时间目标是不超过3秒。
- 模型答案：根据文档中的性能需求表格，问答响应时间目标是≤3秒，即从用户提问到生成答案的时间不超过3秒。
- Answer Chunk Hit：1 | Similarity：0.5 | Key Fact F1：0.5 | Groundedness：0.0
- cited_chunk_ids：rag_500_100_0051

### q014 | rag_500_100 | top_k=1
- 问题：系统的准确性指标中，检索精度和问答准确率目标分别是多少？
- 标准答案：检索精度目标是召回率@5不低于85%，问答准确率目标是F1分数不低于80%。
- 模型答案：根据提供的文档内容，在准确性指标中，检索精度和问答准确率的具体目标值没有明确列出。文档中提到的准确性需求包括文字识别准确率（≥95%）、表格识别准确率（≥85%）、实体抽取准确率（≥80%）和答案可接受度（≥90%），但没有直接指定检索精度和问答准确率的目标数值。
- Answer Chunk Hit：1 | Similarity：0.1831 | Key Fact F1：0.5 | Groundedness：0.0
- cited_chunk_ids：rag_500_100_0052

### q015 | rag_500_100 | top_k=1
- 问题：RAG问答系统的阶段计划在第几周完成？
- 标准答案：RAG问答系统计划在第8周完成。
- 模型答案：根据提供的文档内容，RAG问答系统的阶段计划在第8周完成。具体来说，第8周的工作包括：星期一集成RAG流程（检索+生成）和设计RAG提示词模板，星期五实现多文档查询接口和测试RAG问答。
- Answer Chunk Hit：1 | Similarity：0.303 | Key Fact F1：0.5 | Groundedness：0.0
- cited_chunk_ids：rag_500_100_0107

### q016 | rag_500_100 | top_k=1
- 问题：系统在数据准备与RAG模块阶段分别做什么？
- 标准答案：数据准备阶段负责数据集收集、清洗、预处理和标注；RAG模块阶段负责文档分块、索引构建和检索策略。
- 模型答案：根据提供的文档内容，系统在数据准备与RAG模块阶段的具体工作描述不充分。仅有的证据来自rag_500_100_0030，该部分讨论了传统RAG方法的不足（如固定分块策略破坏语义结构、难以利用版式信息）和LAD-RAG的改进（引入布局感知机制、动态检索策略），但未明确说明系统本身在数据准备和RAG模块的具体操作。因此，无法基于现有证据详细回答系统在这两个阶段的具体任务。
- Answer Chunk Hit：1 | Similarity：0.1776 | Key Fact F1：0.0 | Groundedness：0.0
- cited_chunk_ids：rag_500_100_0030

### q017 | rag_500_100 | top_k=1
- 问题：项目在自建测试集方面计划构建哪三类测试集？
- 标准答案：计划构建教育文档测试集、企业文档测试集和跨文档综合测试集。
- 模型答案：The document mentions that the project plans to build three types of self-constructed test sets for scenario-specific validation and model optimization, but it does not specify what those three types are. The provided chunk only states the intention to build them without listing the categories.
- Answer Chunk Hit：1 | Similarity：0.0 | Key Fact F1：0.0 | Groundedness：0.0
- cited_chunk_ids：rag_500_100_0065

### q018 | rag_500_100 | top_k=1
- 问题：公开数据集部分提到了哪些用于RAG问答评估的数据集？
- 标准答案：文中提到了DocVQA、VisualMRC等数据集。
- 模型答案：根据提供的文档内容，公开数据集部分没有具体列出用于RAG问答评估的数据集名称。唯一相关的chunk提到“通过以上公开数据集，本项目能够覆盖从基础能力训练到复杂任务评测的全流程需求”，但没有提供具体的公开数据集名称或细节。因此，无法回答公开数据集部分具体提到了哪些用于RAG问答评估的数据集。
- Answer Chunk Hit：1 | Similarity：0.05 | Key Fact F1：0.0 | Groundedness：0.0
- cited_chunk_ids：rag_500_100_0065

### q019 | rag_500_100 | top_k=1
- 问题：系统架构中，表示与存储层负责什么？
- 标准答案：表示与存储层负责文档内容向量化表示及结构化索引构建，是高效检索的基础。
- 模型答案：在DeepDoc系统中，表示与存储层主要负责对文档内容进行向量化表示及结构化索引构建，以支持高效检索。具体包括两个核心部分：向量数据库（如FAISS），用于存储通过文本嵌入模型生成的文档分块的高维语义向量，以支持基于语义相似度的向量检索；以及结构索引，通过构建文档结构图（以文档分块为节点，基于标题层级、段落邻接和跨模态关联建立边连接），实现对文档结构信息的显式建模，弥补纯向量检索在结构理解方面的不足。
- Answer Chunk Hit：1 | Similarity：0.2844 | Key Fact F1：0.2844 | Groundedness：0.0
- cited_chunk_ids：rag_500_100_0084

### q020 | rag_500_100 | top_k=1
- 问题：系统问题降级方案中，RAG能力不足时的优先降级策略是什么？
- 标准答案：优先退回到标准RAG方案，先保证基础问答可用，布局感知模块作为增强功能后续完善。
- 模型答案：根据文档内容，系统问题降级方案中，RAG能力不足时的优先降级策略在提供的证据中未明确提及。文档中只讨论了算力不足时的降级方案，包括使用更小的基座模型、模型量化、加入请求队列和清理存储空间等措施，但没有专门针对RAG能力不足的降级策略。
- Answer Chunk Hit：1 | Similarity：0.1096 | Key Fact F1：0.0 | Groundedness：0.0
- cited_chunk_ids：rag_500_100_0134
