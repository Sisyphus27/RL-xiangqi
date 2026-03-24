---
phase: 05-board-rendering
plan: 08
subsystem: ui
tags: [bugfix, grid-lines, river-gap]
dependency_graph:
  requires: []
  provides: [complete-horizontal-grid]
  affects: [board-rendering]
tech_stack:
  added: []
  patterns: [PyQt6-QLineF]
key_files:
  created: []
  modified:
    - src/xiangqi/ui/board.py
decisions:
  - Remove incorrect row 4 skip in horizontal line loop
metrics:
  duration_minutes: 1
  completed_date: "2026-03-24T08:37:00Z"
  tasks_completed: 1
  files_modified: 1
---

# Phase 05 Plan 08: Fix Missing Horizontal Grid Line Summary

## One-liner

Fixed horizontal grid line bug by removing incorrect `if row == 4: continue` that was skipping the row 4 line.

## What Was Done

### Task 1: Remove the incorrect row 4 skip in horizontal line loop

**Problem:** The code at lines 146-150 had `if row == 4: continue` which incorrectly skipped drawing the horizontal line at row 4. This caused "Black's pawns missing a row in front" visual bug.

**Root Cause:** Misunderstanding of river gap behavior. In Chinese chess:
- The river is the space between rows 4 and 5
- The horizontal line at row 4 (y = 4.6*cell) is the line row 4 pieces sit ON
- The horizontal line at row 5 (y = 5.6*cell) is the line row 5 pieces sit ON
- Both lines should be drawn
- The "river gap" only affects VERTICAL lines (they break between rows 4 and 5)

**Fix:** Removed the `if row == 4: continue` conditional from the horizontal line loop.

**Before:** 9 horizontal lines (missing row 4 at y = 4.6*cell)
**After:** 10 horizontal lines (complete grid)

**Files modified:** `src/xiangqi/ui/board.py`
**Commit:** 038852e

## Deviations from Plan

None - plan executed exactly as written.

## Test Results

- `grep "if row == 4" src/xiangqi/ui/board.py` returns empty (verified)
- `pytest tests/ui/ -v` - all 28 tests pass

## Verification

- [x] board.py does NOT contain `if row == 4` in the horizontal line loop
- [x] Complete 10-row horizontal grid is rendered
- [x] All 28 automated UI tests pass

## Self-Check: PASSED

- [x] File `src/xiangqi/ui/board.py` exists and was modified
- [x] Commit `038852e` exists in git log
