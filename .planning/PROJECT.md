# RL-Xiangqi: 异构智能体象棋对战平台

## What This Is

一个基于异构多智能体强化学习的中国象棋对战平台。人类玩家通过桌面UI与AI对弈，AI由多种"棋子智能体"协作驱动。AI在与人对弈过程中持续在线学习，棋力可观测地提升。

## Core Value

人机对弈时AI能实时学习并持续变强，用户能直观感受到AI棋力随时间提升。

## Requirements

### Validated

- [x] Phase 1-4: 象棋引擎（纯规则，无UI/RL） — v0.1
- [x] Phase 5: 棋盘渲染（QGraphicsView，9×10 + 河/宫） — v0.2
- [x] Phase 6: 棋子交互（选子/高亮/落子） — v0.2
- [x] Phase 7: AIPlayer 接口 + RandomAI — v0.2
- [x] Phase 8: 游戏控制（新对局/悔棋） — v0.2
- [x] Phase 9: XiangqiEnv gym.Env core (reset/step/observation/action_masks/SyncVectorEnv) — v0.3
- [x] Phase 10: AlphaZero board planes (canonical rotation, 16 channels, repetition, halfmove) — v0.3
- [x] Phase 11: Per-piece-type action masking + reward signal — v0.3
- [x] Phase 12: Self-play E2E validation (100 games, 314 tests) — v0.3
- [x] Phase 13: Test suite fix (from_fen unpacking + QThread mock) — v0.3

### Active

- [ ] 论文采集脚本优化 — v1.0
- [ ] 两阶段关键词设计（广泛检索 + 精细抽取） — v1.0
- [ ] 文献筛选与技术分析 — v1.0
- [ ] 异构智能体预测协作RL算法设计 — v1.0

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
- **Codebase**: `src/xiangqi/engine/` + `src/xiangqi/ui/` + `src/xiangqi/controller/` + `src/xiangqi/ai/` + `src/xiangqi/rl/`
- **Test Suite**: 314 tests passing, 1 skipped, 0 failures
- **LOC**: ~3,030 Python (src/)
- **Git Range**: v0.1 (2026-03-19) → v0.3 (2026-03-29) — ~290 commits

## Current Milestone: v1.0 Explore RL for Heterogeneous Agent Predictive Collaboration

**Goal:** 研究驱动的里程碑 — 探索、筛选和分析面向异构智能体预测协作的强化学习技术

**Target features:**
- 论文采集脚本优化（dblp_search.py + dblp_keywords_extract.py）
- 两阶段关键词设计（广泛检索 + 精细抽取），依赖AIM论文深入讨论
- 用户手动文献筛选 + 迭代关键词优化
- 技术分析与异构智能体预测协作RL算法设计

**Start:** 2026-03-29

## Milestones

| Version | Status | Description |
|---------|--------|-------------|
| v0.1 | Complete | 象棋引擎（纯规则，无UI/RL） |
| v0.2 | Complete | PyQt6 UI + RandomAI + AI 接口 |
| v0.3 | Complete | 多智能体Gymnasium RL环境 |
| v1.0 | — | 探索异构智能体预测协作的强化学习技术 |

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 异构智能体架构 | 不同棋子移动方式差异大，独立策略更合理 | v0.1: 棋子走法架构设计完成 |
| 独立提议+仲裁 | 各棋子智能体提出候选走法，仲裁网络选择最优 | v0.1: RL环境接口待实现 |
| Shaping奖励 | 纯终局奖励稀疏，中间奖励加速学习 | v0.3: 终局+物质奖励完成，团队奖励→v1.0 |
| 从零开始 | 验证在线学习能力，不依赖先验知识 | v0.1: 引擎无预训练依赖 |
| 桌面应用 | 本地训练需要计算资源，桌面更稳定 | v0.1: PyQt6 UI完成 |
| Move encoding: 7-bit to_sq | 原plan为9-bit有bit overlap bug；修正后范围0-89只需7 bits | v0.1 |
| RepetitionState在engine.py | XiangqiState为纯棋盘状态；重复跟踪是游戏历史策略 | v0.1 |
| 长将→DRAW，长捉→捉方负 | WXO规则：长将无法解除→和棋；长捉属故意拖延→判负 | v0.1 |
| PyQt6 float坐标包装 | fillRect用QRectF、drawLine用QLineF包装浮点坐标 | v0.2 |
| Turn-aware piece selection | piece_value * engine.turn > 0 for correct side selection | v0.2 |
| EngineSnapshot frozen=True | Thread-safe state capture for AI worker threads | v0.2 |
| Double-step undo | Human+AI move pair undone together in one undo() | v0.2 |
| Multi-agent Gymnasium | 7 independent piece-type agents, no communication, team rewards | v0.3 |
| Flat Discrete(8100) action space | Simplest; mask filters illegal moves; proven approach | v0.3 |
| 16-channel AlphaZero board planes | 7 piece types × 2 colors + repetition + halfmove clock | v0.3 |
| Canonical rotation with negation | -np.rot90(board, k=2) negates piece values; active player always channels 0-6 | v0.3 |
| WXF FEN 5-field detection | parts[3][0].isdigit() distinguishes WXF from standard 6-field | v0.3 |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-03-29 — v1.0 milestone started*
