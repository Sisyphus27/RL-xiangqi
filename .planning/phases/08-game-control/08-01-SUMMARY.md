---
phase: 08-game-control
plan: 01
type: summary
subsystem: ui
tags: [toolbar, qt, game-control, signals]
dependency_graph:
  requires: [07-ai-interface]
  provides: [08-02]
  affects: []
tech_stack:
  added: []
  patterns:
    - "QToolBar with QPushButton widgets"
    - "QShortcut for keyboard accelerators"
    - "Signal-slot for button state management"
key_files:
  created: []
  modified:
    - src/xiangqi/ui/main.py
    - src/xiangqi/controller/game_controller.py
decisions:
  - "QShortcut from PyQt6.QtGui (not QtWidgets)"
  - "Undo button disabled initially, enabled via undo_available signal"
  - "new_game() re-randomizes human side for variety"
  - "undo() removes both AI and human moves to return to human's turn"
metrics:
  duration_minutes: 25
  completed_date: "2026-03-26"
---

# Phase 08 Plan 01: Toolbar and UI Summary

## One-Liner

Added QToolBar with New Game (新对局) and Undo (悔棋) buttons, keyboard shortcuts (Ctrl+N/Ctrl+Z), and signal-based button state management.

## What Was Built

### MainWindow Toolbar (`src/xiangqi/ui/main.py`)

- **`_setup_toolbar()`**: Creates QToolBar titled "游戏控制" with:
  - `_new_game_btn`: "新对局" button, always enabled, tooltip "开始新对局 (Ctrl+N)"
  - `_undo_btn`: "悔棋" button, initially disabled, tooltip "悔棋 (Ctrl+Z)"
  - Keyboard shortcuts: Ctrl+N → `_on_new_game()`, Ctrl+Z → `_on_undo()`

- **`_connect_controller_signals()`**: Wires `controller.undo_available` signal to `_undo_btn.setEnabled`

- **`_on_new_game()` / `_on_undo()`**: Handler methods delegating to controller

### GameController API (`src/xiangqi/controller/game_controller.py`)

- **`undo_available` signal**: Emits bool to control undo button state
- **`new_game()` method**: Resets engine to starting position, re-randomizes human side, syncs board via `sync_state()`, triggers AI if human plays Black
- **`undo()` method**: Undoes moves (both AI and human) to return to human's turn, syncs board state

## Verification Results

All checks passed:
- Toolbar buttons exist with correct labels ("新对局", "悔棋")
- Undo button starts disabled
- Controller has required methods and signals
- Imports resolve correctly

## Commits

| Hash | Message |
|------|---------|
| c8f0f81 | feat(08-01): add toolbar with New Game and Undo buttons |
| 611f527 | feat(08-01): add new_game() and undo() methods to GameController |

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None - all functionality implemented.

## Self-Check: PASSED

- [x] src/xiangqi/ui/main.py modified
- [x] src/xiangqi/controller/game_controller.py modified
- [x] Commits c8f0f81 and 611f527 exist
- [x] Import verification passed
- [x] Toolbar verification passed
