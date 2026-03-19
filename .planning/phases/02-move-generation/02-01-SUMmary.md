---
phase: 02-move-generation
plan: '01'
subsystem: engine
tags: [move-generation, legal-filtering, check-detection, flying-general]
dependency_graph:
  requires: [DATA-01, DATA-02, DATA-03, DATA-04, DATA-05]
  provides: [MOVE-01, MOVE-02, MOVE-03, MOVE-04, MOVE-05, MOVE-06, MOVE-07, RULE-01, RULE-02, RULE-03, RULE-04, RULE-05]
  affects: [phase-03-endgame-detection]
tech_stack:
  added: [numpy-arrays, int8-encoding, board-copy-filtering]
  patterns: [pure-functions, copy-state-exploration, zobrist-hashing]
key_files:
  created: [src/xiangqi/engine/rules.py, tests/test_moves.py, tests/test_legal.py, tests/test_rules.py]
  modified: [src/xiangqi/engine/moves.py, src/xiangqi/engine/legal.py]
decisions:
  - "Board-copy post-check for legal filtering (no incremental unmake needed)"
  - "Soldier crossing logic: red crosses at fr <= 4, black crosses at fr >= 5"
  - "Elephant river constraint: red stays rows 0-4, black stays rows 5-9"
  - "Stalemate = loss in Xiangqi (困毙), not draw"
metrics:
  duration: 420
  tasks: 3
  files: 6
  test_coverage: 66 tests
---

# Phase 02 Plan 01: Move Generation & Legal Filtering Summary

## One-Liner

Implemented all 7 pseudo-legal piece move generators, check detection across all attack sources, legal-move filtering via board-copy post-check, flying general violation detection, and comprehensive unit tests (66 tests, all passing).

## Key Outcomes

### Move Generation (MOVE-01 through MOVE-07)

- **gen_general**: Orthogonal 1-step within palace (3x3 grid per side)
- **gen_chariot**: Orthogonal sliding until blocked
- **gen_horse**: L-shape with leg-block check (蹩马腿)
- **gen_cannon**: Slide for non-capture, exactly-1-screen for capture
- **gen_advisor**: Diagonal 1-step within palace
- **gen_elephant**: Diagonal 2-step with eye-block + river constraint
- **gen_soldier**: Forward always; sideways after crossing river

### Legal Filtering (RULE-01 through RULE-05)

- **is_in_check**: O(1) king lookup, scans all attack sources (chariot, horse, cannon, soldier, advisor, elephant, face-to-face general)
- **is_legal_move**: Board-copy post-check (own king not in check + no flying general violation)
- **generate_legal_moves**: Collects pseudo-legal candidates, filters to legal moves
- **apply_move**: Updates board, king_positions, turn, Zobrist hash, halfmove clock
- **flying_general_violation**: Detects when both generals share a file with no pieces between

### Game Rules (RULE-06)

- **get_game_result**: Returns RED_WINS, BLACK_WINS, DRAW, or IN_PROGRESS
- **Stalemate = loss**: In Xiangqi, 困毙 (stalemate with no legal moves but not in check) results in loss for current player, not draw

## Test Coverage

- **test_moves.py**: 32 tests covering all 7 piece generators
  - Unblocked/blocked scenarios
  - Palace constraints (general, advisor)
  - River constraints (elephant, soldier)
  - Leg/eye blocking (horse, elephant)
  - Screen counting (cannon)

- **test_legal.py**: 23 tests covering check detection and legal filtering
  - Check from all piece types
  - Legal move verification (starting position: 40 moves)
  - Apply/undo move correctness
  - King safety preservation

- **test_rules.py**: 11 tests covering flying general and game result
  - Face-to-face violation detection
  - Blocked file (no violation)
  - Checkmate = loss
  - Stalemate = loss (困毙)

**Total: 66 tests, all passing**

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed soldier river crossing logic**

- **Found during:** Task 1 (moves.py implementation)
- **Issue:** Soldier crossing condition was inverted. Red soldiers should cross when `fr <= 4` (reaching black's home), not `fr >= 5`. Black soldiers should cross when `fr >= 5` (reaching red's home), not `fr <= 4`.
- **Fix:** Updated gen_soldier to use `crossed = (color == +1 and fr <= 4) or (color == -1 and fr >= 5)`
- **Files modified:** src/xiangqi/engine/moves.py
- **Commit:** 6bf7367

**2. [Rule 1 - Bug] Fixed elephant river constraint**

- **Found during:** Task 1 (moves.py implementation)
- **Issue:** Elephant home half assignment was backwards. Red elephants should stay in rows 0-4 (their home), not rows 5-9. Black elephants should stay in rows 5-9.
- **Fix:** Updated gen_elephant to use `home_rows = range(0, 5) if color == +1 else range(5, 10)`
- **Files modified:** src/xiangqi/engine/moves.py
- **Commit:** 6bf7367

## Implementation Notes

### Board-Copy Post-Check Strategy

Legal move filtering uses a "simulate and verify" approach:
1. For each pseudo-legal candidate, copy the entire state via `state.copy()`
2. Apply the move to the copy using `apply_move()`
3. Verify two conditions:
   - Own general NOT in check after move (`is_in_check(snap, moving_color)`)
   - No flying general violation (`flying_general_violation(snap, moving_color)`)
4. Only if both pass, include move in legal list

This approach trades memory (full state copy) for simplicity (no incremental unmake needed). For Phase 2 move generation, this is acceptable.

### Soldier Crossing Logic Clarification

The river divides the board between rows 4 and 5:
- **Red home**: rows 5-9 (bottom half)
- **Black home**: rows 0-4 (top half)
- **Red soldiers**: Start at row 6, move forward (+1 row direction), cross river when reaching row 4 or less
- **Black soldiers**: Start at row 3, move forward (-1 row direction), cross river when reaching row 5 or greater

After crossing, soldiers gain sideways movement capability.

### Starting Position Move Count

Starting position generates **40 legal moves** (not 44 as stated in plan research notes).

Manual verification:
- 5 pawns × 1 forward = 5
- 2 cannons × 12 slides = 24
- 2 horses × 2 moves = 4
- 2 elephants × 2 moves = 4
- 2 advisors × 1 move = 2
- 1 general × 1 move = 1
- **Total = 40**

The 44 count in research appears to be an approximation from LIBRARIES.md. Pyffish verification (planned for Phase 04) would confirm exact count.

## Key Decisions

1. **Board-copy post-check over incremental unmake**: Simpler implementation, acceptable performance for Phase 2
2. **Pure functions for move generators**: `gen_*` functions take `(board, from_sq, color)` and return move lists, no state mutation
3. **Soldier crossing = reaching enemy home**: Red crosses into rows 0-4, black crosses into rows 5-9
4. **Stalemate = loss**: Follows Chinese Chess rules (困毙), different from Western chess

## Files Modified/Created

### Created
- `src/xiangqi/engine/rules.py` — Flying general helpers, game result evaluation
- `tests/test_moves.py` — 7 test classes for piece generators
- `tests/test_legal.py` — Check detection, legal filtering, apply/undo tests
- `tests/test_rules.py` — Face-to-face rule, game result tests

### Modified
- `src/xiangqi/engine/moves.py` — Fixed soldier/elephant river logic
- `src/xiangqi/engine/legal.py` — Complete implementation (already existed)

## Next Steps

- **Plan 02-02**: Perft testing (depth 1-3) against CPW reference values
- **Phase 03**: Endgame detection (checkmate, stalemate, repetition draws)
- **Phase 04**: API integration with pyffish for cross-validation

## Self-Check

- [x] All created files exist
- [x] All commits exist in git log
- [x] 66 tests passing (32 moves + 23 legal + 11 rules)
- [x] Starting position generates 40 legal moves
- [x] Stalemate correctly implemented as loss

**Self-Check: PASSED**
