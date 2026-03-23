---
status: complete
phase: 03-endgame-detection
source: 03-01-SUMMARY.md
started: 2026-03-20T21:30:00+08:00
updated: 2026-03-20T21:40:00+08:00
---

## Current Test

[testing complete]

number: 14
name: Long chase fires before checkmate in priority order
expected: |
  State with 4+ chase entries AND zero legal moves (checkmate position)
  returns 'BLACK_WINS' (long chase fires before the no-legal-moves check).
awaiting: user response

## Tests

### 1. Checkmate — red has 0 legal moves while in check
expected: get_game_result(state) returns 'BLACK_WINS' when red has no legal moves while the red king is in check (classic double-chariot checkmate).
result: pass

### 2. Checkmate — black has 0 legal moves while in check
expected: get_game_result(state) returns 'RED_WINS' when black has no legal moves while the black king is in check.
result: pass

### 3. Stalemate/困毙 — zero legal moves = opponent wins
expected: get_game_result(state) returns 'BLACK_WINS' when red has zero legal moves (no legal moves regardless of whether king is in check — 困毙 = loss in Xiangqi).
result: pass

### 4. Starting position — 44 legal moves = IN_PROGRESS
expected: get_game_result(starting_state) returns 'IN_PROGRESS' (starting position has 44 legal moves).
result: pass

### 5. Repetition draw — same position hash appears 3x
expected: get_game_result(state) returns 'DRAW' when a position hash appears 3x in zobrist_hash_history (END-04, non-consecutive).
result: pass

### 6. Long check draw — 4 consecutive checking moves
expected: get_game_result(state, rep_state) returns 'DRAW' when consecutive_check_count >= 4 (END-03长将).
result: pass

### 7. Long chase — same (att_sq, tgt_sq) x4 = chaser loses
expected: get_game_result(state, rep_state) returns 'BLACK_WINS' when red chases same target 4 times; returns 'RED_WINS' when black chases same target 4 times (END-03长捉, chaser loses not draw).
result: pass

### 8. Priority order — repetition fires before checkmate
expected: Position with 3x repetition AND checkmate position returns 'DRAW' (repetition checked before checkmate per priority order).
result: pass

### 9. RepetitionState.update() — increments on checking move
expected: After a move that gives check, rep_state.consecutive_check_count increments from 0 to 1.
result: pass

### 10. RepetitionState.update() — resets on non-checking move
expected: After a non-checking move, rep_state.consecutive_check_count resets to 0.
result: pass

### 11. RepetitionState.update() — resets chase on meaningful progress
expected: Moving to a new attacking square (new att_sq not seen in current chase_seq) resets the chase sequence (meaningful progress = break).
result: pass

### 12. RepetitionState.reset() — zeroes all fields
expected: Calling reset() on a RepetitionState zeroes consecutive_check_count, chase_seq, and last_chasing_color.
result: pass

### 13. Long check via get_game_result priority
expected: get_game_result(state, rep_state) returns 'DRAW' when rep_state has consecutive_check_count >= 4 (long check fires in priority order).
result: pass

### 14. Long chase fires before checkmate in priority order
expected: State with 4+ chase entries AND zero legal moves returns 'BLACK_WINS' (long chase fires before checkmate check).
result: pass

## Summary

total: 14
passed: 13
issues: 0
pending: 0
skipped: 0

## Gaps

[none yet]
