---
status: partial
phase: 06-piece-interaction
source: 06-00-SUMMARY.md, 06-01-SUMMARY.md, 06-02-SUMMARY.md
started: 2026-03-25T03:07:00Z
updated: 2026-03-25T03:11:00Z
---

## Current Test

[testing paused — 5 items outstanding]

## Tests

### 1. Cold Start Smoke Test
expected: 启动应用：conda activate xqrl && python -m src.xiangqi.ui.main。窗口应该正常打开，棋盘渲染完成，无报错，无崩溃。
result: pass

### 2. Click Red Piece → Gold Selection Ring
expected: 点击红色棋子（如 row 9, col 0 红车位置），棋子上方出现金色圆环（#FFD700），棋子被选中
result: issue
reported: "没有任何反应"
severity: major

### 3. Gold Legal Move Dots Appear
expected: 选中红色棋子后，棋盘上该棋子的合法移动目标位置显示金色圆点（dot），同时显示金色选择环
result: skipped
reason: "依赖test2"

### 4. Click Legal Target → Piece Moves
expected: 点击金色圆点（合法目标），棋子移动到新位置，高亮清除，move_applied 信号发出
result: skipped
reason: "依赖test2"

### 5. Switch Selection → Previous Clears
expected: 选中另一个红色棋子，之前的选择环和圆点清除，新的棋子显示选择环和合法目标圆点
result: skipped
reason: "依赖test2"

### 6. Click Invalid → Deselects
expected: 点击非法位置（空位或非法目标），选择清除，所有高亮消失
result: skipped
reason: "依赖test2"

### 7. Window Resize → Highlights Persist
expected: 调整窗口大小后，棋盘正确缩放；如果有选中棋子，选择环和合法目标圆点应在正确位置重新出现
result: skipped
reason: "依赖test2"

## Summary

total: 7
passed: 1
issues: 1
pending: 0
skipped: 5

## Gaps

- truth: "点击红色棋子后显示金色选择环"
  status: failed
  reason: "User reported: 没有任何反应"
  severity: major
  test: 2
  root_cause: ""
  artifacts: []
  missing: []
  debug_session: ""

### 2. Click Red Piece → Gold Selection Ring
expected: 点击红色棋子（如 row 9, col 0 红车位置），棋子上方出现金色圆环（#FFD700），棋子被选中
result: [pending]

### 3. Gold Legal Move Dots Appear
expected: 选中红色棋子后，棋盘上该棋子的合法移动目标位置显示金色圆点（dot），同时显示金色选择环
result: [pending]

### 4. Click Legal Target → Piece Moves
expected: 点击金色圆点（合法目标），棋子移动到新位置，高亮清除，move_applied 信号发出
result: [pending]

### 5. Switch Selection → Previous Clears
expected: 选中另一个红色棋子，之前的选择环和圆点清除，新的棋子显示选择环和合法目标圆点
result: [pending]

### 6. Click Invalid → Deselects
expected: 点击非法位置（空位或非法目标），选择清除，所有高亮消失
result: [pending]

### 7. Window Resize → Highlights Persist
expected: 调整窗口大小后，棋盘正确缩放；如果有选中棋子，选择环和合法目标圆点应在正确位置重新出现
result: [pending]

## Summary

total: 7
passed: 0
issues: 0
pending: 7
skipped: 0

## Gaps

- truth: "点击红色棋子后显示金色选择环"
  status: failed
  reason: "User reported: 没有任何反应"
  severity: major
  test: 2
  root_cause: ""
  artifacts: []
  missing: []
  debug_session: ""
