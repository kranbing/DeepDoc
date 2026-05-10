# LAD-RAG vs Traditional RAG 对比测试设计

## 测试目标

验证LAD-RAG（hybrid种子8 + section_first扩展）相比传统RAG的优势。

## 测试配置

### 方法定义

| 方法 | 描述 | 配置 |
|------|------|------|
| **Traditional RAG** | 直接hybrid检索 | top_k=10/15/20 |
| **LAD-RAG** | hybrid种子 + 结构扩展 | seed=8, section_first, total=10/15/20 |

### 测试变量

#### 1. 总块数（Total Chunks）
- 10块：轻量级场景
- 15块：标准场景
- 20块：完整场景

#### 2. 问题类型（按difficulty分）
- single_section：单章节问题（27个）
- cross_section：跨章节问题（25个）

#### 3. 问题类型（按category分）
- fact：事实型问题
- method：方法型问题
- result：结果型问题
- comparison：比较型问题
- multi_evidence：多证据问题

### 测试矩阵

| 方法 | 总块数 | 问题数 |
|------|--------|--------|
| Traditional RAG | 10 | 52 |
| Traditional RAG | 15 | 52 |
| Traditional RAG | 20 | 52 |
| LAD-RAG | 10 | 52 |
| LAD-RAG | 15 | 52 |
| LAD-RAG | 20 | 52 |

**总计：6组实验 × 52个问题 = 312次评估**

## 评估指标

### 主要指标
1. **Chunk Recall**：精确匹配证据块的比例
2. **Token Recall**：内容覆盖度（token级别）
3. **Section Recall**：章节覆盖度

### 辅助指标
4. **MRR**：平均倒数排名
5. **Hit Rate**：命中率（至少找到一个证据块的比例）

## 分析维度

### 1. 整体对比
- 各方法在所有问题上的平均表现
- LAD-RAG vs Traditional的改进百分比

### 2. 按问题难度对比
- single_section问题的表现
- cross_section问题的表现

### 3. 按问题类型对比
- 各category的表现差异
- LAD-RAG对不同类型问题的改进

### 4. 统计显著性
- 使用配对t检验
- 计算p值和置信区间

## 预期结果

### 假设
1. LAD-RAG在cross_section问题上改进更大
2. LAD-RAG在multi_evidence问题上改进更大
3. 总块数越多，LAD-RAG优势越明显

### 基线
- Traditional RAG (top-15)：Chunk Recall = 0.5775

### 目标
- LAD-RAG (seed8, section_first, total=15)：Chunk Recall > 0.60

## 输出格式

### 结果表格

```
| Method | Total | Chunk R | Token R | Section R | MRR | Hit |
|--------|-------|---------|---------|-----------|-----|-----|
| Trad   | 10    | x.xxx   | x.xxx   | x.xxx     | x.xx| x.xx|
| Trad   | 15    | x.xxx   | x.xxx   | x.xxx     | x.xx| x.xx|
| Trad   | 20    | x.xxx   | x.xxx   | x.xxx     | x.xx| x.xx|
| LAD    | 10    | x.xxx   | x.xxx   | x.xxx     | x.xx| x.xx|
| LAD    | 15    | x.xxx   | x.xxx   | x.xxx     | x.xx| x.xx|
| LAD    | 20    | x.xxx   | x.xxx   | x.xxx     | x.xx| x.xx|
```

### 改进分析

```
| Total | Chunk R Imp | Token R Imp | Section R Imp | p-value |
|-------|-------------|-------------|---------------|---------|
| 10    | +x.xx%      | +x.xx%      | +x.xx%        | x.xxx   |
| 15    | +x.xx%      | +x.xx%      | +x.xx%        | x.xxx   |
| 20    | +x.xx%      | +x.xx%      | +x.xx%        | x.xxx   |
```

### 按问题类型分析

```
| Category | Trad Chunk R | LAD Chunk R | Improvement |
|----------|--------------|-------------|-------------|
| fact     | x.xxx        | x.xxx       | +x.xx%      |
| method   | x.xxx        | x.xxx       | +x.xx%      |
| result   | x.xxx        | x.xxx       | +x.xx%      |
| ...      | ...          | ...         | ...         |
```

## 代码文件

### 主测试脚本
- `lad_rag_final_comparison.py` - 最终对比测试

### 辅助文件
- `EXPERIMENT_REPORT.md` - 实验报告
- `COMPARISON_TEST_DESIGN.md` - 本文件

## 执行计划

1. **代码实现**：编写对比测试脚本
2. **用户审核**：提交设计供用户确认
3. **执行测试**：运行对比实验
4. **结果分析**：生成报告和可视化
5. **结论总结**：确定LAD-RAG是否优于传统RAG

## 风险与注意事项

1. **样本量**：52个问题可能不够大，结果可能有波动
2. **数据集偏差**：Qasper是学术论文，可能不适用于其他文档类型
3. **模型选择**：使用bge-small-zh-v1.5（中文模型），英文数据集可能不是最优

## 待确认事项

请确认以下设计是否符合预期：

1. ✅ 总块数测试：10, 15, 20
2. ✅ LAD-RAG参数：seed=8, section_first
3. ✅ 评估指标：Chunk Recall, Token Recall, Section Recall
4. ✅ 分析维度：整体、按难度、按类型
5. ❓ 是否需要其他测试维度？
