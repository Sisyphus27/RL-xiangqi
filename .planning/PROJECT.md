# RL-Xiangqi: 异构智能体象棋对战平台

## What This Is

一个基于异构多智能体强化学习的中国象棋对战平台。人类玩家通过桌面UI与AI对弈，AI由多种"棋子智能体"协作驱动。AI在与人对弈过程中持续在线学习，棋力可观测地提升。

## Core Value

人机对弈时AI能实时学习并持续变强，用户能直观感受到AI棋力随时间提升。

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] 中国象棋完整规则实现（含将军检测、胜负判定）
- [ ] 异构多智能体架构：每种棋子类型作为独立智能体
- [ ] 独立提议+仲裁的协作决策机制
- [ ] PyQt6桌面UI：棋盘显示、棋子拖拽、走法合法性校验
- [ ] 在线学习：人机对弈时实时训练
- [ ] 混合更新策略：每步轻量更新 + 终局深度优化
- [ ] Shaping奖励设计（吃子、控盘等中间奖励）
- [ ] MPS后端支持（Apple Silicon优化）
- [ ] 模型自动保存（每局结束后）
- [ ] 训练可视化（loss曲线、棋力指标）

### Out of Scope

- 在线多人对战 — 专注于人机对弈与在线学习
- 棋谱导入/导出 — 从零开始学习，不依赖人类棋谱
- 开局库/残局库 — 纯RL驱动，不依赖 handcrafted 知识
- 移动端支持 — 仅桌面应用
- 其他棋类（国际象棋、围棋）— 专注于中国象棋

## Context

- **平台**: MacBook Pro M1 Max 32GB
- **后端**: PyTorch MPS (Apple Silicon Metal Performance Shaders)
- **UI框架**: PyQt6
- **RL框架**: 自定义实现（或Stable-Baselines3适配）

## Constraints

- **Tech Stack**: Python + PyTorch + PyQt6 — 用户熟悉，生态成熟
- **Hardware**: Apple Silicon MPS — 无CUDA，需适配MPS后端
- **Learning**: 从零开始 — 不依赖预训练，完全在线学习
- **Architecture**: 异构多智能体 — 每种棋子独立网络，协作决策

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 异构智能体架构 | 不同棋子移动方式差异大，独立策略更合理 | — Pending |
| 独立提议+仲裁 | 各棋子智能体提出候选走法，仲裁网络选择最优 | — Pending |
| Shaping奖励 | 纯终局奖励稀疏，中间奖励加速学习 | — Pending |
| 从零开始 | 验证在线学习能力，不依赖先验知识 | — Pending |
| 桌面应用 | 本地训练需要计算资源，桌面更稳定 | — Pending |

---
*Last updated: 2026-03-19 after initialization*
