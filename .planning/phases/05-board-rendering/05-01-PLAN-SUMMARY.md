---
phase: 05-board-rendering
plan: "01"
subsystem: ui
tags: [ui, constants, colors, pyqt6, board-rendering]
dependency_graph:
  requires: []
  provides:
    - src/xiangqi/ui/constants.py
  affects:
    - src/xiangqi/ui/board.py
    - src/xiangqi/ui/board_items.py
tech_stack:
  added:
    - PyQt6 UI constants module
  patterns:
    - Centralized UI constants (colors, sizes, font ratios) as module-level constants
    - Ratios for dynamic sizing (CELL_RATIO, PIECE_FONT_RATIO, etc.) derived from cell unit
key_files:
  created:
    - src/xiangqi/ui/__init__.py
    - src/xiangqi/ui/constants.py
decisions: []
metrics:
  duration: "~1 minute"
  completed_date: "2026-03-23"
  tasks_completed: 1
  files_created: 2
  lines_added: 23
---

# Phase 05 Plan 01 Summary: UI Constants

## One-liner

Centralized UI color, size, and font ratio constants for PyQt6 board rendering in `src/xiangqi/ui/constants.py`.

## Objective

Define all UI constants (colors, sizes, font ratios) in `constants.py`. This is the foundation every other module depends on.

## Tasks Completed

| # | Name | Commit | Result |
|---|------|--------|--------|
| 1 | Create `src/xiangqi/ui/constants.py` | `6360c7e` | PASSED |

## Constants Defined

### Colors (9 total)

| Constant | Value | Usage |
|----------|-------|-------|
| `BOARD_BG` | `#7BA05B` | Green felt scene background |
| `GRID_COLOR` | `#2D5A1B` | Dark green grid lines |
| `RED_FILL` | `#CC2200` | Red piece fill |
| `BLACK_FILL` | `#1A1A1A` | Black piece fill |
| `PIECE_TEXT_COLOR` | `#FFFFFF` | White text on pieces |
| `PIECE_STROKE_COLOR` | `#FFFFFF` | White border around pieces |
| `RIVER_TEXT_COLOR` | `#2D5A1B` | "楚河"/"漢界" fill |
| `COORD_TEXT_COLOR` | `#2D5A1B` | Row/col coordinate labels |

### Size Ratios (4 total)

| Constant | Value | Usage |
|----------|-------|-------|
| `CELL_RATIO` | `0.80` | Piece diameter / cell |
| `PIECE_FONT_RATIO` | `0.56` | Piece char font size / cell |
| `RIVER_FONT_RATIO` | `0.28` | River text font / cell |
| `COORD_FONT_RATIO` | `0.22` | Coordinate label font / cell |

### Window Sizes (3 total)

| Constant | Value | Usage |
|----------|-------|-------|
| `DEFAULT_SIZE` | `(480, 600)` | Default window size |
| `MIN_SIZE` | `(360, 450)` | Minimum window size |
| `MAX_SIZE` | `(720, 900)` | Maximum window size |

## Verification

Import test passed:
```
conda run -n xqrl python -c "from src.xiangqi.ui.constants import BOARD_BG, GRID_COLOR, RED_FILL, BLACK_FILL, PIECE_TEXT_COLOR, PIECE_STROKE_COLOR, CELL_RATIO, PIECE_FONT_RATIO, RIVER_FONT_RATIO, COORD_FONT_RATIO, DEFAULT_SIZE, MIN_SIZE, MAX_SIZE; print('constants ok')"
# output: constants ok
```

## Deviations from Plan

None - plan executed exactly as written.

## Auth Gates

None.

## Known Stubs

None.

## Self-Check

- [x] `src/xiangqi/ui/__init__.py` exists
- [x] `src/xiangqi/ui/constants.py` exists
- [x] Commit `6360c7e` exists
- [x] All 9 color constants defined with correct values
- [x] All 4 size/ratio constants defined with correct values
- [x] All 3 window size constants defined with correct values
- [x] Import verification passes

## Commits

| Hash | Message |
|------|---------|
| `6360c7e` | feat(05-01): add ui package and color/size/font ratio constants |
