---
phase: 03-endgame-detection
plan: "01"
subsystem: engine/endgame
tags: [END-01, END-02, END-03, END-04, checkmate, stalemate, repetition, long-check, long-chase]
dependency_graph:
  requires: []
  provides:
    - src/xiangqi/engine/endgame.py: get_game_result(), check_long_check(), check_long_chase(), check_repetition()
    - src/xiangqi/engine/repetition.py: RepetitionState, check_repetition(), check_long_check(), check_long_chase()
    - src/xiangqi/engine/rules.py: backward-compatibility re-exports
  affects:
    - tests/test_endgame.py
    - tests/test_repetition.py
    - src/xiangqi/engine/legal.py (_generals_face_each_other added)
    - src/xiangqi/engine/state.py (__all__ added)
tech_stack:
  added: [RepetitionState dataclass, Zobrist hash history, lazy import pattern]
  patterns: [priority-order game result detection, meaningful-progress chase tracking]
key_files:
  created:
    - src/xiangqi/engine/endgame.py
    - src/xiangqi/engine/repetition.py
    - tests/test_endgame.py
    - tests/test_repetition.py
  modified:
    - src/xiangqi/engine/rules.py (converted to thin re-export shim)
    - src/xiangqi/engine/legal.py (_generals_face_each_other added)
    - src/xiangqi/engine/state.py (__all__ added)
decisions:
  - id: D03-01
    decision: "Lazy import of repetition.py inside get_game_result() to avoid circular dependency"
    rationale: "endgame.py imports from repetition.py; legal.py (used by repetition.py) imports types; moving _generals_face_each_other into legal.py resolves the cycle"
  - id: D03-02
    decision: "RepetitionState lives in engine.py (Phase 4), not XiangqiState"
    rationale: "Separation of concerns: XiangqiState is pure board state; repetition tracking is game-history policy"
  - id: D03-03
    decision: "Long check -> DRAW, Long chase -> chaser LOSES (not DRAW)"
    rationale: "Per CONTEXT.md and WXO rules: chaser loses because they deliberately create the loop"
  - id: D03-04
    decision: "Meaningful progress: check/capture/new attacking square resets chase sequence"
    rationale: "WXO rules: chaser must make meaningful progress (give check, capture, or move piece). Same (att_sq, tgt_sq) pair without progress = repeat = accumulate toward long chase"
  - id: D05-01
    decision: "enemy = -new_state.turn in _detect_chase (not -mover or -piece_color)"
    rationale: "After apply_move(), new_state.turn = opponent. enemy = -new_state.turn correctly identifies opponent's pieces."
metrics:
  duration_minutes: ~65
  completed_date: "2026-03-20"
  tasks_completed: 7
  tests_added: 30
  bugs_auto_fixed: 6
  test_results: 132 passed
---

# Phase 03 Plan 01: Endgame Detection — Summary

## One-liner

Modular endgame detection layer for Xiangqi with checkmate, stalemate (困毙), threefold repetition, long check (长将), and long chase (长捉) rules.

## What was built

### `src/xiangqi/engine/endgame.py`
`get_game_result(state, rep_state=None)` — single entry point returning `'IN_PROGRESS'`, `'RED_WINS'`, `'BLACK_WINS'`, or `'DRAW'`. Priority order:

1. `check_repetition` — any position hash appears 3x in `zobrist_hash_history` -> DRAW
2. `check_long_check` — `consecutive_check_count >= 4` -> DRAW
3. `check_long_chase` — `len(chase_seq) >= 4` with same `(att_sq, tgt_sq)` pair -> chaser LOSES
4. `generate_legal_moves == 0` + `is_in_check` -> opponent wins (checkmate)
5. `generate_legal_moves == 0` -> opponent wins (stalemate / 困毙)
6. Otherwise -> `'IN_PROGRESS'`

Uses lazy `from .repetition import ...` inside the function to avoid circular import at module load time.

### `src/xiangqi/engine/repetition.py`
- `RepetitionState` dataclass: `consecutive_check_count`, `chase_seq: List[tuple[int,int]]`, `last_chasing_color`
- `RepetitionState.update(prev_state, move, new_state)` — call after `apply_move()`. Tracks long-check counter and chase sequence with meaningful-progress logic.
- `_detect_chase(prev_state, move, new_state)` — detects whether a move is a chase (attacking a non-king enemy piece). Rebuilds post-move board and calls `gen_chariot`/`gen_cannon`/`gen_general`/`gen_soldier` to enumerate attacked squares.
- `check_repetition(state)`, `check_long_check(state, rep_state)`, `check_long_chase(state, rep_state)`

### `src/xiangqi/engine/rules.py` (rewritten as shim)
Thin re-export of `get_game_result`, `flying_general_violation`, `_generals_face_each_other`, `is_in_check`, `is_legal_move`, `generate_legal_moves`, `apply_move`. All logic moved to `endgame.py`, `legal.py`, `state.py`.

### `src/xiangqi/engine/legal.py`
Added `_generals_face_each_other(board)` — returns True if red and black generals occupy the same file with no pieces between them. Previously only in `rules.py`.

### `tests/test_endgame.py`
6 tests: `test_checkmate_red_loses`, `test_checkmate_black_loses`, `test_stalemate_also_loss` (困毙 always = opponent win), `test_starting_position_in_progress`, `test_midgame_in_progress`, `test_repetition_draw_before_checkmate`.

### `tests/test_repetition.py`
24 tests covering: `check_repetition` (END-04), `check_long_check` (END-03), `check_long_chase` (END-03), `RepetitionState.update()` semantics, `RepetitionState.reset()`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `_generals_face_each_other` was in `rules.py`, not `legal.py`**
- **Found during:** Task 4 (plan assumed it was in `legal.py`)
- **Issue:** Plan's reference to `legal._generals_face_each_other` did not exist; function was in `rules.py`
- **Fix:** Extracted the function body into `legal.py` as `_generals_face_each_other(board)`, added to `legal.__all__`, re-exported from `rules.py`
- **Files modified:** `src/xiangqi/engine/legal.py`, `src/xiangqi/engine/rules.py`
- **Commit:** `8a33424`

**2. [Rule 1 - Bug] `is_in_check` argument was wrong in `update()`**
- **Found during:** Task 7 (`test_update_increments_check_count_on_checking_move`)
- **Issue:** `is_in_check(new_state, mover)` — checks if mover is in check, but mover just gave check so opponent is in check
- **Fix:** Changed to `is_in_check(new_state, new_state.turn)` (after `apply_move()`, `new_state.turn` is opponent who was just checked)
- **Files modified:** `src/xiangqi/engine/repetition.py`
- **Commit:** `ce36fc2`

**3. [Rule 1 - Bug] Chariot chasing toward pawn: `gen_chariot` in non-capture sliding mode stops at the pawn**
- **Found during:** Task 7 (`test_update_resets_chase_seq_on_new_attacking_square`, `test_update_appends_to_chase_seq_on_repeated_att_sq`)
- **Issue:** Tests had chariot at (7,0) moving to (6,0) (toward pawn at 3,0). `gen_chariot` slides and stops on the first piece — since the pawn is between (7,0) and (3,0), the chariot never attacks the pawn.
- **Fix:** Redesigned tests with chariot at (6,0) moving to (7,0) (away from pawn). `gen_chariot` slides upward from (7,0) and successfully attacks the pawn at (3,0).
- **Files modified:** `tests/test_repetition.py`
- **Commit:** `008a2ef`

**4. [Rule 1 - Bug] `_detect_chase` move extraction: `m >> 9` returns full 17-bit integer**
- **Found during:** Task 7 (investigation of gen_chariot output)
- **Issue:** `m >> 9` on a 17-bit encoded move returns the full upper bits (e.g., 155 instead of 27 for pawn capture). This caused attacked squares to be wrong or out-of-bounds.
- **Fix:** Use `(m >> 9) & 0x7F` (7-bit mask matching `decode_move`'s extraction)
- **Files modified:** `src/xiangqi/engine/repetition.py`
- **Commit:** `008a2ef`

**5. [Rule 1 - Bug] `_detect_chase` wrong color for `gen_chariot`**
- **Found during:** Task 7 (investigation)
- **Issue:** Passing `mover` (player who moved) as `color` to `gen_chariot` after `apply_move()` flips the turn. For red: `mover=+1`, but the chariot is at `to_sq` on the board, and `belongs_to(chariot=+5, color=+1) = True` means the chariot is treated as an ALLY and stops immediately.
- **Fix:** Derive color from the piece's sign: `piece_color = 1 if piece > 0 else -1`
- **Files modified:** `src/xiangqi/engine/repetition.py`
- **Commit:** `008a2ef`

**6. [Rule 1 - Bug] `_detect_chase` wrong `enemy` calculation**
- **Found during:** Task 7 (investigation)
- **Issue:** `enemy = -piece_color` where `piece_color` is the sign of the piece (+1/-1) — this happens to work numerically but is semantically wrong. Correct formula: `enemy = -new_state.turn` (the opponent of the player who just moved, i.e., who is now to move).
- **Fix:** Changed to `enemy = -new_state.turn`
- **Files modified:** `src/xiangqi/engine/repetition.py`
- **Commit:** `008a2ef`

## Deferred Issues

None.

## Auth Gates

None.

## Commits

| Hash | Message |
|------|---------|
| `ed1cfdb` | fix(03): address 2 plan checker blockers |
| `f1f789e` | feat(03): add endgame.py with get_game_result() and repetition.py with PerpetitionState |
| `ce36fc2` | feat(03): add RepetitionState.update() method for perpetual-rule tracking |
| `8a33424` | refactor(03): convert rules.py to thin re-export shim, add `__all__` to legal/state |
| `213cf07` | test(03): add test_endgame.py covering END-01/END-02 boundary cases |
| `008a2ef` | fix(03): correct _detect_chase move encoding and enemy color bugs |

## Self-Check

- [x] All 132 tests pass
- [x] `endgame.py` exists with `get_game_result`
- [x] `repetition.py` exists with `RepetitionState`, `check_repetition`, `check_long_check`, `check_long_chase`
- [x] `rules.py` is a thin re-export shim
- [x] `legal.py` has `_generals_face_each_other` and `__all__`
- [x] `state.py` has `__all__`
- [x] `tests/test_endgame.py` covers END-01/END-02
- [x] `tests/test_repetition.py` covers END-03/END-04
- [x] All commits present in git log
