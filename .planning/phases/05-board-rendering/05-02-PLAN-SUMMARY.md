---
phase: 05-board-rendering
plan: 02
subsystem: ui
tags: [piece-rendering, pyqt6, qgraphicsellipseitem, chinese-font]
dependency_graph:
  requires: []
  provides:
    - src/xiangqi/ui/board_items.py::PieceItem
  affects:
    - src/xiangqi/ui/board.py
tech_stack:
  added: [PyQt6, QGraphicsEllipseItem]
  patterns: [QGraphicsItem paint override, QFont with StyleStrategy.PreferMatch]
key_files:
  created:
    - src/xiangqi/ui/board_items.py
  modified: []
decisions: []
metrics:
  duration_seconds: 148
  completed_date: "2026-03-23T15:22:13Z"
  tasks_completed: 1
  files_created: 1
  lines_added: 107
---

# Phase 05 Plan 02: PieceItem — Single Piece Renderer Summary

**One-liner:** PieceItem (QGraphicsEllipseItem subclass) renders filled circle + white stroke + centered Chinese character per piece.

## Objective

Implement `PieceItem(QGraphicsEllipseItem)` — the per-piece rendering primitive for the xiangqi board. Each piece is a filled circle with a white stroke border and a centered Chinese character.

## Completed Tasks

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | Create src/xiangqi/ui/board_items.py with PieceItem class | 3d60ca3 | src/xiangqi/ui/board_items.py |

## What Was Built

### PieceItem (QGraphicsEllipseItem)

A Qt graphics item that renders a single xiangqi piece:

- **Ellipse:** diameter = `cell * CELL_RATIO` (0.80), local rect `(0, 0, d, d)`
- **Scene position:** `(col + 0.2) * cell` x `(row + 0.2) * cell` — centers piece at `(col + 0.6, row + 0.6) * cell`
- **Fill color:** `#CC2200` (red) for `piece_value > 0`, `#1A1A1A` (black) for `piece_value < 0`
- **Stroke:** white `QPen`, 2.0px width
- **Character:** `str(Piece(piece_value))` — draws Chinese char centered in ellipse using `QFont("SimSun, Microsoft YaHei, Arial")`, size `cell * 0.56` (min 8px)
- **Z-value:** 1.0 (above board background)
- **Validation:** raises `ValueError` on `piece_value=0` (empty square guard)

### Key Implementation Details

- `__slots__` used for memory efficiency on QGraphicsItem subclasses
- Font uses `QFont.StyleStrategy.PreferMatch` for best available CJK font fallback
- `paint()` calls `QGraphicsEllipseItem.paint()` first (draws ellipse), then overlays text
- All coordinate math verified against 05-RESEARCH.md scene coordinate system

## Verification Results

All automated tests passed:

```
from src.xiangqi.ui.board_items import PieceItem
from src.xiangqi.engine.types import Piece

# Red SHUAI: correct char, correct fill, correct position
piece = PieceItem(row=9, col=4, piece_value=1, cell=50.0)
assert piece._char == '帅'
assert piece.brush().color().name().upper() == '#CC2200'
assert abs(piece.x() - (4 + 0.2) * 50.0) < 0.001
assert abs(piece.y() - (9 + 0.2) * 50.0) < 0.001

# Black JIANG: correct char, correct fill
piece2 = PieceItem(row=0, col=4, piece_value=-1, cell=50.0)
assert piece2._char == '将'
assert piece2.brush().color().name().upper() == '#1A1A1A'

# All 14 piece types produce correct characters
all_values = [1, 2, 3, 4, 5, 6, 7, -1, -2, -3, -4, -5, -6, -7]
for val in all_values:
    p = PieceItem(row=5, col=4, piece_value=val, cell=40.0)
    assert p._char == str(Piece(val))

# White stroke: 2px
assert piece.pen().color().name().upper() == '#FFFFFF'
assert piece.pen().widthF() == 2.0

# Empty piece raises ValueError
PieceItem(row=0, col=0, piece_value=0, cell=50.0)  # raises ValueError
```

## Deviations from Plan

**Rule 3 (Auto-fix blocking issue):** `board_items.py` imports from `.constants`, but `constants.py` was not created in this plan. Discovered it was already committed by plan 05-01 agent. No action needed.

**Rule 1 (Auto-fix bug):** Plan specified `from src.xiangqi.engine.types import Piece, ROWS, COLS` but `ROWS` and `COLS` are defined in `src/xiangqi/engine/constants.py`, not `types.py`. Fixed import to use correct module.

## Dependencies

- `src.xiangqi.engine.types.Piece` — Chinese character mapping
- `src.xiangqi.engine.constants.ROWS, COLS` — board dimensions
- `src.xiangqi.ui.constants` — color and ratio constants (committed by 05-01 agent)
- PyQt6 — Qt6 bindings (installed in xqrl env as missing dependency)

## Next Steps

Plan 05-02 provides the `PieceItem` class. Plan 05-03 will render the board background (grid lines, river, palace diagonals) and integrate `PieceItem` instances into the scene.

## Self-Check

- [x] `src/xiangqi/ui/board_items.py` exists with `class PieceItem`
- [x] `from src.xiangqi.ui.board_items import PieceItem` succeeds
- [x] PieceItem with piece_value=+1 renders red (#CC2200)
- [x] PieceItem with piece_value=-1 renders black (#1A1A1A)
- [x] `str(PieceItem(...)._char)` matches `str(Piece(value))` for all 14 piece types
- [x] Piece ellipse diameter = `cell * 0.80`
- [x] White 2px stroke on all pieces
- [x] Chinese character centered in ellipse
- [x] Task committed with hash `3d60ca3`
- [x] SUMMARY.md created

## Self-Check: PASSED
