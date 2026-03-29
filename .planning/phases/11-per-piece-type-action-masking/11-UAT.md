---
status: complete
phase: 11-per-piece-type-action-masking
source: 11-01-SUMMARY.md, 11-02-SUMMARY.md
started: 2026-03-28T15:50:00+08:00
updated: 2026-03-28T16:05:00+08:00
---

## Current Test

[testing complete]

## Tests

### 1. get_legal_mask API for current player
expected: Calling env.get_legal_mask(1) returns a numpy float32 array of shape (8100,) matching the internal legal mask. Non-zero entries correspond to legal moves.
result: pass

### 2. get_legal_mask for non-current player
expected: Calling env.get_legal_mask(-1) when player 1 is current returns an all-zero numpy array of shape (8100,). No error raised.
result: pass

### 3. get_piece_legal_mask per-type mask
expected: Calling env.get_piece_legal_mask(piece_type=1, player=1) returns a mask for chariots only. Calling with invalid piece_type=99 returns all zeros. Non-current player returns all zeros. No errors raised.
result: pass

### 4. Reward sign correctness
expected: Red capturing a Black piece produces a positive reward. Black capturing a Red piece produces a negative reward. No-capture moves produce 0 reward.
result: pass

### 5. Soldier dynamic river-crossing value
expected: Capturing a soldier that has NOT crossed the river yields reward proportional to value=1. Capturing a soldier that HAS crossed the river yields reward proportional to value=2. Value difference is detectable in the reward signal.
result: pass

### 6. Full test suite passes
expected: Running pytest on tests/test_rl.py shows 29 tests passed, 0 failed, 0 errors. Includes 21 existing + 4 R4 API + 4 R5 reward tests.
result: pass

## Summary

total: 6
passed: 6
issues: 0
pending: 0
skipped: 0

## Gaps

[none]
