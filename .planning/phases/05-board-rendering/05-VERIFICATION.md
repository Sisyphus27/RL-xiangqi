---
phase: 05-board-rendering
verified: 2026-03-24T09:30:00Z
status: passed
score: 7/7 must-haves verified
re_verification:
  previous_status: passed
  previous_score: 7/7
  gaps_closed:
    - "PyQt6 QPalette API compatibility error fixed (QPalette.NoRole -> QPalette.ColorRole.NoRole)"
    - "Application launches successfully without AttributeError"
    - "All 28 UI tests passing after gap closure"
  gaps_remaining: []
  regressions: []
gaps: []
human_verification:
  - test: "Run `python -m src.xiangqi.ui.main` and visually inspect the board window"
    expected: "Green felt board (#7BA05B) with visible 9x10 grid, river gap without line between rows 4-5, palace diagonals on both sides, '楚河'/'漢界' text in the river, coordinate labels, 32 colored pieces (red bottom, black top), window title 'RL-Xiangqi v0.2'"
    why_human: "Visual rendering accuracy — pixel-level appearance, text readability at minimum window size, and overall layout — cannot be verified programmatically without running the Qt event loop and capturing the window."
  - test: "Resize the window to MIN_SIZE (360x450) and DEFAULT_SIZE (480x600) and verify the board scales proportionally"
    expected: "Board maintains 9:10 aspect ratio at all sizes; grid lines and pieces scale smoothly without clipping"
    why_human: "Responsive scaling behavior across different window sizes requires visual confirmation"
---

# Phase 05: Board Rendering Re-Verification Report

**Phase Goal:** Render a static xiangqi board from starting position using PyQt6
**Verified:** 2026-03-24T09:30:00Z
**Status:** passed
**Re-verification:** Yes — after gap closure (05-04)

---

## Re-Verification Summary

This is a **re-verification** after gap closure plan 05-04 fixed a PyQt6 API compatibility error that blocked application launch.

**Previous verification:** 2026-03-24T00:00:00Z (status: passed)
**Gap closure:** 2026-03-24T09:27:00Z (05-04-SUMMARY.md)
**Current verification:** 2026-03-24T09:30:00Z

**Gaps Closed:**
1. **PyQt6 API Fix:** Changed `QPalette.NoRole` to `QPalette.ColorRole.NoRole` in board.py line 71
2. **Application Launch:** Application now launches successfully without AttributeError
3. **Test Suite:** All 28 UI tests passing (previously 28 passed but app wouldn't launch)

**Result:** All must-haves verified. Phase 05 goal fully achieved.

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Board displays 9 columns x 10 rows grid with river gap (no line between rows 4-5) and palace diagonals correctly drawn | VERIFIED | `board.py` lines 140-162: 9 vertical lines (cols 0-8), 10 horizontal lines with `if row == 4: continue` for river gap, 8 palace diagonal lines. `test_board.py::test_piece_count` confirms scene has 32 items. All 28 tests pass. |
| 2 | All 32 pieces (14 types: SHUAI/JIANG x1, CHE x2, MA x2, PAO x2, SHI x2, XIANG x2, BING/ZU x5 x2) visible in starting position | VERIFIED | `_load_pieces()` lines 105-114 iterates `self._state.board` (from `XiangqiState.starting()`) and creates one `PieceItem` per non-zero value. `test_board.py::test_piece_count` asserts `len(pieces) == 32`. `test_red_pieces_count` (16) and `test_black_pieces_count` (16) confirm distribution. |
| 3 | Red pieces (#CC2200) and black pieces (#1A1A1A) correctly colored and distinguished | VERIFIED | `board_items.py` line 72: `fill_color = QColor(RED_FILL) if piece_value > 0 else QColor(BLACK_FILL)`. `test_board.py::test_piece_colors_match_constants` and `test_piece_item.py` verify all 32 pieces. `test_piece_item.py::test_all_piece_characters` covers all 14 piece types (+1..+7, -1..-7). |
| 4 | Board maintains 9:10 aspect ratio on window resize | VERIFIED | `resizeEvent()` line 91: `self._cell = min(vw, vh) / 11.2`. Scene rect: `(10.2*cell, 11.2*cell)`. `test_board.py::test_cell_size_formula` verifies 4 viewport size test cases. Test passes. |
| 5 | Window title displays "RL-Xiangqi v0.2" | VERIFIED | `main.py` line 30: `self.setWindowTitle("RL-Xiangqi v0.2")`. `test_board.py::test_window_title_from_main` asserts equality. Window size set to DEFAULT_SIZE (480, 600) with MIN_SIZE/MAX_SIZE constraints. |
| 6 | River text "楚河"/"漢界" visible in the river gap | VERIFIED | `board.py` lines 165-171: draws "楚河" at `(2.0*cell, 5.1*cell)` and "漢界" at `(5.5*cell, 5.1*cell)` using `RIVER_FONT_RATIO` with minimum 10px. |
| 7 | Coordinate labels (1-9 columns, 1-10 rows) drawn on both sides | VERIFIED | `board.py` lines 173-193: draws column labels (bottom: 1-9 L-to-R, top: 9-1 R-to-L) and row labels (left: 1-10 B-to-T, right: 10-1 T-to-B) using `COORD_FONT_RATIO`. |

**Score:** 7/7 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/xiangqi/ui/constants.py` | 9 colors, 4 ratios, 3 window sizes | VERIFIED | 23 lines. All constants match spec: BOARD_BG="#7BA05B", GRID_COLOR="#2D5A1B", RED_FILL="#CC2200", BLACK_FILL="#1A1A1A", PIECE_TEXT_COLOR="#FFFFFF", PIECE_STROKE_COLOR="#FFFFFF", RIVER_TEXT_COLOR="#2D5A1B", COORD_TEXT_COLOR="#2D5A1B", CELL_RATIO=0.80, PIECE_FONT_RATIO=0.56, RIVER_FONT_RATIO=0.28, COORD_FONT_RATIO=0.22, DEFAULT_SIZE=(480,600), MIN_SIZE=(360,450), MAX_SIZE=(720,900). `test_constants.py` (6 tests) covers every value. |
| `src/xiangqi/ui/board_items.py` | `PieceItem(QGraphicsEllipseItem)` with `paint()` override | VERIFIED | 108 lines. Full implementation: ellipse fill (line 72), white stroke (line 76), centered Chinese char via `QFont("SimSun,...")` (lines 100-107). `test_piece_item.py` (11 tests) tests all 14 piece types, colors, geometry, position. |
| `src/xiangqi/ui/board.py` | `QXiangqiBoard(QGraphicsView)` with `drawBackground()`, `resizeEvent()`, `_load_pieces()` | VERIFIED | 194 lines. All 7 board elements drawn in `drawBackground()` (lines 118-193). PyQt6 API fix applied: `QPalette.ColorRole.NoRole` (line 71). `test_board.py` (11 tests) covers piece count, colors, main window, cell formula. |
| `src/xiangqi/ui/main.py` | `MainWindow` + `main()` entry point | VERIFIED | 48 lines. Title (line 30), central widget (line 31), size constraints (lines 32-34) all correct. `test_board.py::TestMainWindow` (4 tests) covers all properties. |
| `src/xiangqi/ui/__init__.py` | Public API re-exports | VERIFIED | 18 lines. Re-exports `QXiangqiBoard`, `PieceItem`, `MainWindow` (lines 14-16). `__all__` defined (line 18). Import test passed. |
| `tests/ui/conftest.py` | Pytest fixtures for starting_state and board | VERIFIED | 27 lines. `starting_state` and `board(qtbot)` fixtures as designed. |
| `tests/ui/test_constants.py` | Unit tests for all constants | VERIFIED | 80 lines. 6 tests covering all color, size, ratio values and constraints. All pass. |
| `tests/ui/test_piece_item.py` | Unit tests for PieceItem | VERIFIED | 97 lines. 11 tests covering colors, all 14 characters, diameter, position, z-value. All pass. |
| `tests/ui/test_board.py` | Unit tests for QXiangqiBoard + MainWindow | VERIFIED | 118 lines. 11 tests covering scene structure, 32-piece count, red/black counts, colors, cell formula, 4 MainWindow properties. All pass. |

### Artifact Levels Summary

All 9 source artifacts: **EXISTS + SUBSTANTIVE + WIRED**

**Level 1 (Exists):** All 9 artifacts present in codebase
**Level 2 (Substantive):** All artifacts have real implementation (no stubs, no placeholders)
**Level 3 (Wired):** All imports verified, all dependencies connected

- **constants.py**: Substantive (23 lines of concrete color/size values) + Wired (imported by board.py and board_items.py)
- **board_items.py**: Substantive (108 lines with full paint override) + Wired (imported by board.py, imports constants)
- **board.py**: Substantive (194 lines with full drawBackground) + Wired (uses PieceItem, constants, XiangqiState)
- **main.py**: Substantive (48 lines) + Wired (imports QXiangqiBoard and constants)
- **__init__.py**: Substantive (18 lines with re-exports) + Wired (used by external consumers)
- **4 test files**: All substantive (test content matches implementation)

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `board.py` | `board_items.py` | `from .board_items import PieceItem` | WIRED | `board.py` line 21 imports PieceItem. `_load_pieces()` line 113 instantiates it. |
| `board.py` | `constants.py` | `from .constants import ...` | WIRED | `board.py` lines 22-35 import 8 constants (BOARD_BG, GRID_COLOR, RED_FILL, BLACK_FILL, PIECE_TEXT_COLOR, PIECE_STROKE_COLOR, RIVER_TEXT_COLOR, COORD_TEXT_COLOR, CELL_RATIO, PIECE_FONT_RATIO, RIVER_FONT_RATIO, COORD_FONT_RATIO) for `drawBackground()` |
| `board_items.py` | `constants.py` | `from .constants import ...` | WIRED | `board_items.py` lines 23-30 import 5 constants (RED_FILL, BLACK_FILL, PIECE_TEXT_COLOR, PIECE_STROKE_COLOR, CELL_RATIO, PIECE_FONT_RATIO) |
| `board.py` | `engine/state.py` | `from src.xiangqi.engine.state import XiangqiState` | WIRED | `board.py` line 19 imports XiangqiState. Line 68 uses `XiangqiState.starting()`. Line 107 reads `self._state.board`. |
| `board_items.py` | `engine/types.py` | `from src.xiangqi.engine.types import Piece` | WIRED | `board_items.py` line 21 imports Piece. Line 79 calls `str(Piece(piece_value))` for character rendering. |
| `main.py` | `board.py` | `from .board import QXiangqiBoard` | WIRED | `main.py` line 16 imports QXiangqiBoard. Line 31 sets `QXiangqiBoard()` as central widget. |
| `main.py` | `constants.py` | `from .constants import DEFAULT_SIZE, MIN_SIZE, MAX_SIZE` | WIRED | `main.py` line 17 imports all three window size constants. Lines 32-34 use them. |
| `__init__.py` | `board.py`, `board_items.py`, `main.py` | `from .board import ...` | WIRED | Re-exports all three classes correctly (lines 14-16). Import test passed. |

All 8 key links verified as WIRED. No orphaned imports.

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| **UI-01** | 05-01, 05-02, 05-03, 05-04 | PyQt6 QGraphicsView + QGraphicsScene renders 9x10 board (grid + river gap + palace diagonals + river text + coordinate labels) | SATISFIED | `board.py::QXiangqiBoard` is `QGraphicsView` subclass. `drawBackground()` draws 9 vertical lines (cols 0-8), 10 horizontal lines (river gap at row 4), 8 palace diagonals, "楚河"/"漢界" text, coordinate labels on all 4 sides. All 28 tests pass. Application launches successfully. |
| **UI-02** | 05-01, 05-02, 05-03, 05-04 | Pieces rendered via Piece enum Chinese chars, red/black distinguished by color | SATISFIED | `board_items.py::PieceItem.paint()` calls `str(Piece(piece_value))` for character. Fill color logic: `piece_value > 0` → `#CC2200`, else `#1A1A1A`. `test_piece_item.py::test_all_piece_characters` covers all 14 piece types. `test_board.py::test_piece_colors_match_constants` verifies all 32. All tests pass. |

**Requirement IDs from REQUIREMENTS.md:** UI-01 and UI-02 both mapped to Phase 05 in ROADMAP.md traceability table. All 4 plans (05-01, 05-02, 05-03, 05-04) declare these requirements in their frontmatter `requirements:` fields. No orphaned requirements.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | None found | — | — |

**Scan Results:**
- No TODO/FIXME/XXX/HACK/PLACEHOLDER comments found
- No empty implementations (`return null`, `return {}`, `return []`)
- No hardcoded empty data flows to rendering
- No console.log-only implementations
- All classes substantive with real logic
- `_load_pieces()` reads from actual engine state (not hardcoded)
- All tests have real assertions (no stubs)

---

### Gap Closure Verification (05-04)

**Gap 1 (Blocker): PyQt6 QPalette API Compatibility**
- **Issue:** Application crashed with `AttributeError: type object 'QPalette' has no attribute 'NoRole'`
- **Root Cause:** PyQt6 API changed from `QPalette.NoRole` to `QPalette.ColorRole.NoRole`
- **Fix Applied:** `board.py` line 71 now uses `QPalette.ColorRole.NoRole`
- **Verification:** Source code inspection confirms fix. Application launches successfully. Import test passed.
- **Status:** CLOSED

**Gap 2 (Major): Cell Size Formula Test**
- **Issue:** UAT report flagged potential test failure
- **Investigation:** Test code already uses correct formula `min(vw, vh) / 11.2`
- **Fix Required:** None — test was already correct
- **Verification:** `test_cell_size_formula` passes
- **Status:** FALSE POSITIVE — NO ACTION NEEDED

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

### Test Results Summary

**Automated Tests:** 28/28 passed (100%)

```
tests/ui/test_board.py ........... (11 tests)
tests/ui/test_constants.py ...... (6 tests)
tests/ui/test_piece_item.py ........... (11 tests)
============================= 28 passed in 0.14s ==============================
```

**Coverage:**
- Constants: All 9 color constants, 4 size ratios, 3 window sizes
- PieceItem: All 14 piece types, colors, geometry, positioning
- Board: Scene structure, 32-piece count, color distribution, cell formula
- MainWindow: Title, central widget, size constraints, min/max bounds

**Application Launch Test:** PASSED
- MainWindow created successfully
- Window title verified: "RL-Xiangqi v0.2"
- Central widget verified: QXiangqiBoard

---

### Gaps Summary

No gaps remaining. All must-haves verified after gap closure.

**Phase 05 Status:** COMPLETE

The codebase fully implements the Phase 05 goal:

- **Board rendering (UI-01):** `QXiangqiBoard.drawBackground()` draws a complete 9x10 xiangqi board with all required elements. `resizeEvent()` handles responsive scaling via `min(vw, vh)/11.2`.
- **Piece rendering (UI-02):** `PieceItem.paint()` renders all 32 starting pieces with correct Chinese characters and red/black colors. All 14 piece types verified. `_load_pieces()` reads from the engine state.
- **Architecture:** Clean 4-file module (`constants.py`, `board_items.py`, `board.py`, `main.py`) with correct imports and responsibilities. `__init__.py` provides clean public API.
- **Testing:** Comprehensive test suite (4 files, 322 lines, 28 tests) covers all constants, PieceItem, QXiangqiBoard scene structure, piece counts/colors/characters, and MainWindow properties.
- **Gap Closure:** PyQt6 API compatibility issue fixed. Application launches successfully.

---

_Verified: 2026-03-24T09:30:00Z_
_Verifier: Claude (gsd-verifier)_
_Re-verification: Yes (after gap closure plan 05-04)_
