# RAG 主链路测试报告

- 生成时间：2026-04-20 15:23:24
- 来源项目：6cf73d20-55fb-43c6-987e-efc088417ca9
- 来源文档：DeepDoc-文档理解与多源数据整合的知识服务平台
- 测试集规模：20
- 分块策略：rag_500_100, rag_300_100, semantic_78_600_900_160
- TOPK：1, 3, 5

## 策略与 TOPK 汇总


## 详细结果

### q001 | rag_500_100 | top_k=1
- 类别：fact | 难度：easy
- 问题：项目名称是什么？
- 标准答案：项目名称是 DeepDoc-文档理解与多源数据整合的知识服务平台。
- 模型答案：项目名称是DeepDoc-文档理解与多源数据整合的知识服务平台。
- 引用 chunks：rag_500_100_0000
- 召回块数：1
- exact_match：True
- keyword_hits：3
- keyword_recall：1.0
- token_recall：1.0
- retrieval_hit：True
- evidence_hit：True
- evidence_recall：1.0
- cited_support_rate：0.0
- follow_up_questions：项目的主要技术架构是什么？ | 项目针对哪些应用场景？

### q002 | rag_500_100 | top_k=1
- 类别：fact | 难度：easy
- 问题：项目成员有哪些？
- 标准答案：项目成员包括于智通、韩显、樊亦简。
- 模型答案：项目成员包括：于智通（2023112369）、韩显（2023112312）、樊亦简（2023112311）。文档中未明确说明是否有其他成员。
- 引用 chunks：rag_500_100_0000
- 召回块数：1
- exact_match：False
- keyword_hits：3
- keyword_recall：1.0
- token_recall：0.6667
- retrieval_hit：True
- evidence_hit：True
- evidence_recall：1.0
- cited_support_rate：0.0
- follow_up_questions：项目成员的具体职责是什么？ | 项目是否有其他贡献者或合作者？

### q003 | rag_500_100 | top_k=1
- 类别：fact | 难度：easy
- 问题：指导教师是谁？
- 标准答案：指导教师是郭东明、马冲。
- 模型答案：指导教师是郭东明和马冲。
- 引用 chunks：rag_500_100_0000
- 召回块数：1
- exact_match：False
- keyword_hits：2
- keyword_recall：1.0
- token_recall：0.0
- retrieval_hit：True
- evidence_hit：True
- evidence_recall：1.0
- cited_support_rate：0.0
- follow_up_questions：DeepDoc平台的具体技术实现细节是什么？ | 该项目在企业和教育领域有哪些应用案例？

### q004 | rag_500_100 | top_k=1
- 类别：fact | 难度：easy
- 问题：开题日期是什么时候？
- 标准答案：开题日期是2026年3月20日。
- 模型答案：开题日期是2026年3月20日。
- 引用 chunks：rag_500_100_0000
- 召回块数：1
- exact_match：True
- keyword_hits：3
- keyword_recall：1.0
- token_recall：1.0
- retrieval_hit：True
- evidence_hit：True
- evidence_recall：1.0
- cited_support_rate：0.0
- follow_up_questions：DeepDoc项目的结题日期是什么时候？ | 项目成员的具体分工是什么？

### q005 | rag_500_100 | top_k=1
- 类别：definition | 难度：medium
- 问题：文档中对项目背景问题的核心表述是什么？
- 标准答案：核心问题是数字化进程带来了海量非结构化文档，但在将这些分散数据转化为可用知识资产时，仍面临多层面的关键问题。
- 模型答案：文档中对项目背景问题的核心表述是：在数字经济时代，企业和教育机构积累了海量非结构化文档，形成了“数据丰富但知识贫乏”的困境。现有文档问答工具存在处理深度不足、跨文档整合能力缺失、场景适配单一三大局限。
- 引用 chunks：rag_500_100_0000
- 召回块数：1
- exact_match：False
- keyword_hits：0
- keyword_recall：0.0
- token_recall：0.0
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：DeepDoc平台如何具体解决这三大局限？ | 文档中提到的企业和教育应用场景有哪些具体例子？

### q006 | rag_500_100 | top_k=1
- 类别：definition | 难度：medium
- 问题：项目要解决的四个关键问题是什么？
- 标准答案：四个关键问题分别是内容提取准确性问题、长文档理解问题、多源异构数据融合问题、场景化应用适配问题。
- 模型答案：文档中未找到足够依据，因为提供的文本块仅包含项目摘要，未明确列出四个关键问题。
- 引用 chunks：rag_500_100_0000
- 召回块数：1
- exact_match：False
- keyword_hits：0
- keyword_recall：0.0
- token_recall：0.0
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：项目摘要中提到的现有文档问答工具的三大局限是什么？ | DeepDoc平台如何解决这些局限？

### q007 | rag_500_100 | top_k=1
- 类别：definition | 难度：medium
- 问题：项目的四个创新点分别是什么？
- 标准答案：四个创新点是端到端文档内容提取、布局感知与动态检索、基于知识图谱的多源语义关联与融合、多源异构文档融合与自动表格生成。
- 模型答案：文档中未找到足够依据，因为提供的chunk仅包含项目标题、成员和摘要，未列出具体的创新点。
- 引用 chunks：rag_500_100_0000
- 召回块数：1
- exact_match：False
- keyword_hits：0
- keyword_recall：0.0
- token_recall：0.0
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：项目的四个创新点具体是什么？ | 文档中是否有章节详细描述创新点？

### q008 | rag_500_100 | top_k=1
- 类别：process | 难度：medium
- 问题：第2章研究现状从哪四个维度展开？
- 标准答案：从视觉文档理解、文字识别方法、文档布局分析、RAG检索问答四个维度展开。
- 模型答案：文档中未找到足够依据，因为提供的文档片段仅包含标题、摘要和项目信息，未涉及第2章研究现状的具体内容。
- 引用 chunks：rag_500_100_0000
- 召回块数：1
- exact_match：False
- keyword_hits：0
- keyword_recall：0.0
- token_recall：0.0
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：第2章研究现状的具体内容是什么？ | 文档中是否有关于研究现状维度的详细描述？

### q009 | rag_500_100 | top_k=1
- 类别：process | 难度：medium
- 问题：文档解析模块包含哪些核心子功能？
- 标准答案：文档解析模块包括多格式文档上传、端到端文档解析、复杂元素识别、低质量图像增强、解析结果预览。
- 模型答案：文档中未找到足够依据。提供的文档片段仅包含项目标题、成员信息和摘要概述，未具体说明文档解析模块的核心子功能。
- 引用 chunks：rag_500_100_0000
- 召回块数：1
- exact_match：False
- keyword_hits：0
- keyword_recall：0.0
- token_recall：0.0
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：文档解析模块的具体子功能有哪些？ | DeepDoc平台的整体架构包含哪些模块？

### q010 | rag_500_100 | top_k=1
- 类别：process | 难度：medium
- 问题：检索问答模块的核心功能有哪些？
- 标准答案：检索问答模块包括文档结构分析、布局感知分块、向量索引构建、语义检索、动态重排序、答案生成与溯源、多轮对话。
- 模型答案：文档中未找到足够依据，因为提供的文档片段仅包含标题、摘要和项目信息，未具体描述检索问答模块的核心功能。
- 引用 chunks：rag_500_100_0000
- 召回块数：1
- exact_match：False
- keyword_hits：0
- keyword_recall：0.0
- token_recall：0.0
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：检索问答模块在DeepDoc平台中具体实现了哪些功能？ | 检索问答模块如何与RAG和知识图谱集成？

### q001 | rag_500_100 | top_k=3
- 类别：fact | 难度：easy
- 问题：项目名称是什么？
- 标准答案：项目名称是 DeepDoc-文档理解与多源数据整合的知识服务平台。
- 模型答案：项目名称是DeepDoc-文档理解与多源数据整合的知识服务平台。
- 引用 chunks：rag_500_100_0000
- 召回块数：3
- exact_match：True
- keyword_hits：3
- keyword_recall：1.0
- token_recall：1.0
- retrieval_hit：True
- evidence_hit：True
- evidence_recall：1.0
- cited_support_rate：0.0
- follow_up_questions：项目的主要技术特点是什么？ | 平台面向哪些用户群体？

### q002 | rag_500_100 | top_k=3
- 类别：fact | 难度：easy
- 问题：项目成员有哪些？
- 标准答案：项目成员包括于智通、韩显、樊亦简。
- 模型答案：项目成员包括：于智通（2023112369）、韩显（2023112312）、樊亦简（2023112311）。文档中未明确说明是否有其他成员。
- 引用 chunks：rag_500_100_0000
- 召回块数：3
- exact_match：False
- keyword_hits：3
- keyword_recall：1.0
- token_recall：0.6667
- retrieval_hit：True
- evidence_hit：True
- evidence_recall：1.0
- cited_support_rate：0.0
- follow_up_questions：项目成员的具体职责是什么？ | 指导教师郭东明和马冲在项目中扮演什么角色？

### q003 | rag_500_100 | top_k=3
- 类别：fact | 难度：easy
- 问题：指导教师是谁？
- 标准答案：指导教师是郭东明、马冲。
- 模型答案：指导教师是郭东明和马冲。
- 引用 chunks：rag_500_100_0000
- 召回块数：3
- exact_match：False
- keyword_hits：2
- keyword_recall：1.0
- token_recall：0.0
- retrieval_hit：True
- evidence_hit：True
- evidence_recall：1.0
- cited_support_rate：0.0
- follow_up_questions：指导教师的具体职责或贡献是什么？ | 项目成员的具体分工是什么？

### q004 | rag_500_100 | top_k=3
- 类别：fact | 难度：easy
- 问题：开题日期是什么时候？
- 标准答案：开题日期是2026年3月20日。
- 模型答案：开题日期是2026年3月20日。
- 引用 chunks：rag_500_100_0000
- 召回块数：3
- exact_match：True
- keyword_hits：3
- keyword_recall：1.0
- token_recall：1.0
- retrieval_hit：True
- evidence_hit：True
- evidence_recall：1.0
- cited_support_rate：0.0
- follow_up_questions：项目的主要技术架构是什么？ | 平台面向哪些用户群体？

### q005 | rag_500_100 | top_k=3
- 类别：definition | 难度：medium
- 问题：文档中对项目背景问题的核心表述是什么？
- 标准答案：核心问题是数字化进程带来了海量非结构化文档，但在将这些分散数据转化为可用知识资产时，仍面临多层面的关键问题。
- 模型答案：文档中对项目背景问题的核心表述是：在数字经济时代，企业和教育机构积累了海量非结构化文档，形成了“数据丰富但知识贫乏”的困境。现有文档问答工具存在处理深度不足、跨文档整合能力缺失、场景适配单一三大局限。
- 引用 chunks：rag_500_100_0000, rag_500_100_0001
- 召回块数：3
- exact_match：False
- keyword_hits：0
- keyword_recall：0.0
- token_recall：0.0
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：DeepDoc如何具体解决这三大局限？ | 平台面向企业和教育领域提供了哪些具体服务？

### q006 | rag_500_100 | top_k=3
- 类别：definition | 难度：medium
- 问题：项目要解决的四个关键问题是什么？
- 标准答案：四个关键问题分别是内容提取准确性问题、长文档理解问题、多源异构数据融合问题、场景化应用适配问题。
- 模型答案：项目要解决的四个关键问题是：一是基于深度学习的端到端文档内容提取技术，实现对文字、表格、公式、图表等多类元素的联合识别与结构化输出；二是基于布局感知与动态检索的长文档理解机制，有效解决跨页信息丢失问题；三是基于知识图谱的多源文档语义关联与融合机制，实现跨文档的知识关联与复杂问题推理；四是多源异构文档融合与自动表格生成技术，支持从多格式文档到业务报表的自动化流程。
- 引用 chunks：rag_500_100_0001, rag_500_100_0002
- 召回块数：3
- exact_match：False
- keyword_hits：0
- keyword_recall：0.0
- token_recall：0.0
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：这四个关键问题分别对应哪些具体的技术实现？ | DeepDoc平台如何在实际应用中解决这些关键问题？

### q007 | rag_500_100 | top_k=3
- 类别：definition | 难度：medium
- 问题：项目的四个创新点分别是什么？
- 标准答案：四个创新点是端到端文档内容提取、布局感知与动态检索、基于知识图谱的多源语义关联与融合、多源异构文档融合与自动表格生成。
- 模型答案：项目的四个创新点分别是：一是基于深度学习的端到端文档内容提取技术，采用动态分辨率视觉编码器与轻量化语言模型解耦的架构，实现对文字、表格、公式、图表等多类元素的联合识别与结构化输出；二是基于布局感知与动态检索的长文档理解机制，在RAG框架中引入文档结构信息构建双层索引，有效解决跨页信息丢失问题；三是基于知识图谱的多源文档语义关联与融合机制，将向量检索与图谱检索相结合，实现跨文档的知识关联与复杂问题推理；四是多源异构文档融合与自动表格生成技术，支持从多格式文档到业务报表的自动化流程。
- 引用 chunks：rag_500_100_0001, rag_500_100_0002
- 召回块数：3
- exact_match：False
- keyword_hits：2
- keyword_recall：0.5
- token_recall：0.0
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：这些创新点具体如何应用于企业或教育场景？ | 平台如何确保答案的可溯源性和可信度？

### q008 | rag_500_100 | top_k=3
- 类别：process | 难度：medium
- 问题：第2章研究现状从哪四个维度展开？
- 标准答案：从视觉文档理解、文字识别方法、文档布局分析、RAG检索问答四个维度展开。
- 模型答案：第2章研究现状从四个维度展开：1) 视觉文档理解，2) 文字识别方法，3) 文档布局分析方法，4) RAG检索问答。
- 引用 chunks：rag_500_100_0008
- 召回块数：3
- exact_match：False
- keyword_hits：3
- keyword_recall：0.6
- token_recall：0.4
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：第2章中每个维度的具体子主题是什么？ | 这些维度在DeepDoc平台中如何应用？

### q009 | rag_500_100 | top_k=3
- 类别：process | 难度：medium
- 问题：文档解析模块包含哪些核心子功能？
- 标准答案：文档解析模块包括多格式文档上传、端到端文档解析、复杂元素识别、低质量图像增强、解析结果预览。
- 模型答案：文档解析模块包含的核心子功能包括：一是基于深度学习的端到端文档内容提取技术，实现对文字、表格、公式、图表等多类元素的联合识别与结构化输出。文档中未明确说明其他子功能的具体细节。
- 引用 chunks：rag_500_100_0001, rag_500_100_0002
- 召回块数：3
- exact_match：False
- keyword_hits：0
- keyword_recall：0.0
- token_recall：0.0
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：文档解析模块是否包含其他子功能，如布局分析或格式转换？ | 这些子功能的具体技术实现细节是什么？

### q010 | rag_500_100 | top_k=3
- 类别：process | 难度：medium
- 问题：检索问答模块的核心功能有哪些？
- 标准答案：检索问答模块包括文档结构分析、布局感知分块、向量索引构建、语义检索、动态重排序、答案生成与溯源、多轮对话。
- 模型答案：检索问答模块的核心功能包括：1. 基于布局感知与动态检索的长文档理解机制，在RAG框架中引入文档结构信息构建双层索引，有效解决跨页信息丢失问题；2. 基于知识图谱的多源文档语义关联与融合机制，将向量检索与图谱检索相结合，实现跨文档的知识关联与复杂问题推理。文档中未明确说明其他具体功能。
- 引用 chunks：rag_500_100_0001, rag_500_100_0002
- 召回块数：3
- exact_match：False
- keyword_hits：0
- keyword_recall：0.0
- token_recall：0.0
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：检索问答模块如何具体实现双层索引？ | 该模块支持哪些类型的文档格式？

### q001 | rag_500_100 | top_k=5
- 类别：fact | 难度：easy
- 问题：项目名称是什么？
- 标准答案：项目名称是 DeepDoc-文档理解与多源数据整合的知识服务平台。
- 模型答案：项目名称是DeepDoc-文档理解与多源数据整合的知识服务平台。
- 引用 chunks：rag_500_100_0000
- 召回块数：5
- exact_match：True
- keyword_hits：3
- keyword_recall：1.0
- token_recall：1.0
- retrieval_hit：True
- evidence_hit：True
- evidence_recall：1.0
- cited_support_rate：0.0
- follow_up_questions：项目的主要技术特点是什么？ | 平台面向哪些用户群体？

### q002 | rag_500_100 | top_k=5
- 类别：fact | 难度：easy
- 问题：项目成员有哪些？
- 标准答案：项目成员包括于智通、韩显、樊亦简。
- 模型答案：项目成员包括：于智通（2023112369）、韩显（2023112312）、樊亦简（2023112311）。文档中未明确说明是否有其他成员。
- 引用 chunks：rag_500_100_0000
- 召回块数：5
- exact_match：False
- keyword_hits：3
- keyword_recall：1.0
- token_recall：0.6667
- retrieval_hit：True
- evidence_hit：True
- evidence_recall：1.0
- cited_support_rate：0.0
- follow_up_questions：项目成员的具体职责是什么？ | 指导教师郭东明和马冲在项目中扮演什么角色？

### q003 | rag_500_100 | top_k=5
- 类别：fact | 难度：easy
- 问题：指导教师是谁？
- 标准答案：指导教师是郭东明、马冲。
- 模型答案：指导教师是郭东明和马冲。
- 引用 chunks：rag_500_100_0000
- 召回块数：5
- exact_match：False
- keyword_hits：2
- keyword_recall：1.0
- token_recall：0.0
- retrieval_hit：True
- evidence_hit：True
- evidence_recall：1.0
- cited_support_rate：0.0
- follow_up_questions：该项目的具体实施时间是什么？ | DeepDoc平台的主要技术特点有哪些？

### q004 | rag_500_100 | top_k=5
- 类别：fact | 难度：easy
- 问题：开题日期是什么时候？
- 标准答案：开题日期是2026年3月20日。
- 模型答案：开题日期是2026年3月20日。
- 引用 chunks：rag_500_100_0000
- 召回块数：5
- exact_match：True
- keyword_hits：3
- keyword_recall：1.0
- token_recall：1.0
- retrieval_hit：True
- evidence_hit：True
- evidence_recall：1.0
- cited_support_rate：0.0
- follow_up_questions：DeepDoc平台的主要技术特点是什么？ | DeepDoc面向哪些用户群体提供服务？

### q005 | rag_500_100 | top_k=5
- 类别：definition | 难度：medium
- 问题：文档中对项目背景问题的核心表述是什么？
- 标准答案：核心问题是数字化进程带来了海量非结构化文档，但在将这些分散数据转化为可用知识资产时，仍面临多层面的关键问题。
- 模型答案：文档中对项目背景问题的核心表述是：在数字经济时代，企业和教育机构积累了海量非结构化文档，形成了“数据丰富但知识贫乏”的困境。现有文档问答工具存在处理深度不足、跨文档整合能力缺失、场景适配单一三大局限。
- 引用 chunks：rag_500_100_0000, rag_500_100_0001
- 召回块数：5
- exact_match：False
- keyword_hits：0
- keyword_recall：0.0
- token_recall：0.0
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：DeepDoc平台如何具体解决这三大局限？ | 该平台在企业和教育领域有哪些具体应用案例？

### q006 | rag_500_100 | top_k=5
- 类别：definition | 难度：medium
- 问题：项目要解决的四个关键问题是什么？
- 标准答案：四个关键问题分别是内容提取准确性问题、长文档理解问题、多源异构数据融合问题、场景化应用适配问题。
- 模型答案：项目要解决的四个关键问题是：一是基于深度学习的端到端文档内容提取技术，实现对文字、表格、公式、图表等多类元素的联合识别与结构化输出；二是基于布局感知与动态检索的长文档理解机制，有效解决跨页信息丢失问题；三是基于知识图谱的多源文档语义关联与融合机制，实现跨文档的知识关联与复杂问题推理；四是多源异构文档融合与自动表格生成技术，支持从多格式文档到业务报表的自动化流程。
- 引用 chunks：rag_500_100_0001, rag_500_100_0002
- 召回块数：5
- exact_match：False
- keyword_hits：0
- keyword_recall：0.0
- token_recall：0.0
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：这四个关键问题分别针对现有文档问答工具的哪些具体局限？ | DeepDoc平台如何在实际应用中验证这些问题的解决效果？

### q007 | rag_500_100 | top_k=5
- 类别：definition | 难度：medium
- 问题：项目的四个创新点分别是什么？
- 标准答案：四个创新点是端到端文档内容提取、布局感知与动态检索、基于知识图谱的多源语义关联与融合、多源异构文档融合与自动表格生成。
- 模型答案：项目的四个创新点分别是：一是基于深度学习的端到端文档内容提取技术，采用动态分辨率视觉编码器与轻量化语言模型解耦的架构，实现对文字、表格、公式、图表等多类元素的联合识别与结构化输出；二是基于布局感知与动态检索的长文档理解机制，在RAG框架中引入文档结构信息构建双层索引，有效解决跨页信息丢失问题；三是基于知识图谱的多源文档语义关联与融合机制，将向量检索与图谱检索相结合，实现跨文档的知识关联与复杂问题推理；四是多源异构文档融合与自动表格生成技术，支持从多格式文档到业务报表的自动化流程。
- 引用 chunks：rag_500_100_0001, rag_500_100_0002
- 召回块数：5
- exact_match：False
- keyword_hits：2
- keyword_recall：0.5
- token_recall：0.0
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：这些创新点具体如何应用于企业或教育场景？ | 平台如何通过答案可溯源机制增强可信度？

### q008 | rag_500_100 | top_k=5
- 类别：process | 难度：medium
- 问题：第2章研究现状从哪四个维度展开？
- 标准答案：从视觉文档理解、文字识别方法、文档布局分析、RAG检索问答四个维度展开。
- 模型答案：第2章研究现状从四个维度展开：视觉文档理解、文字识别方法、文档布局分析方法、RAG检索问答。
- 引用 chunks：rag_500_100_0008
- 召回块数：5
- exact_match：False
- keyword_hits：3
- keyword_recall：0.6
- token_recall：0.4
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：第2章中视觉文档理解具体包括哪些子方法？ | 第2章研究现状的结论部分主要讨论了什么？

### q009 | rag_500_100 | top_k=5
- 类别：process | 难度：medium
- 问题：文档解析模块包含哪些核心子功能？
- 标准答案：文档解析模块包括多格式文档上传、端到端文档解析、复杂元素识别、低质量图像增强、解析结果预览。
- 模型答案：文档解析模块包含的核心子功能包括：基于深度学习的端到端文档内容提取技术，实现对文字、表格、公式、图表等多类元素的联合识别与结构化输出。文档中未明确说明其他子功能。
- 引用 chunks：rag_500_100_0001, rag_500_100_0002
- 召回块数：5
- exact_match：False
- keyword_hits：0
- keyword_recall：0.0
- token_recall：0.0
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：文档解析模块是否包含其他子功能，如布局分析或格式转换？ | 文档解析模块的具体技术架构或实现细节是什么？

### q010 | rag_500_100 | top_k=5
- 类别：process | 难度：medium
- 问题：检索问答模块的核心功能有哪些？
- 标准答案：检索问答模块包括文档结构分析、布局感知分块、向量索引构建、语义检索、动态重排序、答案生成与溯源、多轮对话。
- 模型答案：检索问答模块的核心功能包括：1. 基于布局感知与动态检索的长文档理解机制，在RAG框架中引入文档结构信息构建双层索引，有效解决跨页信息丢失问题；2. 基于知识图谱的多源文档语义关联与融合机制，将向量检索与图谱检索相结合，实现跨文档的知识关联与复杂问题推理。文档中未明确说明检索问答模块的其他具体功能。
- 引用 chunks：rag_500_100_0001, rag_500_100_0002
- 召回块数：5
- exact_match：False
- keyword_hits：0
- keyword_recall：0.0
- token_recall：0.0
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：检索问答模块的双层索引具体如何构建？ | 检索问答模块如何实现答案可溯源机制？

### q001 | rag_300_100 | top_k=1
- 类别：fact | 难度：easy
- 问题：项目名称是什么？
- 标准答案：项目名称是 DeepDoc-文档理解与多源数据整合的知识服务平台。
- 模型答案：项目名称是DeepDoc-文档理解与多源数据整合的知识服务平台。
- 引用 chunks：rag_300_100_0000
- 召回块数：1
- exact_match：True
- keyword_hits：3
- keyword_recall：1.0
- token_recall：1.0
- retrieval_hit：True
- evidence_hit：True
- evidence_recall：1.0
- cited_support_rate：0.0
- follow_up_questions：项目的主要技术架构是什么？ | 项目针对哪些应用场景？

### q002 | rag_300_100 | top_k=1
- 类别：fact | 难度：easy
- 问题：项目成员有哪些？
- 标准答案：项目成员包括于智通、韩显、樊亦简。
- 模型答案：项目成员包括：于智通（2023112369）、韩显（2023112312）、樊亦简（2023112311）。文档中未明确说明是否有其他成员。
- 引用 chunks：rag_300_100_0000
- 召回块数：1
- exact_match：False
- keyword_hits：3
- keyword_recall：1.0
- token_recall：0.6667
- retrieval_hit：True
- evidence_hit：True
- evidence_recall：1.0
- cited_support_rate：0.0
- follow_up_questions：项目成员的具体职责是什么？ | 指导教师郭东明和马冲在项目中扮演什么角色？

### q003 | rag_300_100 | top_k=1
- 类别：fact | 难度：easy
- 问题：指导教师是谁？
- 标准答案：指导教师是郭东明、马冲。
- 模型答案：指导教师是郭东明和马冲。
- 引用 chunks：rag_300_100_0000
- 召回块数：1
- exact_match：False
- keyword_hits：2
- keyword_recall：1.0
- token_recall：0.0
- retrieval_hit：True
- evidence_hit：True
- evidence_recall：1.0
- cited_support_rate：0.0
- follow_up_questions：该项目的具体实施时间是什么？ | 项目成员的具体分工是什么？

### q004 | rag_300_100 | top_k=1
- 类别：fact | 难度：easy
- 问题：开题日期是什么时候？
- 标准答案：开题日期是2026年3月20日。
- 模型答案：开题日期是2026年3月20日。
- 引用 chunks：rag_300_100_0000
- 召回块数：1
- exact_match：True
- keyword_hits：3
- keyword_recall：1.0
- token_recall：1.0
- retrieval_hit：True
- evidence_hit：True
- evidence_recall：1.0
- cited_support_rate：0.0
- follow_up_questions：DeepDoc项目的具体研究目标是什么？ | 项目成员和指导教师分别负责哪些部分？

### q005 | rag_300_100 | top_k=1
- 类别：definition | 难度：medium
- 问题：文档中对项目背景问题的核心表述是什么？
- 标准答案：核心问题是数字化进程带来了海量非结构化文档，但在将这些分散数据转化为可用知识资产时，仍面临多层面的关键问题。
- 模型答案：文档中未明确说明项目背景问题的核心表述。
- 引用 chunks：rag_300_100_0000
- 召回块数：1
- exact_match：False
- keyword_hits：0
- keyword_recall：0.0
- token_recall：0.0
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：项目背景部分在文档的哪些页面？ | 文档中是否描述了现有文档QA工具的局限性？

### q006 | rag_300_100 | top_k=1
- 类别：definition | 难度：medium
- 问题：项目要解决的四个关键问题是什么？
- 标准答案：四个关键问题分别是内容提取准确性问题、长文档理解问题、多源异构数据融合问题、场景化应用适配问题。
- 模型答案：文档中未找到足够依据，因为提供的chunk仅包含项目标题、成员和摘要开头，未具体列出要解决的四个关键问题。
- 引用 chunks：rag_300_100_0000
- 召回块数：1
- exact_match：False
- keyword_hits：0
- keyword_recall：0.0
- token_recall：0.0
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：项目要解决的四个关键问题具体是什么？ | 文档中是否有章节详细描述这些问题？

### q007 | rag_300_100 | top_k=1
- 类别：definition | 难度：medium
- 问题：项目的四个创新点分别是什么？
- 标准答案：四个创新点是端到端文档内容提取、布局感知与动态检索、基于知识图谱的多源语义关联与融合、多源异构文档融合与自动表格生成。
- 模型答案：文档中未找到足够依据，因为提供的chunk仅包含项目标题、成员和摘要开头，未提及创新点。
- 引用 chunks：rag_300_100_0000
- 召回块数：1
- exact_match：False
- keyword_hits：0
- keyword_recall：0.0
- token_recall：0.0
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：项目的四个创新点具体是什么？ | 创新点是否在文档的其他部分详细描述？

### q008 | rag_300_100 | top_k=1
- 类别：process | 难度：medium
- 问题：第2章研究现状从哪四个维度展开？
- 标准答案：从视觉文档理解、文字识别方法、文档布局分析、RAG检索问答四个维度展开。
- 模型答案：文档中未找到足够依据，因为提供的文档块（rag_300_100_0000）仅包含标题、摘要和项目信息，未涉及第2章研究现状的具体内容。
- 引用 chunks：无
- 召回块数：1
- exact_match：False
- keyword_hits：1
- keyword_recall：0.2
- token_recall：0.2
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：第2章研究现状的具体内容是什么？ | 文档中是否有其他章节的概述或目录？

### q009 | rag_300_100 | top_k=1
- 类别：process | 难度：medium
- 问题：文档解析模块包含哪些核心子功能？
- 标准答案：文档解析模块包括多格式文档上传、端到端文档解析、复杂元素识别、低质量图像增强、解析结果预览。
- 模型答案：文档中未找到足够依据，因为提供的chunk仅包含标题、项目信息和摘要，未涉及文档解析模块的具体子功能。
- 引用 chunks：rag_300_100_0000
- 召回块数：1
- exact_match：False
- keyword_hits：0
- keyword_recall：0.0
- token_recall：0.0
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：文档解析模块的核心子功能有哪些？ | DeepDoc平台如何实现文档解析？

### q010 | rag_300_100 | top_k=1
- 类别：process | 难度：medium
- 问题：检索问答模块的核心功能有哪些？
- 标准答案：检索问答模块包括文档结构分析、布局感知分块、向量索引构建、语义检索、动态重排序、答案生成与溯源、多轮对话。
- 模型答案：文档中未找到足够依据，因为提供的chunk仅包含项目标题、成员和摘要开头，未涉及检索问答模块的具体功能。
- 引用 chunks：rag_300_100_0000
- 召回块数：1
- exact_match：False
- keyword_hits：0
- keyword_recall：0.0
- token_recall：0.0
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：检索问答模块在DeepDoc平台中是如何实现的？ | 检索问答模块支持哪些类型的文档或数据源？

### q001 | rag_300_100 | top_k=3
- 类别：fact | 难度：easy
- 问题：项目名称是什么？
- 标准答案：项目名称是 DeepDoc-文档理解与多源数据整合的知识服务平台。
- 模型答案：项目名称是DeepDoc-文档理解与多源数据整合的知识服务平台。
- 引用 chunks：rag_300_100_0000
- 召回块数：3
- exact_match：True
- keyword_hits：3
- keyword_recall：1.0
- token_recall：1.0
- retrieval_hit：True
- evidence_hit：True
- evidence_recall：1.0
- cited_support_rate：0.0
- follow_up_questions：项目的主要目标是什么？ | 项目针对哪些应用场景？

### q002 | rag_300_100 | top_k=3
- 类别：fact | 难度：easy
- 问题：项目成员有哪些？
- 标准答案：项目成员包括于智通、韩显、樊亦简。
- 模型答案：项目成员包括：于智通（2023112369）、韩显（2023112312）、樊亦简（2023112311）。文档中未明确说明是否有其他成员。
- 引用 chunks：rag_300_100_0000
- 召回块数：3
- exact_match：False
- keyword_hits：3
- keyword_recall：1.0
- token_recall：0.6667
- retrieval_hit：True
- evidence_hit：True
- evidence_recall：1.0
- cited_support_rate：0.0
- follow_up_questions：项目成员的具体职责是什么？ | 项目是否有其他参与者或贡献者？

### q003 | rag_300_100 | top_k=3
- 类别：fact | 难度：easy
- 问题：指导教师是谁？
- 标准答案：指导教师是郭东明、马冲。
- 模型答案：指导教师是郭东明和马冲。
- 引用 chunks：rag_300_100_0000, rag_300_100_0001
- 召回块数：3
- exact_match：False
- keyword_hits：2
- keyword_recall：1.0
- token_recall：0.0
- retrieval_hit：True
- evidence_hit：True
- evidence_recall：1.0
- cited_support_rate：0.0
- follow_up_questions：指导教师的具体职责或贡献是什么？ | 项目成员的具体角色或分工是什么？

### q004 | rag_300_100 | top_k=3
- 类别：fact | 难度：easy
- 问题：开题日期是什么时候？
- 标准答案：开题日期是2026年3月20日。
- 模型答案：开题日期是2026年3月20日。
- 引用 chunks：rag_300_100_0000, rag_300_100_0001
- 召回块数：3
- exact_match：True
- keyword_hits：3
- keyword_recall：1.0
- token_recall：1.0
- retrieval_hit：True
- evidence_hit：True
- evidence_recall：1.0
- cited_support_rate：0.0
- follow_up_questions：项目的主要创新点有哪些？ | DeepDoc平台支持哪些具体应用场景？

### q005 | rag_300_100 | top_k=3
- 类别：definition | 难度：medium
- 问题：文档中对项目背景问题的核心表述是什么？
- 标准答案：核心问题是数字化进程带来了海量非结构化文档，但在将这些分散数据转化为可用知识资产时，仍面临多层面的关键问题。
- 模型答案：文档中对项目背景问题的核心表述是：在数字经济时代，企业和教育机构积累了海量非结构化文档，形成了“数据丰富但知识贫乏”的困境。现有文档问答工具存在处理深度不足、跨文档整合能力缺失、场景适配单一三大局限。
- 引用 chunks：rag_300_100_0001, rag_300_100_0002
- 召回块数：3
- exact_match：False
- keyword_hits：0
- keyword_recall：0.0
- token_recall：0.0
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：DeepDoc平台如何具体解决这三大局限？ | 文档中提到的企业和教育领域应用场景有哪些具体例子？

### q006 | rag_300_100 | top_k=3
- 类别：definition | 难度：medium
- 问题：项目要解决的四个关键问题是什么？
- 标准答案：四个关键问题分别是内容提取准确性问题、长文档理解问题、多源异构数据融合问题、场景化应用适配问题。
- 模型答案：文档中未明确说明项目要解决的四个关键问题。根据文档摘要，现有文档问答工具存在三大局限：处理深度不足、跨文档整合能力缺失、场景适配单一。
- 引用 chunks：rag_300_100_0001
- 召回块数：3
- exact_match：False
- keyword_hits：0
- keyword_recall：0.0
- token_recall：0.0
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：项目具体针对哪些场景或领域设计？ | DeepDoc平台的核心技术组件有哪些？

### q007 | rag_300_100 | top_k=3
- 类别：definition | 难度：medium
- 问题：项目的四个创新点分别是什么？
- 标准答案：四个创新点是端到端文档内容提取、布局感知与动态检索、基于知识图谱的多源语义关联与融合、多源异构文档融合与自动表格生成。
- 模型答案：文档中未找到足够依据。提供的文档片段仅包含项目标题、成员信息、摘要和问题背景，未明确列出项目的四个创新点。
- 引用 chunks：rag_300_100_0000, rag_300_100_0001, rag_300_100_0002
- 召回块数：3
- exact_match：False
- keyword_hits：0
- keyword_recall：0.0
- token_recall：0.0
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：项目的具体创新点有哪些？ | DeepDoc平台的技术架构是什么？

### q008 | rag_300_100 | top_k=3
- 类别：process | 难度：medium
- 问题：第2章研究现状从哪四个维度展开？
- 标准答案：从视觉文档理解、文字识别方法、文档布局分析、RAG检索问答四个维度展开。
- 模型答案：文档中未明确说明第2章研究现状从哪四个维度展开。
- 引用 chunks：rag_300_100_0007
- 召回块数：3
- exact_match：False
- keyword_hits：0
- keyword_recall：0.0
- token_recall：0.0
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：第2章研究现状的具体内容是什么？ | 文档中是否有章节标题或目录列出研究现状的维度？

### q009 | rag_300_100 | top_k=3
- 类别：process | 难度：medium
- 问题：文档解析模块包含哪些核心子功能？
- 标准答案：文档解析模块包括多格式文档上传、端到端文档解析、复杂元素识别、低质量图像增强、解析结果预览。
- 模型答案：文档中未找到足够依据，因为提供的文档片段仅包含标题、项目信息和摘要，未涉及文档解析模块的具体子功能。
- 引用 chunks：rag_300_100_0000, rag_300_100_0001, rag_300_100_0002
- 召回块数：3
- exact_match：False
- keyword_hits：0
- keyword_recall：0.0
- token_recall：0.0
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：文档解析模块的核心子功能有哪些？ | DeepDoc平台的整体架构或模块划分是什么？

### q010 | rag_300_100 | top_k=3
- 类别：process | 难度：medium
- 问题：检索问答模块的核心功能有哪些？
- 标准答案：检索问答模块包括文档结构分析、布局感知分块、向量索引构建、语义检索、动态重排序、答案生成与溯源、多轮对话。
- 模型答案：文档中未找到足够依据，因为提供的文本块主要涉及项目概述和摘要，未具体描述检索问答模块的核心功能。
- 引用 chunks：rag_300_100_0000, rag_300_100_0001, rag_300_100_0002
- 召回块数：3
- exact_match：False
- keyword_hits：0
- keyword_recall：0.0
- token_recall：0.0
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：检索问答模块的具体功能有哪些？ | DeepDoc平台如何实现跨文档整合？

### q001 | rag_300_100 | top_k=5
- 类别：fact | 难度：easy
- 问题：项目名称是什么？
- 标准答案：项目名称是 DeepDoc-文档理解与多源数据整合的知识服务平台。
- 模型答案：项目名称是DeepDoc-文档理解与多源数据整合的知识服务平台。
- 引用 chunks：rag_300_100_0000
- 召回块数：5
- exact_match：True
- keyword_hits：3
- keyword_recall：1.0
- token_recall：1.0
- retrieval_hit：True
- evidence_hit：True
- evidence_recall：1.0
- cited_support_rate：0.0
- follow_up_questions：项目的主要技术特点是什么？ | 平台面向哪些用户群体？

### q002 | rag_300_100 | top_k=5
- 类别：fact | 难度：easy
- 问题：项目成员有哪些？
- 标准答案：项目成员包括于智通、韩显、樊亦简。
- 模型答案：项目成员包括：于智通（2023112369）、韩显（2023112312）、樊亦简（2023112311）。文档中未明确说明是否有其他成员。
- 引用 chunks：rag_300_100_0000
- 召回块数：5
- exact_match：False
- keyword_hits：3
- keyword_recall：1.0
- token_recall：0.6667
- retrieval_hit：True
- evidence_hit：True
- evidence_recall：1.0
- cited_support_rate：0.0
- follow_up_questions：项目成员的具体职责是什么？ | 指导教师郭东明和马冲的详细背景是什么？

### q003 | rag_300_100 | top_k=5
- 类别：fact | 难度：easy
- 问题：指导教师是谁？
- 标准答案：指导教师是郭东明、马冲。
- 模型答案：指导教师是郭东明和马冲。
- 引用 chunks：rag_300_100_0000, rag_300_100_0001
- 召回块数：5
- exact_match：False
- keyword_hits：2
- keyword_recall：1.0
- token_recall：0.0
- retrieval_hit：True
- evidence_hit：True
- evidence_recall：1.0
- cited_support_rate：0.0
- follow_up_questions：指导教师的具体职责或贡献是什么？ | 项目成员的具体分工是什么？

### q004 | rag_300_100 | top_k=5
- 类别：fact | 难度：easy
- 问题：开题日期是什么时候？
- 标准答案：开题日期是2026年3月20日。
- 模型答案：开题日期是2026年3月20日。
- 引用 chunks：rag_300_100_0000, rag_300_100_0001
- 召回块数：5
- exact_match：True
- keyword_hits：3
- keyword_recall：1.0
- token_recall：1.0
- retrieval_hit：True
- evidence_hit：True
- evidence_recall：1.0
- cited_support_rate：0.0
- follow_up_questions：项目的主要技术架构是什么？ | 平台面向哪些用户群体？

### q005 | rag_300_100 | top_k=5
- 类别：definition | 难度：medium
- 问题：文档中对项目背景问题的核心表述是什么？
- 标准答案：核心问题是数字化进程带来了海量非结构化文档，但在将这些分散数据转化为可用知识资产时，仍面临多层面的关键问题。
- 模型答案：文档中对项目背景问题的核心表述是：在数字经济时代，企业和教育机构积累了海量非结构化文档，形成了“数据丰富但知识贫乏”的困境。现有文档问答工具存在处理深度不足、跨文档整合能力缺失、场景适配单一三大局限。
- 引用 chunks：rag_300_100_0001, rag_300_100_0002
- 召回块数：5
- exact_match：False
- keyword_hits：0
- keyword_recall：0.0
- token_recall：0.0
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：DeepDoc平台如何具体解决这三大局限？ | 平台面向企业和教育领域的具体应用场景有哪些？

### q006 | rag_300_100 | top_k=5
- 类别：definition | 难度：medium
- 问题：项目要解决的四个关键问题是什么？
- 标准答案：四个关键问题分别是内容提取准确性问题、长文档理解问题、多源异构数据融合问题、场景化应用适配问题。
- 模型答案：项目要解决的四个关键问题是：1. 基于深度学习的端到端文档内容提取技术，实现对文字、表格、公式、图表等多类元素的联合识别与结构化输出；2. 基于布局感知与动态检索的长文档理解机制，有效解决跨页信息丢失问题；3. 基于知识图谱的多源文档语义关联与融合机制，实现跨文档的知识关联与复杂问题推理；4. 多源异构文档融合与自动表格生成技术，支持从多格式文档到业务报表的自动化流程。
- 引用 chunks：rag_300_100_0003
- 召回块数：5
- exact_match：False
- keyword_hits：0
- keyword_recall：0.0
- token_recall：0.0
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：这些技术如何具体应用于企业或教育场景？ | 平台如何通过答案可溯源机制增强可信度？

### q007 | rag_300_100 | top_k=5
- 类别：definition | 难度：medium
- 问题：项目的四个创新点分别是什么？
- 标准答案：四个创新点是端到端文档内容提取、布局感知与动态检索、基于知识图谱的多源语义关联与融合、多源异构文档融合与自动表格生成。
- 模型答案：项目的四个创新点分别是：一是基于深度学习的端到端文档内容提取技术，采用动态分辨率视觉编码器与轻量化语言模型解耦的架构，实现对文字、表格、公式、图表等多类元素的联合识别与结构化输出；二是基于布局感知与动态检索的长文档理解机制，在RAG框架中引入文档结构信息构建双层索引，有效解决跨页信息丢失问题；三是基于知识图谱的多源文档语义关联与融合机制，将向量检索与图谱检索相结合，实现跨文档的知识关联与复杂问题推理；四是多源异构文档融合与自动表格生成技术，支持从多格式文档到业务报表的自动化流程。
- 引用 chunks：rag_300_100_0003
- 召回块数：5
- exact_match：False
- keyword_hits：2
- keyword_recall：0.5
- token_recall：0.0
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：这些创新点具体如何应用于企业或教育场景？ | 平台如何通过答案可溯源机制增强可信度？

### q008 | rag_300_100 | top_k=5
- 类别：process | 难度：medium
- 问题：第2章研究现状从哪四个维度展开？
- 标准答案：从视觉文档理解、文字识别方法、文档布局分析、RAG检索问答四个维度展开。
- 模型答案：第2章研究现状从四个维度展开：视觉文档理解、文字识别方法、文档布局分析方法、RAG检索问答。
- 引用 chunks：rag_300_100_0010
- 召回块数：5
- exact_match：False
- keyword_hits：3
- keyword_recall：0.6
- token_recall：0.4
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：第2章中每个维度的具体子主题是什么？ | 第2章结论部分总结了哪些内容？

### q009 | rag_300_100 | top_k=5
- 类别：process | 难度：medium
- 问题：文档解析模块包含哪些核心子功能？
- 标准答案：文档解析模块包括多格式文档上传、端到端文档解析、复杂元素识别、低质量图像增强、解析结果预览。
- 模型答案：文档解析模块包含的核心子功能包括：基于深度学习的端到端文档内容提取技术，采用动态分辨率视觉编码器与轻量化语言模型解耦的架构，实现对文字、表格、公式、图表等多类元素的联合识别与结构化输出。文档中未明确说明是否还有其他子功能。
- 引用 chunks：rag_300_100_0003
- 召回块数：5
- exact_match：False
- keyword_hits：0
- keyword_recall：0.0
- token_recall：0.0
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：文档解析模块的具体技术架构细节是什么？ | 文档解析模块如何与其他模块（如理解、关联、应用）集成？

### q010 | rag_300_100 | top_k=5
- 类别：process | 难度：medium
- 问题：检索问答模块的核心功能有哪些？
- 标准答案：检索问答模块包括文档结构分析、布局感知分块、向量索引构建、语义检索、动态重排序、答案生成与溯源、多轮对话。
- 模型答案：检索问答模块的核心功能包括：基于布局感知与动态检索的长文档理解机制，在RAG框架中引入文档结构信息构建双层索引，有效解决跨页信息丢失问题；以及基于知识图谱的多源文档语义关联与融合机制，将向量检索与图谱检索相结合，实现跨文档的知识关联与复杂问题推理。文档中未明确说明其他具体功能。
- 引用 chunks：rag_300_100_0003
- 召回块数：5
- exact_match：False
- keyword_hits：0
- keyword_recall：0.0
- token_recall：0.0
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：检索问答模块如何具体实现双层索引？ | 该模块在企业和教育场景中有哪些应用示例？

### q001 | semantic_78_600_900_160 | top_k=1
- 类别：fact | 难度：easy
- 问题：项目名称是什么？
- 标准答案：项目名称是 DeepDoc-文档理解与多源数据整合的知识服务平台。
- 模型答案：项目名称是DeepDoc-文档理解与多源数据整合的知识服务平台。
- 引用 chunks：semantic_78_600_900_160_0000
- 召回块数：1
- exact_match：True
- keyword_hits：3
- keyword_recall：1.0
- token_recall：1.0
- retrieval_hit：True
- evidence_hit：True
- evidence_recall：1.0
- cited_support_rate：0.0
- follow_up_questions：项目的主要目标是什么？ | 平台集成了哪些关键技术？

### q002 | semantic_78_600_900_160 | top_k=1
- 类别：fact | 难度：easy
- 问题：项目成员有哪些？
- 标准答案：项目成员包括于智通、韩显、樊亦简。
- 模型答案：文档中未找到足够依据，因为提供的chunk仅包含标题'人工智能创新综合课程设计'，未提及项目成员信息。
- 引用 chunks：semantic_78_600_900_160_0000
- 召回块数：1
- exact_match：False
- keyword_hits：0
- keyword_recall：0.0
- token_recall：0.0
- retrieval_hit：True
- evidence_hit：True
- evidence_recall：1.0
- cited_support_rate：0.0
- follow_up_questions：项目成员的具体姓名和角色是什么？ | 项目团队包括哪些组织或机构？

### q003 | semantic_78_600_900_160 | top_k=1
- 类别：fact | 难度：easy
- 问题：指导教师是谁？
- 标准答案：指导教师是郭东明、马冲。
- 模型答案：文档中未明确说明指导教师是谁。
- 引用 chunks：semantic_78_600_900_160_0000
- 召回块数：1
- exact_match：False
- keyword_hits：0
- keyword_recall：0.0
- token_recall：0.0
- retrieval_hit：True
- evidence_hit：True
- evidence_recall：1.0
- cited_support_rate：0.0
- follow_up_questions：该文档是否包含项目团队或作者信息？ | 文档中是否有提及课程设计的具体负责人员？

### q004 | semantic_78_600_900_160 | top_k=1
- 类别：fact | 难度：easy
- 问题：开题日期是什么时候？
- 标准答案：开题日期是2026年3月20日。
- 模型答案：文档中未找到足够依据，因为提供的文档块仅包含标题'人工智能创新综合课程设计'，未提及开题日期。
- 引用 chunks：semantic_78_600_900_160_0000
- 召回块数：1
- exact_match：False
- keyword_hits：0
- keyword_recall：0.0
- token_recall：0.0
- retrieval_hit：True
- evidence_hit：True
- evidence_recall：1.0
- cited_support_rate：0.0
- follow_up_questions：文档中是否在其他部分提到了开题日期或相关时间信息？ | 能否提供更多关于项目时间线的细节？

### q005 | semantic_78_600_900_160 | top_k=1
- 类别：definition | 难度：medium
- 问题：文档中对项目背景问题的核心表述是什么？
- 标准答案：核心问题是数字化进程带来了海量非结构化文档，但在将这些分散数据转化为可用知识资产时，仍面临多层面的关键问题。
- 模型答案：文档中未找到足够依据，因为提供的chunk仅包含标题'人工智能创新综合课程设计'，未涉及项目背景问题的核心表述。
- 引用 chunks：semantic_78_600_900_160_0000
- 召回块数：1
- exact_match：False
- keyword_hits：0
- keyword_recall：0.0
- token_recall：0.0
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：项目背景中提到的'数据丰富但知识贫乏'困境具体指什么？ | DeepDoc平台如何解决现有文档QA工具的局限性？

### q006 | semantic_78_600_900_160 | top_k=1
- 类别：definition | 难度：medium
- 问题：项目要解决的四个关键问题是什么？
- 标准答案：四个关键问题分别是内容提取准确性问题、长文档理解问题、多源异构数据融合问题、场景化应用适配问题。
- 模型答案：文档中未找到足够依据，因为提供的chunk仅包含标题，未提及项目要解决的四个关键问题。
- 引用 chunks：无
- 召回块数：1
- exact_match：False
- keyword_hits：0
- keyword_recall：0.0
- token_recall：0.0
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：项目具体针对哪些现有文档QA工具的局限性？ | DeepDoc平台在文档解析方面有哪些创新点？

### q007 | semantic_78_600_900_160 | top_k=1
- 类别：definition | 难度：medium
- 问题：项目的四个创新点分别是什么？
- 标准答案：四个创新点是端到端文档内容提取、布局感知与动态检索、基于知识图谱的多源语义关联与融合、多源异构文档融合与自动表格生成。
- 模型答案：文档中未找到足够依据。提供的文档块仅包含标题，未提及项目的四个创新点。
- 引用 chunks：无
- 召回块数：1
- exact_match：False
- keyword_hits：0
- keyword_recall：0.0
- token_recall：0.0
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：文档中哪些部分详细描述了DeepDoc的创新点？ | 项目的创新点是否在文档的其他章节或页面中列出？

### q008 | semantic_78_600_900_160 | top_k=1
- 类别：process | 难度：medium
- 问题：第2章研究现状从哪四个维度展开？
- 标准答案：从视觉文档理解、文字识别方法、文档布局分析、RAG检索问答四个维度展开。
- 模型答案：文档中未找到足够依据，因为提供的chunk仅包含项目成员信息，未涉及第2章研究现状的具体维度。
- 引用 chunks：semantic_78_600_900_160_0003
- 召回块数：1
- exact_match：False
- keyword_hits：0
- keyword_recall：0.0
- token_recall：0.0
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：第2章研究现状的具体内容是什么？ | 文档中是否有其他部分详细描述研究现状的维度？

### q009 | semantic_78_600_900_160 | top_k=1
- 类别：process | 难度：medium
- 问题：文档解析模块包含哪些核心子功能？
- 标准答案：文档解析模块包括多格式文档上传、端到端文档解析、复杂元素识别、低质量图像增强、解析结果预览。
- 模型答案：文档中未找到足够依据，因为提供的chunk仅包含标题，未涉及文档解析模块的具体内容。
- 引用 chunks：无
- 召回块数：1
- exact_match：False
- keyword_hits：0
- keyword_recall：0.0
- token_recall：0.0
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：文档解析模块的核心子功能有哪些？ | DeepDoc平台如何实现文档解析？

### q010 | semantic_78_600_900_160 | top_k=1
- 类别：process | 难度：medium
- 问题：检索问答模块的核心功能有哪些？
- 标准答案：检索问答模块包括文档结构分析、布局感知分块、向量索引构建、语义检索、动态重排序、答案生成与溯源、多轮对话。
- 模型答案：文档中未找到足够依据，因为提供的chunk仅包含标题信息，未涉及检索问答模块的具体功能。
- 引用 chunks：无
- 召回块数：1
- exact_match：False
- keyword_hits：0
- keyword_recall：0.0
- token_recall：0.0
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：检索问答模块是否支持多模态文档理解？ | 检索问答模块如何与知识图谱集成？

### q001 | semantic_78_600_900_160 | top_k=3
- 类别：fact | 难度：easy
- 问题：项目名称是什么？
- 标准答案：项目名称是 DeepDoc-文档理解与多源数据整合的知识服务平台。
- 模型答案：项目名称是DeepDoc-文档理解与多源数据整合的知识服务平台。
- 引用 chunks：semantic_78_600_900_160_0001
- 召回块数：3
- exact_match：True
- keyword_hits：3
- keyword_recall：1.0
- token_recall：1.0
- retrieval_hit：True
- evidence_hit：True
- evidence_recall：1.0
- cited_support_rate：0.0
- follow_up_questions：项目的主要技术架构是什么？ | 项目针对哪些应用场景？

### q002 | semantic_78_600_900_160 | top_k=3
- 类别：fact | 难度：easy
- 问题：项目成员有哪些？
- 标准答案：项目成员包括于智通、韩显、樊亦简。
- 模型答案：项目成员1：于智通--2023112369。文档中未明确说明其他项目成员。
- 引用 chunks：semantic_78_600_900_160_0002
- 召回块数：3
- exact_match：False
- keyword_hits：0
- keyword_recall：0.0
- token_recall：0.0
- retrieval_hit：True
- evidence_hit：True
- evidence_recall：1.0
- cited_support_rate：0.0
- follow_up_questions：项目成员是否包括指导教师或更多学生？ | 项目成员的具体职责是什么？

### q003 | semantic_78_600_900_160 | top_k=3
- 类别：fact | 难度：easy
- 问题：指导教师是谁？
- 标准答案：指导教师是郭东明、马冲。
- 模型答案：文档中未明确说明指导教师是谁。文档显示这是一个名为'DeepDoc-文档理解与多源数据整合的知识服务平台'的项目，属于'人工智能创新综合课程设计'，项目成员包括于智通，但未提及指导教师信息。
- 引用 chunks：semantic_78_600_900_160_0000, semantic_78_600_900_160_0001, semantic_78_600_900_160_0002
- 召回块数：3
- exact_match：False
- keyword_hits：0
- keyword_recall：0.0
- token_recall：0.0
- retrieval_hit：True
- evidence_hit：True
- evidence_recall：1.0
- cited_support_rate：0.0
- follow_up_questions：该项目的指导教师姓名是什么？ | 指导教师是否在文档的其他部分有提及？

### q004 | semantic_78_600_900_160 | top_k=3
- 类别：fact | 难度：easy
- 问题：开题日期是什么时候？
- 标准答案：开题日期是2026年3月20日。
- 模型答案：文档中未明确说明开题日期。提供的文档块仅包含项目名称、院系专业和项目成员信息，未提及开题日期。
- 引用 chunks：semantic_78_600_900_160_0000, semantic_78_600_900_160_0001, semantic_78_600_900_160_0002
- 召回块数：3
- exact_match：False
- keyword_hits：0
- keyword_recall：0.0
- token_recall：0.0
- retrieval_hit：True
- evidence_hit：True
- evidence_recall：1.0
- cited_support_rate：0.0
- follow_up_questions：该项目的开题日期是什么时候？ | 项目的时间安排或进度计划是什么？

### q005 | semantic_78_600_900_160 | top_k=3
- 类别：definition | 难度：medium
- 问题：文档中对项目背景问题的核心表述是什么？
- 标准答案：核心问题是数字化进程带来了海量非结构化文档，但在将这些分散数据转化为可用知识资产时，仍面临多层面的关键问题。
- 模型答案：文档中对项目背景问题的核心表述是：DeepDoc是一个知识服务平台，旨在解决企业和教育机构中非结构化文档导致的'数据丰富但知识贫乏'困境，通过集成多模态大模型、检索增强生成和知识图谱，实现深度文档理解和多源数据整合。
- 引用 chunks：semantic_78_600_900_160_0000, semantic_78_600_900_160_0001
- 召回块数：3
- exact_match：False
- keyword_hits：0
- keyword_recall：0.0
- token_recall：0.0
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：DeepDoc平台的具体技术架构包括哪些组件？ | 该平台在企业和教育领域有哪些应用案例？

### q006 | semantic_78_600_900_160 | top_k=3
- 类别：definition | 难度：medium
- 问题：项目要解决的四个关键问题是什么？
- 标准答案：四个关键问题分别是内容提取准确性问题、长文档理解问题、多源异构数据融合问题、场景化应用适配问题。
- 模型答案：文档中未找到足够依据，因为提供的文本块仅包含项目标题和成员信息，未提及要解决的四个关键问题。
- 引用 chunks：无
- 召回块数：3
- exact_match：False
- keyword_hits：0
- keyword_recall：0.0
- token_recall：0.0
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：DeepDoc项目要解决的具体关键问题是什么？ | 文档中是否有列出项目目标或挑战的部分？

### q007 | semantic_78_600_900_160 | top_k=3
- 类别：definition | 难度：medium
- 问题：项目的四个创新点分别是什么？
- 标准答案：四个创新点是端到端文档内容提取、布局感知与动态检索、基于知识图谱的多源语义关联与融合、多源异构文档融合与自动表格生成。
- 模型答案：文档中未找到足够依据，因为提供的chunks仅包含项目标题、成员信息等，未列出具体的创新点。
- 引用 chunks：无
- 召回块数：3
- exact_match：False
- keyword_hits：0
- keyword_recall：0.0
- token_recall：0.0
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：项目的创新点是否在文档的其他部分详细描述？ | 能否提供关于DeepDoc平台技术架构的更多细节？

### q008 | semantic_78_600_900_160 | top_k=3
- 类别：process | 难度：medium
- 问题：第2章研究现状从哪四个维度展开？
- 标准答案：从视觉文档理解、文字识别方法、文档布局分析、RAG检索问答四个维度展开。
- 模型答案：第2章研究现状从四个维度展开：2.1 视觉文档理解，2.2 文字识别方法，2.3 文档布局分析方法，2.4 RAG检索问答。
- 引用 chunks：semantic_78_600_900_160_0016
- 召回块数：3
- exact_match：False
- keyword_hits：3
- keyword_recall：0.6
- token_recall：0.4
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：第2章中每个维度的具体子节内容是什么？ | 第2章结论部分总结了哪些关键点？

### q009 | semantic_78_600_900_160 | top_k=3
- 类别：process | 难度：medium
- 问题：文档解析模块包含哪些核心子功能？
- 标准答案：文档解析模块包括多格式文档上传、端到端文档解析、复杂元素识别、低质量图像增强、解析结果预览。
- 模型答案：文档中未找到足够依据，因为提供的chunks仅包含标题和项目成员信息，未涉及文档解析模块的具体子功能。
- 引用 chunks：无
- 召回块数：3
- exact_match：False
- keyword_hits：0
- keyword_recall：0.0
- token_recall：0.0
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：文档解析模块的核心子功能有哪些？ | DeepDoc平台如何实现文档理解？

### q010 | semantic_78_600_900_160 | top_k=3
- 类别：process | 难度：medium
- 问题：检索问答模块的核心功能有哪些？
- 标准答案：检索问答模块包括文档结构分析、布局感知分块、向量索引构建、语义检索、动态重排序、答案生成与溯源、多轮对话。
- 模型答案：文档中未找到足够依据，因为提供的chunks仅包含项目标题和成员信息，未涉及检索问答模块的具体功能描述。
- 引用 chunks：无
- 召回块数：3
- exact_match：False
- keyword_hits：0
- keyword_recall：0.0
- token_recall：0.0
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：检索问答模块在DeepDoc平台中如何实现？ | 检索问答模块支持哪些类型的文档或数据源？

### q001 | semantic_78_600_900_160 | top_k=5
- 类别：fact | 难度：easy
- 问题：项目名称是什么？
- 标准答案：项目名称是 DeepDoc-文档理解与多源数据整合的知识服务平台。
- 模型答案：项目名称是DeepDoc-文档理解与多源数据整合的知识服务平台。
- 引用 chunks：semantic_78_600_900_160_0001
- 召回块数：5
- exact_match：True
- keyword_hits：3
- keyword_recall：1.0
- token_recall：1.0
- retrieval_hit：True
- evidence_hit：True
- evidence_recall：1.0
- cited_support_rate：0.0
- follow_up_questions：项目的主要技术特点是什么？ | 项目针对哪些应用场景？

### q002 | semantic_78_600_900_160 | top_k=5
- 类别：fact | 难度：easy
- 问题：项目成员有哪些？
- 标准答案：项目成员包括于智通、韩显、樊亦简。
- 模型答案：项目成员包括：于智通（2023112369）、韩显（2023112312）、樊亦简（2023112311）。文档中未明确说明是否有其他成员。
- 引用 chunks：semantic_78_600_900_160_0002, semantic_78_600_900_160_0003, semantic_78_600_900_160_0004
- 召回块数：5
- exact_match：False
- keyword_hits：3
- keyword_recall：1.0
- token_recall：0.6667
- retrieval_hit：True
- evidence_hit：True
- evidence_recall：1.0
- cited_support_rate：0.0
- follow_up_questions：项目成员的具体职责是什么？ | 项目是否有指导教师或顾问？

### q003 | semantic_78_600_900_160 | top_k=5
- 类别：fact | 难度：easy
- 问题：指导教师是谁？
- 标准答案：指导教师是郭东明、马冲。
- 模型答案：文档中未明确说明指导教师是谁。文档提供了项目名称、院系专业和项目成员信息，但未提及指导教师。
- 引用 chunks：semantic_78_600_900_160_0000, semantic_78_600_900_160_0001, semantic_78_600_900_160_0002, semantic_78_600_900_160_0003, semantic_78_600_900_160_0004
- 召回块数：5
- exact_match：False
- keyword_hits：0
- keyword_recall：0.0
- token_recall：0.0
- retrieval_hit：True
- evidence_hit：True
- evidence_recall：1.0
- cited_support_rate：0.0
- follow_up_questions：该项目的指导教师姓名是什么？ | 指导教师是否在文档的其他部分（如致谢或附录）中提到？

### q004 | semantic_78_600_900_160 | top_k=5
- 类别：fact | 难度：easy
- 问题：开题日期是什么时候？
- 标准答案：开题日期是2026年3月20日。
- 模型答案：文档中未找到足够依据，因为提供的文档片段未提及开题日期。
- 引用 chunks：无
- 召回块数：5
- exact_match：False
- keyword_hits：0
- keyword_recall：0.0
- token_recall：0.0
- retrieval_hit：True
- evidence_hit：False
- evidence_recall：1.0
- cited_support_rate：0.0
- follow_up_questions：文档中是否包含项目时间表或开题报告部分？ | 开题日期是否在文档的其他页面或章节中？

### q005 | semantic_78_600_900_160 | top_k=5
- 类别：definition | 难度：medium
- 问题：文档中对项目背景问题的核心表述是什么？
- 标准答案：核心问题是数字化进程带来了海量非结构化文档，但在将这些分散数据转化为可用知识资产时，仍面临多层面的关键问题。
- 模型答案：文档中对项目背景问题的核心表述是：DeepDoc是一个知识服务平台，旨在解决企业和教育机构中非结构化文档导致的'数据丰富但知识贫乏'困境，通过集成多模态大模型、检索增强生成和知识图谱来实现深度文档理解和多源数据整合。
- 引用 chunks：semantic_78_600_900_160_0000, semantic_78_600_900_160_0001
- 召回块数：5
- exact_match：False
- keyword_hits：0
- keyword_recall：0.0
- token_recall：0.0
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：DeepDoc平台的具体技术架构包括哪些组件？ | 文档中提到的企业应用案例有哪些？

### q006 | semantic_78_600_900_160 | top_k=5
- 类别：definition | 难度：medium
- 问题：项目要解决的四个关键问题是什么？
- 标准答案：四个关键问题分别是内容提取准确性问题、长文档理解问题、多源异构数据融合问题、场景化应用适配问题。
- 模型答案：文档中未找到足够依据，因为提供的chunks仅包含项目标题、成员信息等，未提及四个关键问题的具体内容。
- 引用 chunks：无
- 召回块数：5
- exact_match：False
- keyword_hits：0
- keyword_recall：0.0
- token_recall：0.0
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：项目要解决的四个关键问题在文档的哪一页或部分有详细描述？ | 能否提供更多关于DeepDoc平台功能或创新点的chunks？

### q007 | semantic_78_600_900_160 | top_k=5
- 类别：definition | 难度：medium
- 问题：项目的四个创新点分别是什么？
- 标准答案：四个创新点是端到端文档内容提取、布局感知与动态检索、基于知识图谱的多源语义关联与融合、多源异构文档融合与自动表格生成。
- 模型答案：文档中未找到足够依据，因为提供的chunks仅包含项目标题、成员信息等，未列出具体的创新点。
- 引用 chunks：无
- 召回块数：5
- exact_match：False
- keyword_hits：0
- keyword_recall：0.0
- token_recall：0.0
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：项目的创新点是否在文档的其他部分详细描述？ | 能否提供关于DeepDoc平台技术架构或应用场景的更多信息？

### q008 | semantic_78_600_900_160 | top_k=5
- 类别：process | 难度：medium
- 问题：第2章研究现状从哪四个维度展开？
- 标准答案：从视觉文档理解、文字识别方法、文档布局分析、RAG检索问答四个维度展开。
- 模型答案：第2章研究现状从四个维度展开：2.1 视觉文档理解、2.2 文字识别方法、2.3 文档布局分析方法、2.4 RAG检索问答。
- 引用 chunks：semantic_78_600_900_160_0016
- 召回块数：5
- exact_match：False
- keyword_hits：3
- keyword_recall：0.6
- token_recall：0.4
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：第2章中每个维度的具体子内容是什么？ | 第2章结论部分总结了哪些要点？

### q009 | semantic_78_600_900_160 | top_k=5
- 类别：process | 难度：medium
- 问题：文档解析模块包含哪些核心子功能？
- 标准答案：文档解析模块包括多格式文档上传、端到端文档解析、复杂元素识别、低质量图像增强、解析结果预览。
- 模型答案：文档中未找到足够依据，因为提供的文档块仅包含项目标题和成员信息，未涉及文档解析模块的具体子功能。
- 引用 chunks：无
- 召回块数：5
- exact_match：False
- keyword_hits：0
- keyword_recall：0.0
- token_recall：0.0
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：文档解析模块的核心子功能有哪些？ | DeepDoc平台的整体架构包括哪些部分？

### q010 | semantic_78_600_900_160 | top_k=5
- 类别：process | 难度：medium
- 问题：检索问答模块的核心功能有哪些？
- 标准答案：检索问答模块包括文档结构分析、布局感知分块、向量索引构建、语义检索、动态重排序、答案生成与溯源、多轮对话。
- 模型答案：文档中未找到足够依据，因为提供的chunks仅包含项目标题和成员信息，未涉及检索问答模块的具体功能描述。
- 引用 chunks：无
- 召回块数：5
- exact_match：False
- keyword_hits：0
- keyword_recall：0.0
- token_recall：0.0
- retrieval_hit：False
- evidence_hit：False
- evidence_recall：0.0
- cited_support_rate：0.0
- follow_up_questions：检索问答模块在DeepDoc平台中是如何实现的？ | 检索问答模块支持哪些类型的文档或数据源？
