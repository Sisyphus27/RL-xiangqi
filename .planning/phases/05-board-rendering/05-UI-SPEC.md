---
status: draft
phase: 05
phase_name: Board Rendering
tool: none
shadcn: false
upstream:
  - source: 05-CONTEXT.md
    decisions_used: 15
  - source: REQUIREMENTS.md
    decisions_used: 2
  - source: ROADMAP.md
    decisions_used: 5
  - source: STATE.md
    decisions_used: 2
---

# UI-SPEC.md — Phase 05: Board Rendering

**Created:** 2026-03-23
**Status:** draft
**Tech:** PyQt6 (QGraphicsView + QGraphicsScene)
**Tool:** none (Python/Qt — shadcn not applicable)

---

## Visual Contract

### Colors

| Role | Value | Usage |
|------|-------|-------|
| Board background | `#7BA05B` | Scene background (green felt) |
| Grid lines | `#2D5A1B` | Vertical/horizontal grid lines |
| River text | `#2D5A1B` | "楚河" / "漢界" fill |
| Red piece fill | `#CC2200` | All red pieces |
| Red piece text | `#FFFFFF` | Character on red pieces |
| Black piece fill | `#1A1A1A` | All black pieces |
| Black piece text | `#FFFFFF` | Character on black pieces |
| Piece stroke | `#FFFFFF` | White border around all pieces |
| Coordinate text | `#2D5A1B` | Row/column labels |

**No accent color reserved for this phase.** Accent (e.g., selection highlight) is deferred to Phase 06.

### Typography

| Element | Font | Size | Weight | Color |
|---------|------|------|--------|-------|
| Piece character | SimSun / 宋体 | derived (cell * 0.56) | normal | white on fill |
| River text ("楚河"/"漢界") | SimSun / 宋体 | derived (cell * 0.28) | normal | `#2D5A1B` |
| Coordinate labels | SimSun / 宋体 | derived (cell * 0.22) | normal | `#2D5A1B` |
| Window title | OS default | OS default | OS default | OS default |

**No more than 2 font sizes in code** — all derived from single `cell_size` variable.

### Spacing

| Concept | Value | Notes |
|---------|-------|-------|
| Cell unit | `cell = min(width, height) / max(COLS, ROWS)` | Derived at runtime |
| Grid inset (each side) | `cell * 0.6` | Creates outer margin |
| Piece diameter | `cell * 0.80` | D-12: 80% of cell width |
| Grid line width | `1px` | Qt default |
| River gap | Rows 4–5 (0-indexed): no horizontal line | D-03 |
| Palace diagonal gap | Rows 0–2 and 7–9: diagonals drawn | D-06 |

### Window

| Property | Value |
|----------|-------|
| Default size | 480 x 600 px |
| Minimum size | 360 x 450 px |
| Maximum size | 720 x 900 px |
| Title | `RL-Xiangqi v0.2` |
| Resize behavior | Aspect ratio 9:10 locked; board scales with `cell` derived from min dimension |

---

## Layout

### Scene Coordinate System (9 cols x 10 rows)

```
Scene size: (COLS + 1.2) * cell  wide  x  (ROWS + 1.2) * cell  tall
            = 10.2 * cell         wide  x  11.2 * cell         tall

Grid lines drawn from (0.6*cell, 0.6*cell) to (9.6*cell, 10.6*cell)

Engine row 0 = top of screen (black home rank)
Engine row 9 = bottom of screen (red home rank)
Engine col 0 = left side (black's left)
```

### Grid Lines Drawing Order

1. Vertical lines: 9 lines at x = 0.6, 1.6, 2.6, ..., 8.6 cell
2. Horizontal lines: 10 lines at y = 0.6, 1.6, ..., 9.6 cell
3. River break: skip horizontal line between row 4 and row 5 (y = 4.6 cell)
4. Palace diagonals: lines from (0,0)–(2,2) and (6,0)–(8,2) on each side; same for bottom palace
5. River text: centered in row 4.5 gap area, left half "楚河", right half "漢界"

### Coordinate Labels

| Side | Rows | Cols |
|------|------|------|
| Red perspective | row 10 → 1 (bottom-to-top), col 1 → 9 (left-to-right) | — |
| Black perspective | row 1 → 10 (top-to-bottom), col 9 → 1 (right-to-left) | — |
| Red labels | y > bottom grid line | x outside left edge |
| Black labels | y < top grid line | x outside right edge |

### Piece Placement

- Use `XiangqiState.starting()` to get initial board (32 pieces)
- Red pieces: `piece.value > 0` — draw with red fill `#CC2200`, white text
- Black pieces: `piece.value < 0` — draw with black fill `#1A1A1A`, white text
- `str(Piece)` returns the Chinese character (e.g., `"帅"`, `"將"`)
- Piece center aligned to grid intersection at `(col + 0.6, row + 0.6) * cell`
- Each piece rendered as `QGraphicsEllipseItem` (fill + stroke) + `QGraphicsSimpleTextItem` (character overlay)

---

## Components

### QXiangqiBoard (QGraphicsView)

**States:** Read-only in Phase 05 (no interaction)
**Children:** QGraphicsScene containing board + pieces

### BoardPainter (QGraphicsScene background)

Draws in `drawBackground` or via dedicated `QGraphicsItem`:
- Green felt rectangle (`#7BA05B`)
- 9 vertical lines
- 10 horizontal lines with river gap
- 4 palace diagonals
- River text "楚河" left / "漢界" right
- Coordinate labels (both perspectives)

### PieceItem (QGraphicsItem group per piece)

- `QGraphicsEllipseItem`: diameter = `cell * 0.80`, centered, filled, white stroke 2px
- `QGraphicsSimpleTextItem`: Chinese character centered, font size `cell * 0.56`, white

**States:**
| State | Appearance |
|-------|-----------|
| Normal | Red or black fill with white text |
| (no selection/hover in Phase 05) | N/A for this phase |

### Window

- `QMainWindow` subclass `MainWindow`
- `setWindowTitle("RL-Xiangqi v0.2")`
- `QGraphicsView` fills the central widget
- Aspect ratio enforcement via `resizeEvent` clamping

---

## Interaction Contract

**Phase 05 is read-only.** No user interaction with pieces or board.
- View is non-interactive: `setInteractive(False)` or click events ignored
- Window resize: board redraws with correct proportions

---

## Copywriting

| Element | Text |
|---------|------|
| Window title | `RL-Xiangqi v0.2` |
| Piece chars | Source: `str(Piece)` from `src/xiangqi/engine/types.py` |
| River left | `楚河` |
| River right | `漢界` |
| No empty state (always starts with 32 pieces) | — |
| No error state in this phase | — |

---

## Architecture

```
src/xiangqi/ui/
  __init__.py
  board.py          # QXiangqiBoard (QGraphicsView)
  board_items.py    # PieceItem, BoardBackgroundItem
  constants.py      # UI color/size constants (D-01, D-04, D-12–D-16, D-28–D-31)
  main.py           # main() — QApplication + MainWindow

src/xiangqi/ui/constants.py
  BOARD_BG = "#7BA05B"
  GRID_COLOR = "#2D5A1B"
  RED_FILL = "#CC2200"
  BLACK_FILL = "#1A1A1A"
  PIECE_TEXT_COLOR = "#FFFFFF"
  PIECE_STROKE_COLOR = "#FFFFFF"
  CELL_RATIO = 0.80        # piece diameter / cell
  PIECE_FONT_RATIO = 0.56  # font size / cell
  RIVER_FONT_RATIO = 0.28
  COORD_FONT_RATIO = 0.22
  DEFAULT_SIZE = (480, 600)
  MIN_SIZE = (360, 450)
  MAX_SIZE = (720, 900)
```

---

## Deferred Ideas (Not in This Phase)

| Idea | Deferred To |
|------|-------------|
| Board outer border margin | Phase 08+ |
| Check visual highlight | Phase 08+ |
| Captured pieces tray | v0.2+ |
| Sound effects | v0.3 |
| Timer system | v0.3 |
| Drag-to-move | Out of scope (click-to-move only) |

---

## Success Criteria Mapping

| # | Criterion | Implementation |
|---|-----------|----------------|
| SC-1 | 9x10 grid, river gap, palace diagonals | `BoardBackgroundItem.drawBackground` |
| SC-2 | 32 pieces in starting position | `XiangqiState.starting()` + loop over board |
| SC-3 | Red pieces red, black pieces black | Color from piece sign; `str(Piece)` char |
| SC-4 | Aspect ratio preserved on resize | `resizeEvent` recalculates `cell` |
| SC-5 | Window title "RL-Xiangqi v0.2" | `setWindowTitle()` in `MainWindow.__init__` |

---

*UI-SPEC generated: 2026-03-23*
*Status: draft — awaiting gsd-ui-checker approval*
