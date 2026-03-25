# Requirements: RL-Xiangqi v0.2

**Defined:** 2026-03-23
**Core Value:** 人机对弈时AI能实时学习并持续变强，用户能直观感受到AI棋力随时间提升

## v1 Requirements

### UI-01: Board Rendering

- [x] **UI-01**: PyQt6 `QGraphicsView` + `QGraphicsScene` 渲染 9×10 象棋盘（网格 + 河 + 九宫斜线）
- [x] **UI-02**: 棋子使用引擎 Piece 枚举的中文字符渲染（`QGraphicsSimpleTextItem`），红黑区分颜色

### UI-02: Interaction

- [x] **UI-03**: 点击己方棋子选中，合法走法目标格高亮显示
- [x] **UI-04**: 点击合法走法目标格执行走法，调用 `engine.apply()`
- [x] **UI-05**: 点击非法目标格/空格时取消选子，无效交互

### UI-03: Game State

- [ ] **UI-06**: 当前回合提示（红方/黑方）
- [ ] **UI-07**: 对局结束提示（红胜/黑胜/和棋），弹窗显示

### UI-04: AI Interface

- [x] **AI-01**: `AIPlayer` 抽象基类，接口 `suggest_move(snapshot) -> Move | None`
- [x] **AI-02**: `EngineSnapshot` 数据类，封装棋盘数组、回合、合法走法（线程安全）
- [ ] **AI-03**: `RandomAI` 实现，黑方随机选合法走法
- [ ] **AI-04**: AI 走子时 UI 显示"AI 思考中..."提示，走完后自动消失

### UI-05: Game Control

- [ ] **UI-08**: 新对局按钮，重置到初始局面
- [ ] **UI-09**: 悔棋功能（`engine.undo()`），支持连续悔棋

## v2 Requirements

Deferred to future milestones.

### RL Environment

- **RL-01**: Gymnasium `Env` 接口：`reset()`, `step()`, `observation_space`, `action_space`
- **RL-02**: AlphaZero 风格 board planes 观测格式
- **RL-03**: Shaping 奖励设计（吃子、控盘中间奖励）

### AI Enhancement

- **AI-05**: `AlphaBetaAI` 评估函数接入
- **AI-06**: `MCTSAI` 蒙特卡洛树搜索
- **AI-07**: RL 智能体接入（heterogeneous piece agents）

## Out of Scope

| Feature | Reason |
|---------|--------|
| 被吃棋子区域 | MVP 阶段不需要，以后可加 |
| 将军视觉高亮 | MVP 阶段不需要，胜负提示已覆盖 |
| 走法历史记录 | MVP 阶段不需要，纯对弈界面 |
| 拖拽落子 | 点击落子已足够，拖拽增加复杂度 |
| 音效 | MVP 阶段不需要 |
| 计时系统 | MVP 阶段不需要 |
| PGN/棋谱导入导出 | 未来功能 |
| 网络对战 | 专注人机对弈 + 在线学习 |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| UI-01 | Phase 05 | Complete |
| UI-02 | Phase 05 | Complete |
| UI-03 | Phase 06 | Complete |
| UI-04 | Phase 06 | Complete |
| UI-05 | Phase 06 | Complete |
| UI-06 | Phase 07 | Pending |
| UI-07 | Phase 07 | Pending |
| AI-01 | Phase 07 | Complete |
| AI-02 | Phase 07 | Complete |
| AI-03 | Phase 07 | Pending |
| AI-04 | Phase 07 | Pending |
| UI-08 | Phase 08 | Pending |
| UI-09 | Phase 08 | Pending |

**Coverage:**
- v1 requirements: 13 total
- Mapped to phases: 13
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-23*
*Last updated: 2026-03-23 after v0.2 roadmap creation (phase numbering aligned to v0.2 roadmap: 05-08)*
