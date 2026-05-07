# Qasper_after RAG 测试报告

- 生成时间: 2026-04-22 16:59:57
- 数据目录: D:\AI\ceate_design\DeepDoc-main\test\Qasper_after
- chunk 策略: rag_500_100, rag_300_100, semantic_78_600_900_160
- TOPK: 1, 3, 5
- 每组参数固定前 20 条 QA

## 汇总

| Strategy | TOPK | Total | Exact Match | Keyword Recall | Token Recall | Retrieval Hit | Evidence Hit | Evidence Recall | Cited Support |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| rag_300_100 | 1 | 20 | 0.0000 | 0.6208 | 0.5630 | 0.1500 | 0.0000 | 0.1250 | 0.0000 |
| rag_300_100 | 3 | 20 | 0.0000 | 0.6208 | 0.5529 | 0.2500 | 0.0000 | 0.2500 | 0.0000 |
| rag_300_100 | 5 | 20 | 0.0000 | 0.6625 | 0.6071 | 0.3500 | 0.0000 | 0.3500 | 0.0000 |
| rag_500_100 | 1 | 20 | 0.0000 | 0.5771 | 0.5082 | 0.1500 | 0.0000 | 0.1250 | 0.0000 |
| rag_500_100 | 3 | 20 | 0.0000 | 0.5708 | 0.5168 | 0.2500 | 0.0000 | 0.2500 | 0.0000 |
| rag_500_100 | 5 | 20 | 0.0000 | 0.6500 | 0.5720 | 0.3500 | 0.0000 | 0.3500 | 0.0000 |
| semantic_78_600_900_160 | 1 | 20 | 0.0000 | 0.4517 | 0.3934 | 0.0500 | 0.0000 | 0.0500 | 0.0000 |
| semantic_78_600_900_160 | 3 | 20 | 0.0000 | 0.4858 | 0.4159 | 0.1500 | 0.0000 | 0.1250 | 0.0000 |
| semantic_78_600_900_160 | 5 | 20 | 0.0000 | 0.3812 | 0.3070 | 0.1500 | 0.0000 | 0.1250 | 0.0000 |

## 详细结果

### 1909.00694 | train | 753990d0b621d390ed58f20c4d9e4f065f0dc672 | rag_500_100 | top_k=1
- 问题: What is the seed lexicon?
- 标准答案: a vocabulary of positive and negative predicates that helps determine the polarity score of an event
- 模型答案: The seed lexicon is a very small set of seed predicates that directly report one's emotions, such as 'to be glad' (positive).
- 引用 chunks: rag_500_100_0002
- 召回块数: 1
- exact_match: False
- keyword_recall: 0.5
- token_recall: 0.4
- retrieval_hit: False
- evidence_hit: False
- evidence_recall: 0.0
- cited_support_rate: 0.0
- llm_error: 无

### 1909.00694 | train | 9d578ddccc27dd849244d632dd0f6bf27348ad81 | rag_500_100 | top_k=1
- 问题: What are the results?
- 标准答案: Using all data to train: AL -- BiGRU achieved 0.843 accuracy, AL -- BERT achieved 0.863 accuracy, AL+CA+CO -- BiGRU achieved 0.866 accuracy, AL+CA+CO -- BERT achieved 0.835, accuracy, ACP -- BiGRU achieved 0.919 accuracy, ACP -- BERT achived 0.933, accuracy, ACP+AL+CA+CO -- BiGRU achieved 0.917 accuracy, ACP+AL+CA+CO -- BERT achieved 0.913 accuracy. 
Using a subset to train: BERT achieved 0.876 accuracy using ACP (6K), BERT achieved 0.886 accuracy using ACP (6K) + AL, BiGRU achieved 0.830 accuracy using ACP (6K), BiGRU achieved 0.879 accuracy using ACP (6K) + AL + CA + CO.
- 模型答案: The models trained on a Japanese web corpus performed well with minimal supervision. Additionally, combining annotated and unannotated data improved performance over a purely supervised baseline when labeled data were small.
- 引用 chunks: rag_500_100_0004
- 召回块数: 1
- exact_match: False
- keyword_recall: 0.5
- token_recall: 0.0667
- retrieval_hit: False
- evidence_hit: False
- evidence_recall: 0.0
- cited_support_rate: 0.0
- llm_error: 无

### 1909.00694 | train | 02e4bf719b1a504e385c35c6186742e720bcb281 | rag_500_100 | top_k=1
- 问题: How are relations used to propagate polarity?
- 标准答案: based on the relation between events, the suggested polarity of one event can determine the possible polarity of the other event
- 模型答案: Discourse relations are used to propagate polarity by inferring the polarity of an event based on the polarity of a related event and the type of discourse relation. For the Cause relation (x1 causes x2), if x2 is positive, x1 is likely positive; if x2 is negative, x1 is likely negative. For the Concession relation (x2 in spite of x1), the reverse of x2's polarity is propagated to x1. This is transformed into objective functions to train neural network models.
- 引用 chunks: rag_500_100_0002
- 召回块数: 1
- exact_match: False
- keyword_recall: 0.625
- token_recall: 0.4667
- retrieval_hit: True
- evidence_hit: False
- evidence_recall: 0.5
- cited_support_rate: 0.0
- llm_error: 无

### 1909.00694 | train | 44c4bd6decc86f1091b5fc0728873d9324cdde4e | rag_500_100 | top_k=1
- 问题: How big is the Japanese data?
- 标准答案: 7000000 pairs of events were extracted from the Japanese Web corpus, 529850 pairs of events were extracted from the ACP corpus
- 模型答案: The document does not specify the size of the Japanese data.
- 引用 chunks: rag_500_100_0004
- 召回块数: 1
- exact_match: False
- keyword_recall: 0.25
- token_recall: 0.2308
- retrieval_hit: False
- evidence_hit: False
- evidence_recall: 0.0
- cited_support_rate: 0.0
- llm_error: 无

### 1909.00694 | train | 86abeff85f3db79cf87a8c993e5e5aa61226dc98 | rag_500_100 | top_k=1
- 问题: What are labels available in dataset for supervision?
- 标准答案: What are labels available in dataset for supervision?
- 模型答案: The dataset uses a very small seed lexicon as supervision, which contains predicates that directly report emotions (e.g., 'to be glad' is positive). No manually labeled data is used; the method relies on the seed lexicon and a large raw corpus.
- 引用 chunks: rag_500_100_0003
- 召回块数: 1
- exact_match: False
- keyword_recall: 0.375
- token_recall: 0.25
- retrieval_hit: False
- evidence_hit: False
- evidence_recall: 0.0
- cited_support_rate: 0.0
- llm_error: 无

### 1909.00694 | train | c029deb7f99756d2669abad0a349d917428e9c12 | rag_500_100 | top_k=1
- 问题: How big are improvements of supervszed learning results trained on smalled labeled data enhanced with proposed approach copared to basic approach?
- 标准答案: 3%
- 模型答案: The combination of annotated and unannotated data yielded a gain over a purely supervised baseline when labeled data were small. However, the document does not specify the exact size of the improvements.
- 引用 chunks: rag_500_100_0004
- 召回块数: 1
- exact_match: False
- keyword_recall: 0.0
- token_recall: 0.0
- retrieval_hit: False
- evidence_hit: False
- evidence_recall: 0.0
- cited_support_rate: 0.0
- llm_error: 无

### 1909.00694 | train | 39f8db10d949c6b477fa4b51e7c184016505884f | rag_500_100 | top_k=1
- 问题: How does their model learn using mostly raw data?
- 标准答案: by exploiting discourse relations to propagate polarity from seed predicates to final sentiment polarity
- 模型答案: Their method depends only on raw texts and has wider applicability. It uses a very small seed lexicon and a large raw corpus, propagating affective polarity using discourse relations.
- 引用 chunks: rag_500_100_0008
- 召回块数: 1
- exact_match: False
- keyword_recall: 0.375
- token_recall: 0.3333
- retrieval_hit: False
- evidence_hit: False
- evidence_recall: 0.0
- cited_support_rate: 0.0
- llm_error: 无

### 1909.00694 | train | d0bc782961567dc1dd7e074b621a6d6be44bb5b4 | rag_500_100 | top_k=1
- 问题: How big is seed lexicon used for training?
- 标准答案: 30 words
- 模型答案: The seed lexicon consists of positive and negative predicates, but the exact size is not specified in the provided chunks.
- 引用 chunks: rag_500_100_0012
- 召回块数: 1
- exact_match: False
- keyword_recall: 0.0
- token_recall: 0.0
- retrieval_hit: False
- evidence_hit: False
- evidence_recall: 0.0
- cited_support_rate: 0.0
- llm_error: 无

### 1909.00694 | train | a592498ba2fac994cd6fad7372836f0adb37e22a | rag_500_100 | top_k=1
- 问题: How large is raw corpus used for training?
- 标准答案: How large is raw corpus used for training?
- 模型答案: The document does not specify the exact size of the raw corpus used for training. It only mentions that the method requires a large raw corpus.
- 引用 chunks: rag_500_100_0002
- 召回块数: 1
- exact_match: False
- keyword_recall: 0.75
- token_recall: 0.75
- retrieval_hit: False
- evidence_hit: False
- evidence_recall: 0.0
- cited_support_rate: 0.0
- llm_error: 无

### 2003.07723 | train | 3a9d391d25cde8af3334ac62d478b36b30079d74 | rag_500_100 | top_k=1
- 问题: Does the paper report macro F1?
- 标准答案: Does the paper report macro F1?
- 模型答案: The paper does not report macro F1. It reports F1 scores for models, e.g., ~.42 for German models, but does not specify macro F1.
- 引用 chunks: rag_500_100_0062
- 召回块数: 1
- exact_match: False
- keyword_recall: 1.0
- token_recall: 1.0
- retrieval_hit: False
- evidence_hit: False
- evidence_recall: 0.0
- cited_support_rate: 0.0
- llm_error: 无

### 2003.07723 | train | 8d8300d88283c73424c8f301ad9fdd733845eb47 | rag_500_100 | top_k=1
- 问题: How is the annotation experiment evaluated?
- 标准答案: How is the annotation experiment evaluated?
- 模型答案: The annotation experiment is evaluated by measuring inter-annotator agreement, achieving an acceptable agreement of κ = .70 with carefully trained experts. Additionally, crowdsourcing is used as a complementary evaluation method.
- 引用 chunks: rag_500_100_0001
- 召回块数: 1
- exact_match: False
- keyword_recall: 0.8333
- token_recall: 0.8333
- retrieval_hit: False
- evidence_hit: False
- evidence_recall: 0.0
- cited_support_rate: 0.0
- llm_error: 无

### 2003.07723 | train | 48b12eb53e2d507343f19b8a667696a39b719807 | rag_500_100 | top_k=1
- 问题: What are the aesthetic emotions formalized?
- 标准答案: What are the aesthetic emotions formalized?
- 模型答案: The aesthetic emotions formalized are a set of emotions that are predictive of aesthetic appreciation in the reader, including mixed emotional responses, but the specific list is not provided in the chunk.
- 引用 chunks: rag_500_100_0001
- 召回块数: 1
- exact_match: False
- keyword_recall: 0.8333
- token_recall: 0.8333
- retrieval_hit: False
- evidence_hit: False
- evidence_recall: 0.0
- cited_support_rate: 0.0
- llm_error: 无

### 1705.09665 | train | 003f884d3893532f8c302431c9f70be6f64d9be8 | rag_500_100 | top_k=1
- 问题: Do they report results only on English data?
- 标准答案: Do they report results only on English data?
- 模型答案: No, the dataset includes communities from Reddit, and the authors manually removed communities where the bulk of the contributions are in a foreign language. This implies that the results are not exclusively on English data, but non-English communities were filtered out.
- 引用 chunks: rag_500_100_0032
- 召回块数: 1
- exact_match: False
- keyword_recall: 0.625
- token_recall: 0.5
- retrieval_hit: True
- evidence_hit: False
- evidence_recall: 1.0
- cited_support_rate: 0.0
- llm_error: 无

### 1705.09665 | train | bb97537a0a7c8f12a3f65eba73cefa6abcd2f2b2 | rag_500_100 | top_k=1
- 问题: How do the various social phenomena examined manifest in different types of communities?
- 标准答案: Dynamic communities have substantially higher rates of monthly user retention than more stable communities. More distinctive communities exhibit moderately higher monthly retention rates than more generic communities. There is also a strong positive relationship between a community's dynamicity and the average number of months that a user will stay in that community - a short-term trend observed for monthly retention translates into longer-term engagement and suggests that long-term user retention might be strongly driven by the extent to which a community continually provides novel content.
- 模型答案: The document does not describe how specific social phenomena manifest in different types of communities. It introduces a typology based on distinctiveness and temporal dynamism to map communities, but does not provide empirical results on the manifestation of social phenomena.
- 引用 chunks: rag_500_100_0002
- 召回块数: 1
- exact_match: False
- keyword_recall: 0.25
- token_recall: 0.1167
- retrieval_hit: False
- evidence_hit: False
- evidence_recall: 0.0
- cited_support_rate: 0.0
- llm_error: 无

### 1705.09665 | train | eea089baedc0ce80731c8fdcb064b82f584f483a | rag_500_100 | top_k=1
- 问题: What patterns do they observe about how user engagement varies with the characteristics of a community?
- 标准答案: What patterns do they observe about how user engagement varies with the characteristics of a community?
- 模型答案: The document does not explicitly describe observed patterns of how user engagement varies with community characteristics. It states that prior case studies have uncovered striking patterns but that it is unknown whether these observations hold beyond individual cases or when analogies can be drawn between different communities. The document introduces a typology to systematically explore this relationship but does not present specific observed patterns.
- 引用 chunks: rag_500_100_0002
- 召回块数: 1
- exact_match: False
- keyword_recall: 0.625
- token_recall: 0.6875
- retrieval_hit: False
- evidence_hit: False
- evidence_recall: 0.0
- cited_support_rate: 0.0
- llm_error: 无

### 1705.09665 | train | edb2d24d6d10af13931b3a47a6543bd469752f0c | rag_500_100 | top_k=1
- 问题: How did the select the 300 Reddit communities for comparison?
- 标准答案: They selected all the subreddits from January 2013 to December 2014 with at least 500 words in the vocabulary and at least 4 months of the subreddit's history. They also removed communities with the bulk of the contributions are in foreign language.
- 模型答案: The document states that they mapped almost 300 Reddit communities onto the landscape defined by the two axes of their typology, but it does not specify how those 300 communities were selected.
- 引用 chunks: rag_500_100_0006
- 召回块数: 1
- exact_match: False
- keyword_recall: 0.375
- token_recall: 0.1562
- retrieval_hit: False
- evidence_hit: False
- evidence_recall: 0.0
- cited_support_rate: 0.0
- llm_error: 无

### 1705.09665 | train | 938cf30c4f1d14fa182e82919e16072fdbcf2a82 | rag_500_100 | top_k=1
- 问题: How do the authors measure how temporally dynamic a community is?
- 标准答案: How do the authors measure how temporally dynamic a community is?
- 模型答案: The authors measure how temporally dynamic a community is by introducing a quantitative, language-based typology that reflects two key aspects of a community's identity: how distinctive and how temporally dynamic it is. They map almost 300 Reddit communities into the landscape induced by this typology. The specific metric for dynamicity is not explicitly defined in the provided chunks, but the document mentions analyzing the relationship between dynamicity and user retention.
- 引用 chunks: rag_500_100_0045
- 召回块数: 1
- exact_match: False
- keyword_recall: 1.0
- token_recall: 0.9
- retrieval_hit: False
- evidence_hit: False
- evidence_recall: 0.0
- cited_support_rate: 0.0
- llm_error: 无

### 1705.09665 | train | 93f4ad6568207c9bd10d712a52f8de25b3ebadd4 | rag_500_100 | top_k=1
- 问题: How do the authors measure how distinctive a community is?
- 标准答案: How do the authors measure how distinctive a community is?
- 模型答案: The authors measure how distinctive a community is using a quantitative, language-based typology, but the specific metric or method for distinctiveness is not detailed in the provided chunk. The chunk only mentions that there is no significant relationship between distinctiveness and long-term engagement.
- 引用 chunks: rag_500_100_0045
- 召回块数: 1
- exact_match: False
- keyword_recall: 0.875
- token_recall: 0.8889
- retrieval_hit: False
- evidence_hit: False
- evidence_recall: 0.0
- cited_support_rate: 0.0
- llm_error: 无

### 1908.06606 | train | 71a7153e12879defa186bfb6dbafe79c74265e10 | rag_500_100 | top_k=1
- 问题: What data is the language model pretrained on?
- 标准答案: What data is the language model pretrained on?
- 模型答案: The document does not specify what data the language model is pretrained on.
- 引用 chunks: 无
- 召回块数: 1
- exact_match: False
- keyword_recall: 1.0
- token_recall: 1.0
- retrieval_hit: False
- evidence_hit: False
- evidence_recall: 0.0
- cited_support_rate: 0.0
- llm_error: 无

### 1908.06606 | train | 85d1831c28d3c19c84472589a252e28e9884500f | rag_500_100 | top_k=1
- 问题: What baselines is the proposed model compared against?
- 标准答案: What baselines is the proposed model compared against?
- 模型答案: The proposed model is compared against QANet and BERT-Base.
- 引用 chunks: rag_500_100_0034
- 召回块数: 1
- exact_match: False
- keyword_recall: 0.75
- token_recall: 0.75
- retrieval_hit: True
- evidence_hit: False
- evidence_recall: 1.0
- cited_support_rate: 0.0
- llm_error: 无

### 1909.00694 | train | 753990d0b621d390ed58f20c4d9e4f065f0dc672 | rag_500_100 | top_k=3
- 问题: What is the seed lexicon?
- 标准答案: a vocabulary of positive and negative predicates that helps determine the polarity score of an event
- 模型答案: The seed lexicon is a very small set of seed predicates that directly report one's emotions (e.g., 'to be glad' is positive).
- 引用 chunks: rag_500_100_0002, rag_500_100_0003
- 召回块数: 3
- exact_match: False
- keyword_recall: 0.5
- token_recall: 0.4
- retrieval_hit: False
- evidence_hit: False
- evidence_recall: 0.0
- cited_support_rate: 0.0
- llm_error: 无

### 1909.00694 | train | 9d578ddccc27dd849244d632dd0f6bf27348ad81 | rag_500_100 | top_k=3
- 问题: What are the results?
- 标准答案: Using all data to train: AL -- BiGRU achieved 0.843 accuracy, AL -- BERT achieved 0.863 accuracy, AL+CA+CO -- BiGRU achieved 0.866 accuracy, AL+CA+CO -- BERT achieved 0.835, accuracy, ACP -- BiGRU achieved 0.919 accuracy, ACP -- BERT achived 0.933, accuracy, ACP+AL+CA+CO -- BiGRU achieved 0.917 accuracy, ACP+AL+CA+CO -- BERT achieved 0.913 accuracy. 
Using a subset to train: BERT achieved 0.876 accuracy using ACP (6K), BERT achieved 0.886 accuracy using ACP (6K) + AL, BiGRU achieved 0.830 accuracy using ACP (6K), BiGRU achieved 0.879 accuracy using ACP (6K) + AL + CA + CO.
- 模型答案: The models performed well with minimum supervision. The combination of annotated and unannotated data yielded a gain over a purely supervised baseline when labeled data were small. From a corpus of about 100 million sentences, they obtained 1.4 million event pairs for AL, 41 million for CA, and 6 million for CO. Results are shown in Table TABREF16.
- 引用 chunks: rag_500_100_0004, rag_500_100_0021
- 召回块数: 3
- exact_match: False
- keyword_recall: 0.375
- token_recall: 0.2
- retrieval_hit: False
- evidence_hit: False
- evidence_recall: 0.0
- cited_support_rate: 0.0
- llm_error: 无

### 1909.00694 | train | 02e4bf719b1a504e385c35c6186742e720bcb281 | rag_500_100 | top_k=3
- 问题: How are relations used to propagate polarity?
- 标准答案: based on the relation between events, the suggested polarity of one event can determine the possible polarity of the other event
- 模型答案: Relations are used to propagate polarity by exploiting discourse relations such as Cause and Concession. For Cause, if the latter event (x2) has known polarity, the former event (x1) is assigned the same polarity. For Concession, x1 is assigned the opposite polarity of x2. This propagation is applied when the seed lexicon matches the latter event but not the former, and the relation type is Cause or Concession.
- 引用 chunks: rag_500_100_0002, rag_500_100_0003, rag_500_100_0012
- 召回块数: 3
- exact_match: False
- keyword_recall: 0.5
- token_recall: 0.3333
- retrieval_hit: True
- evidence_hit: False
- evidence_recall: 1.0
- cited_support_rate: 0.0
- llm_error: 无

### 1909.00694 | train | 44c4bd6decc86f1091b5fc0728873d9324cdde4e | rag_500_100 | top_k=3
- 问题: How big is the Japanese data?
- 标准答案: 7000000 pairs of events were extracted from the Japanese Web corpus, 529850 pairs of events were extracted from the ACP corpus
- 模型答案: The document does not specify the size of the Japanese data. It only mentions that a Japanese web corpus was used.
- 引用 chunks: rag_500_100_0004, rag_500_100_0003
- 召回块数: 3
- exact_match: False
- keyword_recall: 0.25
- token_recall: 0.3846
- retrieval_hit: False
- evidence_hit: False
- evidence_recall: 0.0
- cited_support_rate: 0.0
- llm_error: 无

### 1909.00694 | train | 86abeff85f3db79cf87a8c993e5e5aa61226dc98 | rag_500_100 | top_k=3
- 问题: What are labels available in dataset for supervision?
- 标准答案: What are labels available in dataset for supervision?
- 模型答案: The seed lexicon consists of 15 positive words and 15 negative words.
- 引用 chunks: rag_500_100_0022
- 召回块数: 3
- exact_match: False
- keyword_recall: 0.0
- token_recall: 0.0
- retrieval_hit: False
- evidence_hit: False
- evidence_recall: 0.0
- cited_support_rate: 0.0
- llm_error: 无

### 1909.00694 | train | c029deb7f99756d2669abad0a349d917428e9c12 | rag_500_100 | top_k=3
- 问题: How big are improvements of supervszed learning results trained on smalled labeled data enhanced with proposed approach copared to basic approach?
- 标准答案: 3%
- 模型答案: When labeled data are small (e.g., 6,000 events), the proposed method (semi-supervised with AL+CA+CO) is effective and yields a gain over a purely supervised baseline. However, the document does not provide exact numerical improvements.
- 引用 chunks: rag_500_100_0004, rag_500_100_0032
- 召回块数: 3
- exact_match: False
- keyword_recall: 0.0
- token_recall: 0.0
- retrieval_hit: False
- evidence_hit: False
- evidence_recall: 0.0
- cited_support_rate: 0.0
- llm_error: 无

### 1909.00694 | train | 39f8db10d949c6b477fa4b51e7c184016505884f | rag_500_100 | top_k=3
- 问题: How does their model learn using mostly raw data?
- 标准答案: by exploiting discourse relations to propagate polarity from seed predicates to final sentiment polarity
- 模型答案: The model uses a very small seed lexicon and a large raw corpus. It automatically extracts discourse-tagged event pairs (Cause and Concession) from the raw corpus. Events with predicates in the seed lexicon are assigned polarity scores (+1 or -1). For pairs where only the latter event has a seed match, the former event's polarity is inferred via discourse relations: same polarity for Cause, opposite for Concession. These inferred scores serve as reference for training, allowing the model to learn complex phenomena through label propagation.
- 引用 chunks: rag_500_100_0008, rag_500_100_0011, rag_500_100_0012
- 召回块数: 3
- exact_match: False
- keyword_recall: 0.625
- token_recall: 0.5833
- retrieval_hit: False
- evidence_hit: False
- evidence_recall: 0.0
- cited_support_rate: 0.0
- llm_error: 无

### 1909.00694 | train | d0bc782961567dc1dd7e074b621a6d6be44bb5b4 | rag_500_100 | top_k=3
- 问题: How big is seed lexicon used for training?
- 标准答案: 30 words
- 模型答案: The seed lexicon consists of 15 positive words and 15 negative words.
- 引用 chunks: rag_500_100_0022
- 召回块数: 3
- exact_match: False
- keyword_recall: 0.5
- token_recall: 0.5
- retrieval_hit: True
- evidence_hit: False
- evidence_recall: 1.0
- cited_support_rate: 0.0
- llm_error: 无

### 1909.00694 | train | a592498ba2fac994cd6fad7372836f0adb37e22a | rag_500_100 | top_k=3
- 问题: How large is raw corpus used for training?
- 标准答案: How large is raw corpus used for training?
- 模型答案: The raw corpus used for training is a Japanese web corpus, but its size is not specified in the document.
- 引用 chunks: rag_500_100_0003
- 召回块数: 3
- exact_match: False
- keyword_recall: 0.75
- token_recall: 0.75
- retrieval_hit: False
- evidence_hit: False
- evidence_recall: 0.0
- cited_support_rate: 0.0
- llm_error: 无

### 2003.07723 | train | 3a9d391d25cde8af3334ac62d478b36b30079d74 | rag_500_100 | top_k=3
- 问题: Does the paper report macro F1?
- 标准答案: Does the paper report macro F1?
- 模型答案: The paper reports F1 scores (e.g., ~.42 for German models) but does not explicitly mention macro F1.
- 引用 chunks: rag_500_100_0062
- 召回块数: 3
- exact_match: False
- keyword_recall: 1.0
- token_recall: 0.8571
- retrieval_hit: False
- evidence_hit: False
- evidence_recall: 0.0
- cited_support_rate: 0.0
- llm_error: 无
