---
status: partial
phase: 06-piece-interaction
source: 06-00-SUMMARY.md, 06-01-SUMMARY.md, 06-02-SUMMARY.md
started: 2026-03-25T03:07:00Z
updated: 2026-03-25T06:45:00Z
---

## Current Test

[testing complete - 2 issues found]

## Tests

### 1. Cold Start Smoke Test
expected: 启动应用：conda activate xqrl && python -m src.xiangqi.ui.main。窗口应该正常打开，棋盘渲染完成，无报错，无崩溃。
result: pass

### 2. Click Red Piece → Gold Selection Ring
expected: 点击红色棋子（如 row 9, col 0 红车位置），棋子上方出现金色圆环（#FFD700），棋子被选中
result: issue
reported: "我的鼠标能点到，但并不是实际位置。例如我点你说的这个车，只有在点击其右上方才能选中。而且在不同分辨率点的相对位置还不一样。"
severity: major

### 3. Gold Legal Move Dots Appear
expected: 选中红色棋子后，棋盘上该棋子的合法移动目标位置显示金色圆点（dot），同时显示金色选择环
result: pass

### 4. Click Legal Target → Piece Moves
expected: 点击金色圆点（合法目标），棋子移动到新位置，高亮清除，move_applied 信号发出
result: pass

### 5. Switch Selection → Previous Clears
expected: 选中另一个红色棋子，之前的选择环和圆点清除，新的棋子显示选择环和合法目标圆点
result: issue
reported: "我走第一个棋子时会显示可移动位置，当其完成移动后再选择另一个棋子（这时存在黄圈）但是无法进行移动（也没有显示可移动位置）。我也没法操作黑棋"
severity: major

### 6. Click Invalid → Deselects
expected: 点击非法位置（空位或非法目标），选择清除，所有高亮消失
result: pass

### 7. Window Resize → Highlights Persist
expected: 调整窗口大小后，棋盘正确缩放；如果有选中棋子，选择环和合法目标圆点应在正确位置重新出现
result: pass

## Summary

total: 7
passed: 5
issues: 2
pending: 0
skipped: 0

## Gaps

- truth: "点击红色棋子后显示金色选择环"
  status: diagnosed
  reason: "User reported: 我的鼠标能点到，但并不是实际位置。例如我点你说的这个车，只有在点击其右上方才能选中。而且在不同分辨率点的相对位置还不一样。"
  severity: major
  test: 2
  root_cause: "Hardcoded viewport-to-scene offset (103.5, 2.0) in mousePressEvent (board.py lines 163-164) does not account for QGraphicsView's dynamic scene centering, which varies with viewport size and resolution. Should use self.mapToScene() instead."
  artifacts:
    - path: "src/xiangqi/ui/board.py"
      issue: "lines 163-164: Hardcoded coordinate conversion vp_x - 103.5, vp_y - 2.0"
  missing:
    - "Replace hardcoded offset with self.mapToScene(event.position())"
  debug_session: ".planning/debug/click-offset.md"
- truth: "选中另一个红色棋子，之前的选择环和圆点清除，新的棋子显示选择环和合法目标圆点"
  status: diagnosed
  reason: "User reported: 我走第一个棋子时会显示可移动位置，当其完成移动后再选择另一个棋子（这时存在黄圈）但是无法进行移动（也没有显示可移动位置）。我也没法操作黑棋"
  severity: major
  test: 5
  root_cause: "Turn management mismatch. UI hardcoded to only allow red pieces (lines 192, 204: piece_value > 0), but engine alternates turns. After red moves, turn becomes black, so legal_moves() returns black's moves. Selecting a red piece queries black's legal moves, resulting in empty list."
  artifacts:
    - path: "src/xiangqi/ui/board.py"
      issue: "lines 192, 204: Only allows red piece selection (piece_value > 0)"
    - path: "src/xiangqi/engine/engine.py"
      issue: "line 180: Flips turn after move, line 193: legal_moves() returns moves for current turn"
  missing:
    - "UI should check engine.turn and only allow selecting pieces of the current turn's color"
    - "Or implement two-player mode where both sides can be operated"
  debug_session: ".planning/debug/second-selection-no-legal-moves.md"
