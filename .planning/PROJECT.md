# RL-Xiangqi: 异构智能体象棋对战平台

## What This Is

一个基于异构多智能体强化学习的中国象棋对战平台。人类玩家通过桌面UI与AI对弈，AI由多种"棋子智能体"协作驱动。AI在与人对弈过程中持续在线学习，棋力可观测地提升。

## Core Value

人机对弈时AI能实时学习并持续变强，用户能直观感受到AI棋力随时间提升。

## Requirements

### Validated

- [x] Phase 1: 数据结构 (v0.1) — 棋盘表示 (DATA-01), Piece枚举 (DATA-02), 走法编码 (DATA-03), XiangqiState (DATA-04), FEN与边界掩码 (DATA-05) — 28 tests passing
- [x] Phase 2: 棋子走法与规则校验 (v0.1) — 所有7种棋子的合法走法生成，将军/应将检测 — 94 tests passing
- [x] Phase 3: 终局判定 (v0.1) — 将死/困毙/和棋规则（含长将/长捉/重复局面）— 30 tests passing
- [x] Phase 4: API 接口 (v0.1) — XiangqiEngine公共API，FEN往返，undo/redo，perft验证 — 47 tests passing
- [x] Phase 4.1: Bugfix — is_legal()几何校验，legal_moves()性能优化（29ms→0.54ms）— 47 tests passing
- [x] Phase 5: 棋盘渲染 (v0.2) — PyQt6 QGraphicsView棋盘，9×10网格，河界，宫斜线，32个棋子渲染 — 28 tests passing

### Active

- [x] Phase 1-4: 象棋引擎（纯规则，无UI/RL） — v0.1 ✓
- [x] Phase 5: 棋盘渲染（QGraphicsView，9×10 + 河/宫） — v0.2 ✓ — 28 tests passing
- [ ] 棋子交互（选子/高亮/落子） — v0.2
- [ ] AIPlayer 接口 + RandomAI — v0.2
- [ ] 游戏控制（新对局/悔棋） — v0.2
- [ ] Gymnasium RL Environment — v0.3
- [ ] PyQt6 桌面 UI — v0.2/v0.3
- [ ] 异构多智能体架构 — v1.0
- [ ] Alpha-Beta / MCTS AI — v1.0
- [ ] 在线学习（实时训练） — v1.0
- [ ] MPS 后端支持（Apple Silicon） — v1.0

### Out of Scope

- 在线多人对战 — 专注于人机对弈与在线学习
- 棋谱导入/导出 — 从零开始学习，不依赖人类棋谱
- 开局库/残局库 — 纯RL驱动，不依赖 handcrafted 知识
- 移动端支持 — 仅桌面应用
- 其他棋类（国际象棋、围棋）— 专注于中国象棋

## Context

- **Platform**: MacBook Pro M1 Max 32GB
- **Backend**: PyTorch MPS (Apple Silicon Metal Performance Shaders)
- **UI Framework**: PyQt6 (pending v0.3)
- **RL Framework**: Custom or Stable-Baselines3
- **Codebase**: `src/xiangqi/engine/` — 4,056 lines Python
- **Test Suite**: 179 passed, 1 skipped (pyffish unavailable)
- **Git Range**: 2026-03-19 → 2026-03-21 (2 days, ~20 commits)
- **Phase Count**: 7 phases, 11 plans completed

## Current Milestone: v0.2 PyQt6 UI

**Goal:** 人机对弈界面（PyQt6）+ RandomAI + AI 抽象接口

**Target features:**
- 棋盘渲染（QGraphicsView + QGraphicsScene，9×10 + 河/宫）
- 棋子交互（点击选子 + 合法走法高亮 + 落子）
- AI 接口（AIPlayer ABC + EngineSnapshot + RandomAI）
- 游戏控制（新对局 + 悔棋）

## Milestones

| Version | Status | Description |
|---------|--------|-------------|
| v0.1 | ✓ Complete | 象棋引擎（纯规则，无UI/RL） |
| v0.2 | — In Progress | PyQt6 UI + RandomAI + AI 接口 |
| v0.3 | — | Gymnasium RL Environment |
| v1.0 | — | AI 对弈（Alpha-Beta / MCTS） |

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 异构智能体架构 | 不同棋子移动方式差异大，独立策略更合理 | v0.1: 棋子走法架构设计完成 |
| 独立提议+仲裁 | 各棋子智能体提出候选走法，仲裁网络选择最优 | v0.1: RL环境接口待实现 |
| Shaping奖励 | 纯终局奖励稀疏，中间奖励加速学习 | v0.1: 终局判定完成，奖励设计待v0.2 |
| 从零开始 | 验证在线学习能力，不依赖先验知识 | v0.1: 引擎无预训练依赖 |
| 桌面应用 | 本地训练需要计算资源，桌面更稳定 | v0.1: PyQt6 UI待实现 |
| Move encoding: 7-bit to_sq | 原plan为9-bit有bit overlap bug；修正后范围0-89只需7 bits | ✓ v0.1 |
| RepetitionState在engine.py | XiangqiState为纯棋盘状态；重复跟踪是游戏历史策略 | ✓ v0.1 |
| 长将→DRAW，长捉→捉方负 | WXO规则：长将无法解除→和棋；长捉属故意拖延→判负 | ✓ v0.1 |
| 几何校验在board copy前 | is_legal()先验证走法几何（O(1)），再做board copy后检查 | ✓ v0.1 (Bug 1 fix) |
| 己方棋子预过滤 | generate_legal_moves()先过滤己方目的格，避免不必要board copy | ✓ v0.1 (Bug 2 fix, 58x perf) |
| 兵前进方向：红-1/黑+1 | 红兵向敌方阵地（row减少），黑兵向红方阵地（row增加） | ✓ v0.1 (Bug fix) |
| Stalemate=负（中国规则） | 困毙=无合法走法，无论是否被将军均判负 | ✓ v0.1 |

---
*Last updated: 2026-03-24 after Phase 05 gap closure (fillRect TypeError fix)*
