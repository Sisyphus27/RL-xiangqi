---
phase: 08-game-control
plan: 03
subsystem: game-controller
tags: [undo, bug-fix, board-sync]
dependency_graph:
  requires: []
  provides: []
  affects: [GameController.undo(), QXiangqiBoard.sync_state()]
tech_stack:
  added: []
  patterns: [gap-closure]
key_files:
  created: []
  modified:
    - src/xiangqi/controller/game_controller.py
decisions: []
metrics:
  duration: ~1 minute
  completed: "2026-03-26T02:40:00Z"
---

# Phase 08 Gap Closure Plan 03: Fix Undo Board Sync - Summary

## One-liner

Fixed AttributeError in undo() by replacing non-existent reset_to_state() with correct sync_state() method.

## Bug Fixed

**Issue:** Line 290 in game_controller.py called `self._board.reset_to_state(self._engine.state)` but QXiangqiBoard has no `reset_to_state` method.

**Fix:** Changed to `self._board.sync_state(self._engine.state)` which properly:
1. Updates board's internal `_state` to match engine state
2. Calls `refresh_pieces()` to update visual display

## Verification

- sync_state method exists on QXiangqiBoard: PASS
- Undo completed without AttributeError: PASS
- Board state correctly restored after undo

## Commits

- `a1d5f26`: fix(08-03): replace reset_to_state with sync_state in undo()

## Deviations from Plan

None - plan executed exactly as written.

## Auto-Fixed Issues

None.

## Known Stubs

None.
