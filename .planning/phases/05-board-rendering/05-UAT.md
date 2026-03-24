---
status: complete
phase: 05-board-rendering
source:
  - .planning/phases/05-board-rendering/05-01-PLAN-SUMMARY.md
  - .planning/phases/05-board-rendering/05-02-PLAN-SUMMARY.md
  - .planning/phases/05-board-rendering/05-03-PLAN-SUMMARY.md
  - .planning/phases/05-board-rendering/05-04-SUMMARY.md
  - .planning/phases/05-board-rendering/05-05-SUMMARY.md
  - .planning/phases/05-board-rendering/05-06-SUMMARY.md
started: "2026-03-24T03:27:00Z"
updated: "2026-03-24T03:35:00Z"
---

## Current Test

[testing complete]

## Tests

### 1. Application Cold Start
expected: Launch the application from scratch (no prior state). The MainWindow opens successfully without any errors or exceptions. Window displays the xiangqi board UI.
result: issue
reported: "成功打开可以看到象棋棋盘界面。但是看到的米字格是在车到相，马到炮的位置。而非应该正确的在帅/将的位置。黑方的卒前面少了一行，虽然那少的一行有序号但是没有划线。其次当前不能点击（不知道是否是这个phase完成）。"
severity: major

### 2. MainWindow Title and Initial Display
expected: Window title shows "RL-Xiangqi v0.2". The board is visible in the central widget area.
result: pass

### 3. Window Default Size and Constraints
expected: Window opens at approximately 480×600 pixels. Can resize within min (360×450) to max (720×900) bounds.
result: pass

### 4. Board Green Felt Background
expected: The board background is a green felt color (#7BA05B) covering the full visible area.
result: pass

### 5. Grid Lines Rendered (9×10)
expected: Dark green grid lines (#2D5A1B) form a 9-column by 10-row grid. Vertical lines visible from column 0 to 8, horizontal lines from row 0 to 9 with river gap.
result: issue
reported: "黑方卒前面少了一行（有行号但无横线）。红方底线竖着的线超出了边界（黑方正常），直接竖着连接到最边界处了。"
severity: major

### 6. River Text Display
expected: Between rows 4 and 5, "楚河" appears on the left side and "漢界" on the right side in dark green text.
result: pass

### 7. Palace Diagonal Lines
expected: Diagonal lines form X patterns in both palace areas (top: columns 3-5, rows 0-2; bottom: columns 3-5, rows 7-9).
result: issue
reported: "米字格实际位置：top: columns 0-2, 6-8, rows 0-2; bottom: columns 0-2, 6-8, rows 7-9。应该在中间列（columns 3-5）而非两侧。"
severity: major

### 8. Coordinate Labels
expected: Column labels (1-9 red at bottom, 9-1 black at top) and row labels (1-10 on left and right edges) are visible.
result: pass

### 9. Red Pieces Visual Appearance
expected: All red pieces appear as filled circles in deep red-orange (#CC2200) with white 2px stroke borders. Each displays its Chinese character (帅, 仕, 相, 马, 车, 炮, 兵).
result: pass

### 10. Black Pieces Visual Appearance
expected: All black pieces appear as filled circles in near-black (#1A1A1A) with white 2px stroke borders. Each displays its Chinese character (将, 士, 象, 马, 车, 炮, 卒).
result: pass

### 11. All 32 Pieces in Starting Positions
expected: The board shows exactly 32 pieces in standard xiangqi starting formation: 16 red pieces (top half), 16 black pieces (bottom half), with correct piece types in correct positions.
result: pass

### 12. Board Resizing Maintains Aspect Ratio
expected: Resizing the window causes the board to scale proportionally. All grid lines, text, and pieces remain correctly positioned at the new scale. Cell size formula: min(width, height) / 11.2.
result: pass

### 13. Automated Test Suite Passes
expected: Running `pytest tests/ui/ -v` shows all 28 tests passing (test_constants.py: 6 tests, test_piece_item.py: 11 tests, test_board.py: 11 tests).
result: pass

### 14. UI Constants Import Successfully
expected: `from src.xiangqi.ui.constants import BOARD_BG, GRID_COLOR, RED_FILL, BLACK_FILL, PIECE_TEXT_COLOR, PIECE_STROKE_COLOR, RIVER_TEXT_COLOR, COORD_TEXT_COLOR, CELL_RATIO, PIECE_FONT_RATIO, RIVER_FONT_RATIO, COORD_FONT_RATIO, DEFAULT_SIZE, MIN_SIZE, MAX_SIZE` succeeds without errors.
result: pass

### 15. Public API Re-exports Work
expected: `from src.xiangqi.ui import QXiangqiBoard, PieceItem, MainWindow` imports all three classes successfully.
result: pass

## Summary

total: 15
passed: 10
issues: 3
pending: 0
skipped: 0
blocked: 0

## Gaps

- truth: "Palace diagonal lines form X patterns in correct positions (columns 3-5, rows 0-2 top palace; columns 3-5, rows 7-9 bottom palace)"
  status: failed
  reason: "User reported: 实际位置在 top: columns 0-2, 6-8, rows 0-2; bottom: columns 0-2, 6-8, rows 7-9。应该在中间列（columns 3-5）而非两侧。"
  severity: major
  test: 7
  root_cause: ""
  artifacts: []
  missing: []
  debug_session: ""

- truth: "Grid lines form complete 9×10 grid with river gap between rows 4-5"
  status: failed
  reason: "User reported: 黑方的卒前面少了一行，虽然那少的一行有序号但是没有划线"
  severity: major
  test: 1
  root_cause: ""
  artifacts: []
  missing: []
  debug_session: ""

- truth: "Vertical grid lines stay within board boundaries"
  status: failed
  reason: "User reported: 红方底线竖着的线超出了边界（黑方正常），直接竖着连接到最边界处了"
  severity: major
  test: 5
  root_cause: ""
  artifacts: []
  missing: []
  debug_session: ""
