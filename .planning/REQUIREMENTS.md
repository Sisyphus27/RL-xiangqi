# Milestone v1.0 Requirements

## Literature Collection Pipeline

### LIT (Literature Collection)

- [ ] **LIT-01**: 研究者可以重新设计 `dblp_config.json` 中的搜索关键词，从超图/交通领域替换为MARL/异构智能体/预测协作领域
- [ ] **LIT-02**: 研究者可以设计两阶段关键词：阶段1（广泛检索）覆盖MARL核心术语，阶段2（精细抽取）使用嵌套AND/OR逻辑精确筛选
- [ ] **LIT-03**: 研究者可以添加AAMAS等多智能体相关会议到搜索范围
- [ ] **LIT-04**: 研究者可以运行 `dblp_search.py` 进行广泛检索并生成CSV结果
- [ ] **LIT-05**: 研究者可以运行 `dblp_keywords_extract.py` 进行精细关键词筛选并生成短名单Excel
- [ ] **LIT-06**: 研究者可以通过手动筛选短名单论文，记录纳入/排除决策及理由
- [ ] **LIT-07**: 研究者可以为每篇纳入的论文收集完整文本（markdown格式存入 papers/ 目录）

### ITER (Iteration & Discovery)

- [ ] **ITER-01**: 研究者可以根据筛选反馈迭代优化关键词，重新运行管线获取增量结果
- [ ] **ITER-02**: 研究者可以从已纳入论文的参考文献中发现并补充遗漏的相关论文

---

## Future Requirements (Deferred)

### TECH (Technical Analysis) — 后续里程碑

- 逐篇论文技术分析（方法、优缺点、可借鉴技术点）
- 跨论文综合分析文档
- 技术趋势提炼

### ALGO (Algorithm Design) — 后续里程碑

- CTDE框架选型
- 值分解方法选择（QTypeMix/QPLEX/MAPPO）
- 异构感知混合网络设计
- 奖励设计（协作奖励加成、课程学习）
- 完整算法规格说明书

---

## Out of Scope

| Item | Reason |
|------|--------|
| 修改 dblp_search.py 或 dblp_keywords_extract.py 代码 | 现有脚本已通过配置驱动，无需代码修改 |
| 构建筛选Web UI | 单研究者CSV筛选已足够，无需过度工程化 |
| 算法实现代码 | v1.0为研究里程碑，算法实现在后续里程碑 |
| RL训练框架集成 | 待算法设计确定后再选型 |
| 技术分析与综合 | 推迟到后续里程碑 |

---

## Traceability

| REQ-ID | Phase | Status |
|--------|-------|--------|
| LIT-01 | — | — |
| LIT-02 | — | — |
| LIT-03 | — | — |
| LIT-04 | — | — |
| LIT-05 | — | — |
| LIT-06 | — | — |
| LIT-07 | — | — |
| ITER-01 | — | — |
| ITER-02 | — | — |

---
*Requirements for: RL-Xiangqi v1.0 — Heterogeneous Agent Predictive Collaboration Literature Pipeline*
*Created: 2026-03-29*
