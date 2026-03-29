# Roadmap: RL-Xiangqi

## Milestones

- **v0.1** - Xiangqi Rule Engine (2026-03-19) [[archived]](milestones/v0.1-ROADMAP.md)
- **v0.2** - PyQt6 UI + RandomAI + AI Interface (2026-03-26) [[archived]](milestones/v0.2-ROADMAP.md)
- **v0.3** - Multi-Agent Gymnasium RL Environment (2026-03-29) [[archived]](milestones/v0.3-ROADMAP.md)
- **v1.0** - Heterogeneous Multi-Agent Training + Alpha-Beta/MCTS

## Phases

<details>
<summary>v0.1 Core Engine (Phases 01-04) — SHIPPED 2026-03-19</summary>

- [x] Phase 01: Board & State (4/4 plans)
- [x] Phase 02: Move Generation (4/4 plans)
- [x] Phase 03: Endgame Rules (4/4 plans)
- [x] Phase 04: Engine Public API (5/5 plans)

</details>

<details>
<summary>v0.2 PyQt6 UI + RandomAI (Phases 05-08) — SHIPPED 2026-03-26</summary>

- [x] Phase 05: Board Rendering (5/5 plans)
- [x] Phase 06: Piece Interaction (6/6 plans)
- [x] Phase 07: AI Interface (6/6 plans)
- [x] Phase 08: Game Control (5/5 plans)

</details>

<details>
<summary>v0.3 Gymnasium RL Environment (Phases 09-13) — SHIPPED 2026-03-29</summary>

- [x] Phase 09: XiangqiEnv Core (5/5 plans) — completed 2026-03-27
- [x] Phase 10: Observation Encoding (2/2 plans) — completed 2026-03-28
- [x] Phase 11: Per-Piece-Type Action Masking (2/2 plans) — completed 2026-03-28
- [x] Phase 12: Self-Play E2E Validation (1/1 plan) — completed 2026-03-28
- [x] Phase 13: Fix Test Suite (1/1 plan) — completed 2026-03-29

</details>

### v1.0 Heterogeneous Multi-Agent Training (Planned)

- [ ] Per-piece-type policy networks (7 networks)
- [ ] Team reward shaping + cooperation bonuses
- [ ] Arbitration network for move selection
- [ ] Alpha-Beta / MCTS AI opponent

## Progress

| Phase | Milestone | Plans | Status | Completed |
|-------|-----------|-------|--------|-----------|
| 01-04 | v0.1 | 17/17 | Complete | 2026-03-19 |
| 05-08 | v0.2 | 22/22 | Complete | 2026-03-26 |
| 09 | v0.3 | 5/5 | Complete | 2026-03-27 |
| 10 | v0.3 | 2/2 | Complete | 2026-03-28 |
| 11 | v0.3 | 2/2 | Complete | 2026-03-28 |
| 12 | v0.3 | 1/1 | Complete | 2026-03-28 |
| 13 | v0.3 | 1/1 | Complete | 2026-03-29 |

---
*Roadmap updated: v0.3 milestone completed 2026-03-29*
