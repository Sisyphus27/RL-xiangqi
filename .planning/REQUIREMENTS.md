# Requirements: RL-Xiangqi

**Defined:** 2026-03-19
**Core Value:** 人机对弈时AI能实时学习并持续变强，用户能直观感受到AI棋力随时间提升

## v1 Requirements

### Game Engine

- [ ] **ENG-01**: 系统实现完整中国象棋棋盘状态表示（9列×10行，红/黑双方）
- [ ] **ENG-02**: 系统为7种棋子类型（将/帅、仕/士、相/象、车、马、炮、兵/卒）实现合法走法生成
- [ ] **ENG-03**: 系统检测将军状态并拒绝导致己方将军的走法
- [ ] **ENG-04**: 系统判定将死（输）和困毙（无子可动即输）终局状态
- [ ] **ENG-05**: 系统按WXF标准实现永久将/永久追规则（判负检测）
- [ ] **ENG-06**: 系统记录完整局面历史，支持重复局面检测（60步无吃子判和）

### UI

- [ ] **UI-01**: 界面渲染9×10象棋棋盘，显示棋子图标，区分红黑双方
- [ ] **UI-02**: 用户通过点击选中己方棋子，再点击目标格完成走棋
- [ ] **UI-03**: 选中棋子后高亮显示合法目标格；高亮显示AI上一步走法
- [ ] **UI-04**: 界面提供"新局"、"暂停/继续"、"投降"控制按钮
- [ ] **UI-05**: AI计算在独立QThread中运行，不阻塞UI主线程

### RL Architecture

- [ ] **RL-01**: 系统为7种棋子类型各创建独立策略网络（异构智能体）
- [ ] **RL-02**: 每步AI决策时，当前局面所有可动棋子各提议候选走法，仲裁网络选出最终走法
- [ ] **RL-03**: 系统在PyTorch MPS后端运行，强制float32，设置MPS fallback环境变量
- [ ] **RL-04**: 系统在程序启动时验证MPS可用性，可降级至CPU

### Online Learning

- [ ] **OL-01**: 每步走棋后执行轻量级策略更新（小batch梯度步）
- [ ] **OL-02**: 每局结束后执行深度PPO优化（多epoch，完整局面数据）
- [ ] **OL-03**: 系统维护循环经验回放缓冲区，混合当前与历史对局数据
- [ ] **OL-04**: 奖励函数包含中间Shaping奖励：吃子价值差、棋盘控制评估
- [ ] **OL-05**: 每局结束后自动保存模型检查点，支持断点续训

### Observability

- [ ] **OBS-01**: 实时显示训练指标：每步loss、每局累计奖励、更新次数
- [ ] **OBS-02**: 显示AI棋力评分趋势（基于近N局胜率的滑动窗口ELO估计）
- [ ] **OBS-03**: 每步AI走棋时显示各候选走法的得分及仲裁结果
- [ ] **OBS-04**: 显示历史对局胜/负/和统计

### Self-play Warm-up

- [ ] **SP-01**: 首次启动时执行自我对弈预热（默认200局），再开放人机对战

## v2 Requirements

### Advanced Features

- **ADV-01**: 棋谱导出（PGN/中国象棋标准格式）
- **ADV-02**: 难度调节（限制仲裁网络搜索深度）
- **ADV-03**: 复盘模式（逐步回放历史对局）
- **ADV-04**: 多AI风格（保存不同训练阶段的模型供选择）

## Out of Scope

| Feature | Reason |
|---------|--------|
| 在线多人对战 | 专注人机对弈与在线学习，联网功能超出v1范围 |
| 棋谱导入/预训练 | 从零开始是核心设计，引入先验知识破坏实验目的 |
| 开局库/残局库 | 纯RL驱动，不依赖handcrafted知识 |
| 移动端支持 | 仅桌面应用，M1 Max是唯一目标平台 |
| 国际象棋/围棋 | 专注中国象棋 |
| 拖拽走棋 | 点击操作已足够，拖拽增加UI复杂度但不提升核心价值 |

## Traceability

*Updated during roadmap creation*

| Requirement | Phase | Status |
|-------------|-------|--------|
| ENG-01 | Phase 1 | Pending |
| ENG-02 | Phase 1 | Pending |
| ENG-03 | Phase 1 | Pending |
| ENG-04 | Phase 1 | Pending |
| ENG-05 | Phase 1 | Pending |
| ENG-06 | Phase 1 | Pending |
| UI-01 | Phase 2 | Pending |
| UI-02 | Phase 2 | Pending |
| UI-03 | Phase 2 | Pending |
| UI-04 | Phase 2 | Pending |
| UI-05 | Phase 2 | Pending |
| RL-01 | Phase 3 | Pending |
| RL-02 | Phase 3 | Pending |
| RL-03 | Phase 3 | Pending |
| RL-04 | Phase 3 | Pending |
| OL-01 | Phase 4 | Pending |
| OL-02 | Phase 4 | Pending |
| OL-03 | Phase 4 | Pending |
| OL-04 | Phase 4 | Pending |
| OL-05 | Phase 4 | Pending |
| OBS-01 | Phase 5 | Pending |
| OBS-02 | Phase 5 | Pending |
| OBS-03 | Phase 5 | Pending |
| OBS-04 | Phase 5 | Pending |
| SP-01 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 25 total
- Mapped to phases: 25
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-19*
*Last updated: 2026-03-19 after initial definition*
