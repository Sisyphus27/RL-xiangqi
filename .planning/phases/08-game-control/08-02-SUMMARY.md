---
phase: 08-game-control
plan: 02
type: summary
subsystem: controller
tags: [game-control, ui, undo, new-game]
dependency_graph:
  requires: [07-ai-interface]
  provides: [game-control-logic]
  affects: [main-window-ui]
tech-stack:
  added: []
  patterns: [pyqt-signals, random-side-assignment, double-step-undo]
key-files:
  created: []
  modified:
    - src/xiangqi/controller/game_controller.py
    - src/xiangqi/ui/board.py
decisions:
  - "Random side assignment: 50% probability for human to play Red or Black"
  - "Double-step undo: undo both human move and AI response together"
  - "undo_available signal controls button state in UI"
  - "Status bar format: 你执红方/黑方 | 红方回合/黑方回合/AI思考中..."
metrics:
  duration: "30 minutes"
  completed_date: "2026-03-26"
  tests_passing: 284
---

# Phase 08 Plan 02: GameController Logic Summary

## One-Liner

Extended GameController with game control logic: random side assignment, new game initialization, double-step undo, and updated status bar with side indicator per UI-08 and UI-09 requirements.

## What Was Built

### Core Features

1. **Random Side Assignment (D-07)**
   - `_human_side: int` attribute initialized to `random.choice([1, -1])`
   - 50% probability for human to play Red (+1) or Black (-1)
   - Side indicator shown in status bar: "你执红方" or "你执黑方"

2. **New Game Functionality (UI-08)**
   - `new_game()` method resets engine to starting position
   - Re-randomizes human side for variety
   - Clears board and reloads pieces via `sync_state()`
   - Triggers AI move immediately if human plays Black (D-09)
   - Emits `undo_available(False)` since undo stack is empty

3. **Undo Functionality (UI-09)**
   - `undo()` method performs double-step undo (human + AI move)
   - Guard: cannot undo during AI thinking
   - Guard: requires at least 2 moves in history
   - Updates board display and undo button state

4. **Status Bar Enhancement**
   - Updated format: `{side_text} | {turn_text}`
   - Side text: "你执红方" or "你执黑方"
   - Turn text: "红方回合", "黑方回合", or "AI 思考中..."

5. **Turn-Aware Interaction Control (D-09)**
   - `_on_turn_changed()` enables interaction only on human's turn
   - Replaces hardcoded `turn == 1` check with `turn == self._human_side`
   - AI turn trigger updated to `if self._engine.turn != self._human_side`

6. **Undo Button State Management**
   - `undo_available = pyqtSignal(bool)` signal added
   - Emits `False` during AI thinking (D-04)
   - Emits `True` after AI finishes if moves exist (D-05)
   - Emits `False` after new game (empty undo stack)

### Board Updates

- `refresh_pieces()` method: clears and reloads all piece items from current state
- `sync_state(state)` method: updates internal `_state` reference and refreshes display
- Used by GameController after engine reset or undo operations

## Files Modified

| File | Changes |
|------|---------|
| `src/xiangqi/controller/game_controller.py` | Added `_human_side`, `undo_available`, `new_game()`, `undo()`, updated status bar and interaction control |
| `src/xiangqi/ui/board.py` | Added `refresh_pieces()` and `sync_state()` methods |

## Key Implementation Details

### Double-Step Undo Logic

```python
def undo(self) -> None:
    # Guard: cannot undo during AI turn
    if self._engine.turn != self._human_side:
        return

    # Need at least 2 moves to undo (human + AI)
    if len(self._engine.move_history) < 2:
        return

    # Double-step undo
    self._engine.undo()  # Undo AI move
    self._engine.undo()  # Undo human move

    # Update UI...
```

### Random Side Assignment

```python
self._human_side: int = random.choice([1, -1])  # +1=Red, -1=Black
```

### Status Bar Format

```python
side_text = "你执红方" if self._human_side == 1 else "你执黑方"
status.showMessage(f"{side_text} | {turn_text}")
```

## Verification

All 284 tests passing:
- 5 tests in `tests/controller/test_game_controller.py`
- 11 tests in `tests/ui/test_board.py`
- All existing engine, legal, and UI tests continue to pass

## Deviations from Plan

None - plan executed exactly as written.

## Dependencies

- Requires Phase 07 GameController base implementation (completed)
- Plan 08-01 provides the UI buttons that trigger these methods

## Next Steps

- Plan 08-01: UI buttons for "新对局" and "悔棋" to connect to these methods
- Integration testing with full game flow
