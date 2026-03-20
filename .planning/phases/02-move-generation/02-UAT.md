---
status: diagnosed
phase: 02-move-generation
source:
  - 02-01-SUMmary.md
  - 02-02-SUMMARY.md
started: 2026-03-20T00:00:00Z
updated: 2026-03-20T12:50:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Starting position legal move count
expected: All 66 unit tests pass. Perft(1)=44, Perft(2)=1,920.
result: pass

### 2. Perft depth 3 accuracy
expected: Perft(3) on starting position returns 79,666 nodes.
Currently failing: engine returns 77,508 (missing 2,158 nodes).
result: issue
reported: "perft(3): expected 79666, got 77508"
severity: major

### 3. Perft depth 4 accuracy
expected: Perft(4) on starting position returns 3,290,240 nodes.
Currently failing: engine returns 3,112,545 (missing 177,695 nodes).
result: issue
reported: "perft(4): expected 3290240, got 3112545"
severity: major

### 4. All piece move generators
expected: All 32 move generator tests pass. Each piece type (chariot, horse, cannon, advisor, elephant, soldier, general) generates correct pseudo-legal moves.
result: pass


## Summary

total: 4
passed: 2
issues: 2
pending: 0
skipped: 0

## Gaps

- truth: "Perft(3) on starting position returns 79,666 nodes (CPW-verified reference value)"
  status: failed
  reason: "perft(3): expected 79666, got 77508 (missing 2,158 nodes)"
  severity: major
  test: 2
  root_cause: "gen_soldier in moves.py line 186 has INVERTED forward direction. `forward_dr = +1 if color == +1 else -1` should be `forward_dr = -1 if color == +1 else +1`. In standard xiangqi (black at top row 0, red at bottom row 9): red advances toward row 0 (forward_dr=-1), black toward row 9 (forward_dr=+1). Current code reverses both. Monkey-patch test confirms: perft(3)=79666 with corrected direction."
  artifacts:
    - path: "src/xiangqi/engine/moves.py"
      issue: "Line 186: forward_dr = +1 if color == +1 else -1 — inverted for both colors. Red pawns move toward their own home (row 9) instead of enemy home (row 0). Black pawns move toward their own home (row 0) instead of enemy home (row 9)."
    - path: "tests/test_moves.py"
      issue: "test_red_soldier_pre_river and test_red_soldier_crossed_river encode the wrong direction (same bug as implementation). Both pass but validate incorrect behavior."
  missing:
    - "Flip forward_dr in gen_soldier: `forward_dr = -1 if color == +1 else +1`"
    - "Update test_moves.py soldier test cases to validate correct forward direction"
    - "Run perft(1)=44, perft(2)=1920, perft(3)=79666 to confirm fix"
  debug_session: ".planning/debug/perft-depth3-bug.md"
- truth: "Perft(4) on starting position returns 3,290,240 nodes (CPW-verified reference value)"
  status: failed
  reason: "perft(4): expected 3290240, got 3112545 (missing 177,695 nodes)"
  severity: major
  test: 3
  root_cause: "Same root cause as perft(3): gen_soldier inverted direction. Fixing forward_dr also fixes perft(4)."
  artifacts:
    - path: "src/xiangqi/engine/moves.py"
      issue: "Line 186: forward_dr inverted (same as perft(3) bug)"
  missing:
    - "Flip forward_dr in gen_soldier (fixes both perft(3) and perft(4))"
    - "Run perft(4)=3290240 to confirm"
  debug_session: ".planning/debug/perft-depth3-bug.md"