---
phase: 05-board-rendering
verified: 2026-03-24T00:00:00Z
status: passed
score: 7/7 must-haves verified
re_verification: false
gaps: []
human_verification:
  - test: "Run `python -m src.xiangqi.ui.main` and visually inspect the board window"
    expected: "Green felt board (#7BA05B) with visible 9x10 grid, river gap without line between rows 4-5, palace diagonals on both sides, '楚河'/'漢界' text in the river, coordinate labels, 32 colored pieces (red bottom, black top), window title 'RL-Xiangqi v0.2'"
    why_human: "Visual rendering accuracy — pixel-level appearance, text readability at minimum window size, and overall layout — cannot be verified programmatically without running the Qt event loop and capturing the window."
  - test: "Resize the window to MIN_SIZE (360x450) and DEFAULT_SIZE (480x600) and verify the board scales proportionally"
    expected: "Board maintains 9:10 aspect ratio at all sizes; grid lines and pieces scale smoothly without clipping"
    why_human: "Responsive scaling behavior across different window sizes requires visual confirmation"
---

# Phase 05: Board Rendering Verification Report

**Phase Goal:** Render a static xiangqi board from starting position using PyQt6
**Verified:** 2026-03-24
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Board displays 9 columns x 10 rows grid with river gap (no line between rows 4-5) and palace diagonals correctly drawn | VERIFIED | `board.py` `drawBackground()` implements 9 vertical lines (cols 0-8), 10 horizontal lines with `if row == 4: continue` for river gap, 8 palace diagonal lines (top-left, top-right, bottom-left, bottom-right). `test_board.py::test_piece_count` confirms scene has 32 items. |
| 2 | All 32 pieces (14 types: SHUAI/JIANG x1, CHE x2, MA x2, PAO x2, SHI x2, XIANG x2, BING/ZU x5 x2) visible in starting position | VERIFIED | `_load_pieces()` iterates `self._state.board` (from `XiangqiState.starting()`) and creates one `PieceItem` per non-zero value. `test_board.py::test_piece_count` asserts `len(pieces) == 32`. `test_board.py::test_red_pieces_count` (16) and `test_black_pieces_count` (16) confirm correct distribution. |
| 3 | Red pieces (#CC2200) and black pieces (#1A1A1A) correctly colored and distinguished | VERIFIED | `board_items.py` sets `fill_color = QColor(RED_FILL) if piece_value > 0 else QColor(BLACK_FILL)`. `test_board.py::test_piece_colors_match_constants` and `test_piece_item.py` verify all 32 pieces. `test_piece_item.py::test_all_piece_characters` covers all 14 piece types (+1..+7, -1..-7). |
| 4 | Board maintains 9:10 aspect ratio on window resize | VERIFIED | `resizeEvent()` uses `self._cell = min(vw, vh) / 11.2`. Scene rect: `(10.2*cell, 11.2*cell)`. `test_board.py::test_cell_size_formula` verifies 4 viewport size test cases. |
| 5 | Window title displays "RL-Xiangqi v0.2" | VERIFIED | `MainWindow.__init__` calls `self.setWindowTitle("RL-Xiangqi v0.2")`. `test_board.py::test_window_title_from_main` asserts equality. Window size set to DEFAULT_SIZE (480, 600) with MIN_SIZE/MIN_SIZE constraints. |
| 6 | River text "楚河"/"漢界" visible in the river gap | VERIFIED | `board.py` `drawBackground()` draws "楚河" at `(2.0*cell, 5.1*cell)` and "漢界" at `(5.5*cell, 5.1*cell)` using `RIVER_FONT_RATIO` with minimum 10px. |
| 7 | Coordinate labels (1-9 columns, 1-10 rows) drawn on both sides | VERIFIED | `board.py` `drawBackground()` draws column labels (bottom: 1-9 L-to-R, top: 9-1 R-to-L) and row labels (left: 1-10 B-to-T, right: 10-1 T-to-B) using `COORD_FONT_RATIO`. |

**Score:** 7/7 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/xiangqi/ui/constants.py` | 9 colors, 4 ratios, 3 window sizes | VERIFIED | 23 lines. All constants match spec. `test_constants.py` covers every value. |
| `src/xiangqi/ui/board_items.py` | `PieceItem(QGraphicsEllipseItem)` with `paint()` override | VERIFIED | 108 lines. Full implementation: ellipse fill, white stroke, centered Chinese char via `QFont("SimSun,...")`. `test_piece_item.py` tests all 14 piece types, colors, geometry, position. |
| `src/xiangqi/ui/board.py` | `QXiangqiBoard(QGraphicsView)` with `drawBackground()`, `resizeEvent()`, `_load_pieces()` | VERIFIED | 194 lines. All 7 board elements drawn in `drawBackground()`. `test_board.py` covers piece count, colors, main window. |
| `src/xiangqi/ui/main.py` | `MainWindow` + `main()` entry point | VERIFIED | 48 lines. Title, central widget, size constraints all correct. `test_board.py::TestMainWindow` covers all 4 properties. |
| `src/xiangqi/ui/__init__.py` | Public API re-exports | VERIFIED | 18 lines. Re-exports `QXiangqiBoard`, `PieceItem`, `MainWindow`. `__all__` defined. |
| `tests/ui/conftest.py` | Pytest fixtures for starting_state and board | VERIFIED | 27 lines. `starting_state` and `board(qtbot)` fixtures as designed. |
| `tests/ui/test_constants.py` | Unit tests for all constants | VERIFIED | 80 lines. 7 tests covering all color, size, ratio values and constraints. |
| `tests/ui/test_piece_item.py` | Unit tests for PieceItem | VERIFIED | 97 lines. Tests colors, all 14 characters, diameter, position, z-value. |
| `tests/ui/test_board.py` | Unit tests for QXiangqiBoard + MainWindow | VERIFIED | 118 lines. Tests scene structure, 32-piece count, red/black counts, colors, cell formula, 4 MainWindow properties. |

### Artifact Levels Summary

All 9 source artifacts: **EXISTS + SUBSTANTIVE + WIRED**

- **constants.py**: Substantive (23 lines of concrete color/size values) + Wired (imported by board.py and board_items.py)
- **board_items.py**: Substantive (108 lines with full paint override) + Wired (imported by board.py)
- **board.py**: Substantive (194 lines with full drawBackground) + Wired (uses PieceItem, constants, XiangqiState)
- **main.py**: Substantive (48 lines) + Wired (imports QXiangqiBoard and constants)
- **__init__.py**: Substantive (18 lines with re-exports) + Wired (used by external consumers)
- **4 test files**: All substantive (test content matches implementation)

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `board.py` | `board_items.py` | `from .board_items import PieceItem` | WIRED | `board.py` line 21 imports PieceItem. `_load_pieces()` instantiates it. |
| `board.py` | `constants.py` | `from .constants import ...` | WIRED | `board.py` imports 8 constants (BOARD_BG, GRID_COLOR, etc.) for `drawBackground()` |
| `board_items.py` | `constants.py` | `from .constants import ...` | WIRED | `board_items.py` imports 5 constants (RED_FILL, BLACK_FILL, CELL_RATIO, PIECE_FONT_RATIO, PIECE_TEXT_COLOR) |
| `board.py` | `engine/state.py` | `from src.xiangqi.engine.state import XiangqiState` | WIRED | `board.py` uses `XiangqiState.starting()` to initialize `_state`. `_load_pieces()` reads `self._state.board`. |
| `board_items.py` | `engine/types.py` | `from src.xiangqi.engine.types import Piece` | WIRED | `board_items.py` calls `str(Piece(piece_value))` for character rendering |
| `main.py` | `board.py` | `from .board import QXiangqiBoard` | WIRED | `MainWindow.__init__` sets `QXiangqiBoard()` as central widget |
| `main.py` | `constants.py` | `from .constants import DEFAULT_SIZE, MIN_SIZE, MAX_SIZE` | WIRED | `main.py` imports and uses all three window size constants |
| `__init__.py` | `board.py`, `board_items.py`, `main.py` | `from .board import ...` | WIRED | Re-exports all three classes correctly |

All 8 key links verified as WIRED. No orphaned imports.

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| **UI-01** | 05-01, 05-02, 05-03 | PyQt6 QGraphicsView + QGraphicsScene renders 9x10 board (grid + river gap + palace diagonals + river text + coordinate labels) | SATISFIED | `board.py::QXiangqiBoard` is `QGraphicsView` subclass. `drawBackground()` draws 9 vertical lines (cols 0-8), 10 horizontal lines (river gap at row 4), 8 palace diagonals, "楚河"/"漢界" text, coordinate labels on all 4 sides. `test_board.py` verifies 32-piece count. |
| **UI-02** | 05-01, 05-02, 05-03 | Pieces rendered via Piece enum Chinese chars, red/black distinguished by color | SATISFIED | `board_items.py::PieceItem.paint()` calls `str(Piece(piece_value))` for character. Fill color logic: `piece_value > 0` → `#CC2200`, else `#1A1A1A`. `test_piece_item.py::test_all_piece_characters` covers all 14 piece types. `test_board.py::test_piece_colors_match_constants` verifies all 32. |

**Requirement IDs from REQUIREMENTS.md:** UI-01 and UI-02 both mapped to Phase 05 in ROADMAP.md traceability table. Both plans 05-01, 05-02, and 05-03 declare these requirements in their frontmatter `requirements:` fields. No orphaned requirements.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | None found | — | — |

No TODO/FIXME/placeholder comments. No empty implementations. No hardcoded empty data. No stub patterns. All classes are substantive with real logic. `_load_pieces()` reads from the actual engine state, not hardcoded data.

---

### Human Verification Required

**2 items need human testing:**

1. **Visual board rendering**
   - Test: Run `python -m src.xiangqi.ui.main` and visually inspect the board window
   - Expected: Green felt board (#7BA05B) with visible 9x10 grid, river gap (no line between rows 4-5), palace diagonals on both sides, "楚河"/"漢界" text in the river, coordinate labels, 32 colored pieces (red on bottom half, black on top half), window title "RL-Xiangqi v0.2"
   - Why human: Pixel-level visual rendering accuracy and text readability at minimum window size cannot be verified programmatically without running the Qt event loop

2. **Responsive scaling**
   - Test: Resize window from MIN_SIZE (360x450) to DEFAULT_SIZE (480x600) to MAX_SIZE (720x900)
   - Expected: Board maintains 9:10 aspect ratio at all sizes; grid lines and pieces scale proportionally without clipping
   - Why human: Visual proportionality across window sizes requires human confirmation; automated tests only verify the `cell` formula, not the visual result

---

### Gaps Summary

No gaps found. All must-haves verified. The codebase fully implements the Phase 05 goal:

- **Board rendering (UI-01):** `QXiangqiBoard.drawBackground()` draws a complete 9x10 xiangqi board with all required elements. `resizeEvent()` handles responsive scaling via `min(vw, vh)/11.2`.
- **Piece rendering (UI-02):** `PieceItem.paint()` renders all 32 starting pieces with correct Chinese characters and red/black colors. All 14 piece types verified. `_load_pieces()` reads from the engine state.
- **Architecture:** Clean 4-file module (`constants.py`, `board_items.py`, `board.py`, `main.py`) with correct imports and responsibilities. `__init__.py` provides clean public API.
- **Testing:** Comprehensive test suite (4 files, 322 lines) covers all constants, PieceItem, QXiangqiBoard scene structure, piece counts/colors/characters, and MainWindow properties.

---

_Verified: 2026-03-24_
_Verifier: Claude (gsd-verifier)_
