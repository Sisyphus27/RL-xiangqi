---
gsd_state_version: 1.0
milestone: v0.2
milestone_name: milestone
status: Phase 06 complete, ready for Phase 07
last_updated: "2026-03-25T09:20:00.000Z"
progress:
  total_phases: 1
  completed_phases: 0
  total_plans: 6
  completed_plans: 4
  percent: 100
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-23)

**Core value:** 人机对弈时AI能实时学习并持续变强，用户能直观感受到AI棋力随时间提升
**Current focus:** Phase 07 — AI Interface + Game State

## Runtime Environment

**CRITICAL: Always use conda environment `xqrl`.**

All commands (python, pip, pytest, etc.) must run inside `conda activate xqrl`.
Install missing packages with `pip install` inside that environment.

## Current Position

Phase: 07 (AI Interface + Game State) — READY TO START
Plan: 0 of 0

## Phase Structure

| # | Phase | Requirements | Status |
|---|-------|-------------|--------|
| 05 | Board Rendering | UI-01, UI-02 | Complete |
| 06 | Piece Interaction | UI-03, UI-04, UI-05 | Complete |
| 07 | AI Interface + Game State | AI-01, AI-02, AI-03, AI-04, UI-06, UI-07 | Not started |
| 08 | Game Control | UI-08, UI-09 | Not started |

Progress: [████████████████░░░░] 50% (2/4 phases)

Phase 05 (Board Rendering) — COMPLETE ✓

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [v0.2 Init]: PyQt6 UI — QGraphicsView + QGraphicsScene, click-to-move (not drag)
- [v0.2 Init]: AIPlayer ABC + EngineSnapshot — core AI interface contract
- [v0.2 Init]: RandomAI — black plays random legal move
- [v0.2 Init]: QThread worker (moveToThread) — AI off main thread, "AI 思考中" indicator
- [v0.2 Init]: EngineSnapshot for thread safety — engine reference never crosses thread boundary
- [v0.2 Init]: Generation counter for stale AI result discarding
- [v0.2 Init]: is_legal() guard on every AI-returned move before apply()
- [05-03 Complete]: Phase 05 Board Rendering done — QXiangqiBoard + MainWindow + full test suite ✓
- [Phase 05-board-rendering]: Used QRectF wrapper for fillRect coordinates to accept floating-point values in PyQt6
- [05-06 Complete]: Used QLineF wrapper for drawLine coordinates, completing PyQt6 float-coordinate pattern
- [Phase 05]: Vertical lines bounded at y=9.6*cell matching last horizontal line (row 9)
- [Phase 05-board-rendering]: Palace coordinates use column 3.6*cell (left) and 5.6*cell (right) for center placement
- [Phase 06]: XiangqiEngine.state property added for board fixture contract (06-00)
- [06-01 Complete]: Gold ring: 0.85*cell diameter, z=1.1, 3px pen, 70% opacity; dot: 0.50*cell diameter, z=0.5, 50% opacity
- [06-01 Complete]: Board stores engine reference for legal_moves() queries (not moves passed from outside)
- [06-01 Complete]: QGraphicsView.mapToScene(int,int) returns QPointF (not list); viewport centering offset handled empirically
- [Phase 06]: Use XiangqiEngine.starting() factory method for MainWindow initialization
- [06-04 Complete]: Engine wiring pattern — create engine, then pass engine.state and engine to QXiangqiBoard
- [06-05 Complete]: Use mapToScene(event.position().toPoint()) for accurate viewport-to-scene coordinate conversion
- [06-05 Complete]: Turn-aware piece selection: piece_value * engine.turn > 0 for alternating red/black gameplay

### Pending Todos

- Phase 07: AIPlayer ABC + EngineSnapshot + RandomAI + turn/game-over UI + AI thinking indicator
- Phase 08: New game button + undo (with continuous support)

### Blockers/Concerns

None — roadmap created.
