---
gsd_state_version: 1.0
milestone: v0.1
milestone_name: milestone
status: unknown
stopped_at: Completed 04-02-PLAN.md
last_updated: "2026-03-20T15:30:43.520Z"
progress:
  total_phases: 6
  completed_phases: 5
  total_plans: 10
  completed_plans: 9
  percent: 100
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-19)

**Core value:** 人机对弈时AI能实时学习并持续变强，用户能直观感受到AI棋力随时间提升
**Current focus:** Phase 04 — api-interface

## Runtime Environment

**CRITICAL: Always use conda environment `xqrl`.**

All commands (python, pip, pytest, etc.) must run inside `conda activate xqrl`.
Install missing packages with `pip install` inside that environment.
**pyffish requires stockfish system library first** (brew install stockfish / apt install stockfish), then `pip install pyffish`.

## Current Position

Phase: 04 (api-interface) — PLAN 1 OF 2 COMPLETE
Plan: 2 of 2

## Phase Structure

| # | Phase | Requirements | Status |
|---|-------|-------------|--------|
| 1 | 数据结构 | DATA-01..05 | Complete |
| 2 | 棋子走法与规则校验 | MOVE-01..07, RULE-01..06 | Complete |
| 2.1 | Fix stalemate test | RULE-06 | Complete |
| 2.2 | Tech debt cleanup | — | Complete |
| 3 | 终局判定 | END-01..05 | Complete |
| 4 | API 接口与集成测试 | API-01..04, TEST-01..04 | Plan 1 complete, plan 2 pending |

Progress: [██████████] 100%

## Performance Metrics

**Velocity:**

- Total plans completed: 2
- Average duration: 120s
- Total execution time: 0.067 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-data-structures | 2 | 2 | 120s |

**Recent Trend:**

- Last 5 plans: 01-01 (60s), 01-02 (120s)
- Trend: stable

*Updated after each plan completion*
| Phase 01-data-structures P02 | 120 | 3 tasks | 4 files |
| Phase 02 P02 | 25 | 1 tasks | 3 files |
| Phase 02.1 P01 | 480 | 2 tasks | 1 files |
| Phase 02.2 P01 | 180 | 4 tasks | 4 files |
| Phase 03 P01 | 65 | 7 tasks | 8 files |
| Phase 04 P01 | 523 | 3 tasks | 4 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Init]: 异构智能体架构 — 7 piece-type networks + arbitration network
- [Init]: 从零开始 — no pretrained weights, pure online learning
- [Init]: MPS backend — PyTorch with Apple Silicon optimization
- [Init]: Phase granularity to be user-defined — roadmap deleted, awaiting milestone structure
- [01-02]: XiangqiState includes king_positions dict for Phase 2 fast king lookup
- [Phase 01-02]: XiangqiState includes king_positions dict for Phase 2 fast king lookup (researcher recommendation)
- [02-01]: Board-copy post-check for legal filtering (no incremental unmake)
- [02-01]: Soldier crossing: red crosses at fr <= 4, black crosses at fr >= 5
- [02-01]: Stalemate = loss in Xiangqi (困毙), not draw
- [Phase 02-02]: Used CPW/Fairy-Stockfish perft values (44, 1,920, 79,666, 3,290,240) not the incorrect REQUIREMENTS.md values
- [Phase 02-02]: Fixed elephant home half: red rows 5-9, black rows 0-4 (was inverted causing perft(1) to fail)
- [Phase 02.1]: B_SHI (not B_ADVISOR) is the correct enum; B_ADVISOR was a plan naming error
- [Phase 02.1]: Double-chariot checkmate: B_CHE at (0,4) checks king AND protects B_SHI at (8,4) via same-column geometry
- [Phase 02.1]: R_SHI at (8,3)/(8,5) (not 9,3/9,5) blocks diagonal escapes; R_SHI at row 9 can capture B_SHI at (8,4) diagonally
- [Phase 02.2]: Strict equality (==44) over permissive lower-bound (>=40) for starting position legal move count
- [Phase 02.2]: Per-child CPW assertions catch regressions in individual depth-1 move subtree counts, not just total
- [Phase 03]: Lazy import of repetition.py inside get_game_result() avoids circular dependency
- [Phase 03]: RepetitionState lives in engine.py (Phase 4), not XiangqiState — separation of concerns
- [Phase 03]: Long check -> DRAW; Long chase -> chaser LOSES (per WXO rules)
- [Phase 03]: enemy = -new_state.turn in _detect_chase; piece_color = 1 if piece>0 else -1 for gen_* calls
- [Phase 04]: Engine 持有 XiangqiState，对外统一接口，FEN 在 Engine 类上（from_fen/to_fen）
- [Phase 04]: apply() 委托 legal.apply_move，仅返回 captured int
- [Phase 04]: undo() 增量记录元组，公开 API，空栈抛 IndexError
- [Phase 04]: undo() 同时回退 RepetitionState（apply/undo 共同维护）
- [Phase 04]: RepetitionState 完全封装于 Engine 内部，reset() 时重置
- [Phase 04]: pyffish 不可用则 pytest.skip()，完全独立 test_pyffish.py，仅验证 perft(1) 44步
- [Phase 04]: 非法操作（非法走法/FEN）抛 ValueError，undo 空栈抛 IndexError
- [Phase 04-01]: object.__setattr__(self, '_field', val) pattern for private dataclass fields
- [Phase 04-01]: is_legal_move() now rejects moves where source piece doesn't belong to mover (Rule 1 bug fix)
- [Phase 04-01]: engine.apply() adds ownership validation before delegating to is_legal_move()
- [Phase 04-01]: stalemate test board corrected: B_CHE at (0,4) needed to block red king diagonal escape to (8,4)

### Pending Todos

- Phase 4: API integration and pyffish validation

### Blockers/Concerns

None — Phase 3 complete, Phase 4 context gathered, ready for planning.

## Session Continuity

Last session: 2026-03-20T15:24:47.834Z
Stopped at: Completed 04-02-PLAN.md
Resume file: None
