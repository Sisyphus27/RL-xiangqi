# RL-Xiangqi: 异构智能体象棋对战平台

## What This Is

一个基于异构多智能体强化学习的中国象棋对战平台。人类玩家通过桌面UI与AI对弈，AI由多种"棋子智能体"协作驱动。AI在与人对弈过程中持续在线学习，棋力可观测地提升。

## Core Value

人机对弈时AI能实时学习并持续变强，用户能直观感受到AI棋力随时间提升。

## Requirements

### Validated

- [x] Phase 1-4: 象棋引擎（纯规则，无UI/RL） — v0.1 ✓
- [x] Phase 5: 棋盘渲染（QGraphicsView，9×10 + 河/宫） — v0.2 ✓ — 28 tests passing
- [x] Phase 6: 棋子交互（选子/高亮/落子） — v0.2 ✓
- [x] Phase 7: AIPlayer 接口 + RandomAI — v0.2 ✓ — 22 tests passing
- [x] Phase 8: 游戏控制（新对局/悔棋） — v0.2 ✓ — 7 UAT tests passing

### Active

- [ ] Gymnasium RL Environment — v0.3
- [ ] Alpha-Beta / MCTS AI — v1.0
- [ ] 异构多智能体架构 — v1.0
- [ ] 在线学习（实时训练） — v1.0
- [ ] PyQt6 桌面 UI 增强 — v0.2/v0.3

### Out of Scope

- 在线多人对战 — 专注于人机对弈与在线学习
- 棋谱导入/导出 — 从零开始学习，不依赖人类棋谱
- 开局库/残局库 — 纯RL驱动，不依赖 handcrafted 知识
- 移动端支持 — 仅桌面应用
- 其他棋类（国际象棋、围棋）— 专注于中国象棋

## Context

- **Platform**: Windows 11 Pro
- **Backend**: Python 3.x + PyTorch
- **UI Framework**: PyQt6 (desktop app working)
- **RL Framework**: Gymnasium + Stable-Baselines3 (planned)
- **Codebase**: `src/xiangqi/engine/` + `src/xiangqi/ui/` + `src/xiangqi/controller/` + `src/xiangqi/ai/`
- **Test Suite**: 207+ tests passing
- **Git Range**: v0.1 (2026-03-19) → v0.2 (2026-03-26) — ~112 commits

## Current Milestone: v0.2 COMPLETE ✅

**Shipped:** 2026-03-26
**Features:** PyQt6 board + RandomAI + AI interface + game control
**Requirements:** 13/13 satisfied
**Archive:** `.planning/milestones/v0.2-ROADMAP.md`

## Next Milestone: v0.3 Gymnasium RL Environment

**Goal:** Create Gymnasium-compatible RL environment for training

**Target features:**
- Gymnasium `Env` interface: `reset()`, `step()`, `observation_space`, `action_space`
- AlphaZero-style board planes observation format
- Shaping rewards (piece capture, center control)

**Start:** `/gsd:new-milestone v0.3`

## Milestones

| Version | Status | Description |
|---------|--------|-------------|
| v0.1 | ✓ Complete | 象棋引擎（纯规则，无UI/RL） |
| v0.2 | ✓ Complete | PyQt6 UI + RandomAI + AI 接口 |
| v0.3 | — Next | Gymnasium RL Environment |
| v1.0 | — | AI 对弈（Alpha-Beta / MCTS） |

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 异构智能体架构 | 不同棋子移动方式差异大，独立策略更合理 | v0.1: 棋子走法架构设计完成 |
| 独立提议+仲裁 | 各棋子智能体提出候选走法，仲裁网络选择最优 | v0.1: RL环境接口待实现 |
| Shaping奖励 | 纯终局奖励稀疏，中间奖励加速学习 | v0.1: 终局判定完成，奖励设计待v0.2 |
| 从零开始 | 验证在线学习能力，不依赖先验知识 | v0.1: 引擎无预训练依赖 |
| 桌面应用 | 本地训练需要计算资源，桌面更稳定 | v0.1: PyQt6 UI完成 |
| Move encoding: 7-bit to_sq | 原plan为9-bit有bit overlap bug；修正后范围0-89只需7 bits | ✓ v0.1 |
| RepetitionState在engine.py | XiangqiState为纯棋盘状态；重复跟踪是游戏历史策略 | ✓ v0.1 |
| 长将→DRAW，长捉→捉方负 | WXO规则：长将无法解除→和棋；长捉属故意拖延→判负 | ✓ v0.1 |
| PyQt6 float坐标包装 | fillRect用QRectF、drawLine用QLineF包装浮点坐标 | ✓ v0.2 |
| Turn-aware piece selection | piece_value * engine.turn > 0 for correct side selection | ✓ v0.2 (06-05) |
| EngineSnapshot frozen=True | Thread-safe state capture for AI worker threads | ✓ v0.2 (07-01) |
| Double-step undo | Human+AI move pair undone together in one undo() | ✓ v0.2 (08-02) |

---

*Last updated: 2026-03-26 after v0.2 milestone completion*
