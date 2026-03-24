---
status: complete
phase: 05-board-rendering
source:
  - .planning/phases/05-board-rendering/05-01-PLAN-SUMMARY.md
  - .planning/phases/05-board-rendering/05-02-PLAN-SUMMARY.md
  - .planning/phases/05-board-rendering/05-03-PLAN-SUMMARY.md
started: "2026-03-24T01:07:00Z"
updated: "2026-03-24T01:25:00Z"
---

## Current Test

[testing complete]

## Tests

### 1. Board Renders with Green Felt Background and Grid Lines
expected: |
  The board window shows a green felt background (#7BA05B) covering the full scene area,
  with dark green grid lines (#2D5A1B) forming the 9-column × 10-row grid.
  Vertical lines at x positions 0.6–8.4 cells, horizontal lines spanning the full width at rows 0–9.
result: blocked
blocked_by: code-bug
reason: "App crashes on startup: AttributeError: type object 'QPalette' has no attribute 'NoRole'"

### 2. River Text "楚河" and "漢界" Visible on Board
expected: |
  Between rows 4 and 5, the river text appears: "楚河" on the left half and "漢界" on the right half,
  in the dark green color (#2D5A1B) with font size proportional to cell size.
result: blocked
blocked_by: code-bug
reason: "Same error as Test 1"

### 3. Palace Diagonal Lines Rendered at Both Ends
expected: |
  The top and bottom palace areas (columns 3–5, rows 0–2 and 7–9) show diagonal lines
  connecting the corner squares to form the palace X patterns.
result: blocked
blocked_by: code-bug
reason: "Same error as Test 1"

### 4. Coordinate Labels Visible on Board Edges
expected: |
  Red column labels 1–9 appear along the bottom edge (left side),
  and black column labels 9–1 appear along the top edge (right side).
  Row labels 1–10 appear on the left and right edges.
result: blocked
blocked_by: code-bug
reason: "Same error as Test 1"

### 5. Red Pieces Displayed in #CC2200 with Correct Chinese Characters
expected: |
  All 16 red pieces appear as filled circles in #CC2200 (deep red-orange) with a white 2px stroke.
  Each piece displays its correct Chinese character centered in the circle.
  Red pieces: 帅, 仕, 相, 马, 车, 炮, 兵 (in correct starting positions).
result: blocked
blocked_by: code-bug
reason: "Same error as Test 1"

### 6. Black Pieces Displayed in #1A1A1A with Correct Chinese Characters
expected: |
  All 16 black pieces appear as filled circles in #1A1A1A (near-black) with a white 2px stroke.
  Each piece displays its correct Chinese character centered in the circle.
  Black pieces: 将, 士, 象, 马, 车, 炮, 卒 (in correct starting positions).
result: blocked
blocked_by: code-bug
reason: "Same error as Test 1"

### 7. 32 Pieces Total in Correct Starting Positions
expected: |
  The board shows exactly 32 pieces in the standard xiangqi starting formation:
  5 red pieces in the top row (R, advisor, minister, horse, chariot ×2),
  5 black pieces in the bottom row,
  2 red cannons + 5 red soldiers down the right/left flanks,
  2 black cannons + 5 black soldiers up the flanks.
result: blocked
blocked_by: code-bug
reason: "Same error as Test 1"

### 8. MainWindow Launches with Title "RL-Xiangqi v0.2"
expected: |
  Running the application opens a window titled "RL-Xiangqi v0.2".
  The central widget is the QXiangqiBoard filling the window.
result: issue
reported: "AttributeError: type object 'Qt' has no attribute 'BackgroundRole'"
severity: blocker

### 9. MainWindow Default Size (480 × 600), Min (360 × 450), Max (720 × 900)
expected: |
  MainWindow opens at 480×600 pixels by default.
  Resizing is constrained: cannot go below 360×450 or above 720×900.
result: issue
reported: "AttributeError: type object 'Qt' has no attribute 'BackgroundRole'"
severity: blocker

### 10. Board Pieces Scale Correctly on Window Resize
expected: |
  Dragging the window corner to resize the window maintains the board's 9:10 aspect ratio
  (cell = min(width, height) / 11.2). All 32 pieces re-center at their correct board positions
  at the new scale without overlapping grid lines.
result: blocked
blocked_by: code-bug
reason: "Same error as Test 1 - app crashes on startup"

### 11. Automated Test Suite: All Constants and PieceItem Tests Pass
expected: |
  pytest tests/ui/ — all tests in test_constants.py and test_piece_item.py pass
  (17 tests covering color constants, ratio constants, piece characters, fill colors, positions).
result: pass

### 12. Automated Test Suite: Board Scene and Piece Counts
expected: |
  pytest tests/ui/ — board scene exists, 32 pieces total, 16 red, 16 black,
  no empty squares in starting positions, piece colors match constants.
result: issue
reported: "Qt.BackgroundRole.NoRole does not exist in PyQt6 — board.py:71
  causes all QXiangqiBoard tests to error (11 tests: 6 ERROR + 5 FAIL)"
severity: blocker

### 13. Automated Test Suite: MainWindow Title and Size
expected: |
  pytest tests/ui/ — MainWindow title is "RL-Xiangqi v0.2", default size is (480, 600),
  min/max size constraints set correctly.
result: issue
reported: "Qt.BackgroundRole.NoRole does not exist in PyQt6 — main.py:31 → board.py:71
  causes all MainWindow tests to error (4 tests: ERROR)"
severity: blocker

### 14. Cell Size Formula Correct for All Viewport Sizes
expected: |
  pytest tests/ui/ — cell = min(viewport_width, viewport_height) / 11.2 produces correct
  cell sizes at various viewport dimensions (360×450, 480×600, 720×900, 400×500).
result: issue
reported: "test_cell_size_formula hardcodes wrong expected_cell for (480, 600):
  expects 600/11.2=53.57 but formula gives 480/11.2=42.86; diff=8.03 exceeds 0.01"
severity: major

### 15. UI Constants Module: All 9 Colors, 4 Ratios, 3 Window Sizes Defined
expected: |
  from src.xiangqi.ui.constants import BOARD_BG, GRID_COLOR, RED_FILL, BLACK_FILL,
  PIECE_TEXT_COLOR, PIECE_STROKE_COLOR, RIVER_TEXT_COLOR, COORD_TEXT_COLOR,
  CELL_RATIO, PIECE_FONT_RATIO, RIVER_FONT_RATIO, COORD_FONT_RATIO,
  DEFAULT_SIZE, MIN_SIZE, MAX_SIZE — all import successfully.
result: pass

### 16. Public API: QXiangqiBoard, PieceItem, MainWindow Re-exported from ui Package
expected: |
  from src.xiangqi.ui import QXiangqiBoard, PieceItem, MainWindow — all import successfully.
result: pass

## Summary

total: 16
passed: 3
issues: 5
pending: 0
skipped: 0
blocked: 8

## Gaps

- truth: "Application launches successfully with MainWindow and QXiangqiBoard"
  status: failed
  reason: "User reported: AttributeError: type object 'QPalette' has no attribute 'NoRole' — app crashes on startup"
  severity: blocker
  test: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 13
  root_cause: "PyQt6 does not have Qt.BackgroundRole.NoRole or QPalette.NoRole — correct API is QPalette.ColorRole.NoRole or setAutoFillBackground(False)"
  artifacts:
    - path: "src/xiangqi/ui/board.py"
      issue: "Line 71: self.setBackgroundRole(QPalette.NoRole) — QPalette.NoRole does not exist in PyQt6"
  missing:
    - "Fix board.py:71 to use correct PyQt6 API for disabling background role"
  debug_session: ".planning/debug/board-qt-attributerror.md"

- truth: "Cell size formula min(vw,vh)/11.2 correct across all viewport dimensions"
  status: failed
  reason: "User reported: test_cell_size_formula hardcodes wrong expected_cell for (480, 600): expects 600/11.2=53.57 but formula gives 480/11.2=42.86; diff=8.03 exceeds 0.01"
  severity: major
  test: 14
  root_cause: "Test hardcodes expected_cell = max(vw,vh)/11.2 for cases 1-3, but the formula uses min(vw,vh)/11.2. For (480,600): expected=600/11.2=53.57 but actual=480/11.2=42.86"
  artifacts:
    - path: "tests/ui/test_board.py"
      issue: "TestCellSizeFormula.test_cell_size_formula — line 67 hardcodes expected_cell = max(vw,vh)/11.2; correct expected_cell per test case should be min(vw,vh)/11.2"
  missing:
    - "Fix test_cell_size_formula expected_cell values to match min(vw,vh)/11.2 per case"
  debug_session: ".planning/debug/test-cell-size-formula.md"
