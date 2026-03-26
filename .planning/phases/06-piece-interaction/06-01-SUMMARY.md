# Phase 06 Plan 01: Piece Selection Infrastructure Summary

**Plan:** 06-01
**Phase:** 06-piece-interaction
**Status:** COMPLETE
**Date:** 2026-03-25

## One-liner

Gold selection ring and legal move dot highlighting infrastructure added to QXiangqiBoard with engine-backed legal move queries.

## What Was Built

Selection and legal move highlight infrastructure for QXiangqiBoard:
- `HIGHLIGHT_COLOR = "#FFD700"` constant in `constants.py`
- Engine-backed selection system with `_engine`, `_selected`, `_selection_ring`, `_highlight_items`, `_piece_index`
- `_create_selection_ring(row, col)` - gold ring (0.85*cell, z=1.1, 3px, 70% opacity)
- `_create_legal_move_dot(row, col)` - gold dot (0.50*cell, z=0.5, 50% opacity)
- `_clear_highlights()` - removes all highlight items from scene
- `_select_piece(row, col)` - creates ring + legal move dots
- `_show_legal_moves(row, col)` - queries engine.legal_moves() and creates dots
- `_deselect_piece()` - clears highlights and selection
- `_piece_index` dict built during `_load_pieces` for O(1) piece lookup
- `move_applied = pyqtSignal(int, int, int)` signal for move notification
- Full click-to-move flow: `_handle_board_click`, `_is_legal_target`, `_execute_move`, `apply_move`
- Fixed PyQt6 `mapToScene(int, int)` coordinate conversion in `mousePressEvent`

## Must-Haves Verification

| Must-Have | Status |
|-----------|--------|
| Clicking red piece shows gold ring around it | IMPLEMENTED |
| Clicking red piece shows gold dots at legal move targets | IMPLEMENTED |
| Highlights clear when different red piece selected or cancelled | IMPLEMENTED |
| Piece index dictionary tracks all piece positions for fast lookup | IMPLEMENTED |
| HIGHLIGHT_COLOR constant in constants.py | IMPLEMENTED |
| board.py has _engine, _selected, _selection_ring, _highlight_items, _piece_index | IMPLEMENTED |

## Key Decisions Made

| Decision | Rationale |
|----------|-----------|
| Gold #FFD700 selection ring | Matches traditional Chinese chess highlight convention |
| Ring: 0.85*cell diameter, z=1.1, 3px pen, 70% opacity | Above pieces, visible but not occluding |
| Dot: 0.50*cell diameter, z=0.5, 50% opacity | Below pieces, subtle but visible |
| _piece_index built during _load_pieces | O(1) lookup, consistent with resizeEvent rebuild pattern |
| Board stores engine reference (not moves passed from outside) | Per checker feedback clarification |

## Deviations from Plan

**1. [Rule 3 - Blocking] Fixed PyQt6 mapToScene API usage**
- Found during: Click simulation tests
- Issue: `mapToScene(QPoint)` returned wrong type; `mapToScene(int,int)` returns `QPointF` directly (not list)
- Fix: Changed to `mapToScene(int(vp_x), int(vp_y))` returning `QPointF` directly
- Files modified: `src/xiangqi/ui/board.py`
- Commit: 7044e00

**2. [Rule 1 - Bug] Fixed Qt BrushStyle/PenStyle usage**
- Found during: Test execution
- Issue: `setBrush(Qt.BrushStyle.NoBrush)` and `setPen(Qt.PenStyle.NoPen)` raise TypeError in PyQt6
- Fix: Removed `setBrush(NoBrush)` from ring (default is no brush); removed `setPen(NoPen)` from dot
- Files modified: `src/xiangqi/ui/board.py`
- Commit: 7044e00

**3. [Rule 3 - Blocking] Fixed test helper viewport coordinate mapping**
- Found during: `test_board_interaction_task2.py` test failures
- Issue: `_click` helper passed scene coords as `localPos` but Qt expects viewport coords; viewport size varies by platform
- Fix: Compute viewport center offset based on actual viewport dimensions; use `QPointF(vp_x, vp_y)` for localPos
- Files modified: `tests/ui/test_board_interaction_task2.py`
- Commit: 7044e00

**4. [Rule 1 - Bug] Fixed test assertion for red chariot position**
- Found during: Test execution
- Issue: Test asserted piece at (6,4) was red chariot (+5), but it's red soldier (+7)
- Fix: Changed to lookup at (9, 0) where red chariot actually starts
- Files modified: `tests/ui/test_board_interaction.py`
- Commit: 7044e00

## Commits

| Hash | Type | Message |
|------|------|---------|
| e7f877c | test | test(06-01): add failing test for HIGHLIGHT_COLOR constant |
| b4caa9e | test | test(06-01): add failing tests for board interaction infrastructure |
| 7044e00 | feat | feat(06-01): add piece selection and legal move highlight infrastructure |

## Metrics

- **Duration:** 2026-03-25T02:38:24Z to 2026-03-25T~02:52:00Z (~14 minutes)
- **Tasks Completed:** 3/3
- **Files Modified:** 5 (constants.py, board.py, test_board.py, test_board_interaction.py, test_board_interaction_task2.py)
- **Tests Added:** 25 (06-01 infrastructure) + 1 (HIGHLIGHT_COLOR)
- **Tests Total Passing:** 97 (full UI suite)

## Self-Check: PASSED

- [x] constants.py has HIGHLIGHT_COLOR = "#FFD700" - FOUND
- [x] board.py has __init__ with engine parameter - FOUND
- [x] board.py has _selected, _selection_ring, _highlight_items, _piece_index, _engine - FOUND
- [x] board.py has _create_selection_ring (0.85*cell, z=1.1, 3px, 70% opacity) - FOUND
- [x] board.py has _create_legal_move_dot (0.50*cell, z=0.5, 50% opacity) - FOUND
- [x] board.py has _clear_highlights - FOUND
- [x] board.py has _select_piece, _show_legal_moves, _deselect_piece - FOUND
- [x] _load_pieces populates _piece_index - FOUND
- [x] _show_legal_moves uses self._engine.legal_moves() - FOUND
- [x] All commits found in git log
