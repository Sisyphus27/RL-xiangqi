---
phase: 11-per-piece-type-action-masking
plan: 02
subsystem: rl
tags: [testing, reward-signal, action-masking, numpy]

# Dependency graph
requires:
  - phase: 11-01
    provides: get_legal_mask, get_piece_legal_mask, fixed _compute_reward
provides:
  - 8 test functions covering R4 and R5 requirements
affects: [verification, regression-safety]

# Tech tracking
tech-stack:
  added: []
  patterns: [direct-method-testing, positional-reward-verification]

key-files:
  created: []
  modified:
    - tests/test_rl.py

key-decisions:
  - "Tests use direct _compute_reward calls with known piece values for deterministic verification"
  - "Soldier river-crossing tests use explicit square indices for pre/post-river positions"

# Self-Check: PASSED

## What was built

8 test functions added to tests/test_rl.py:

**Task 1 (R4 Public API — 4 tests):**
1. `test_get_legal_mask_current_player` — verifies shape (8100,), dtype float32, matches internal mask
2. `test_get_legal_mask_non_current_player` — verifies all-zero for non-current player
3. `test_get_piece_legal_mask_current_player` — verifies per-type mask, matches internal, invalid piece_type returns zero
4. `test_get_piece_legal_mask_non_current_player` — verifies all-zero for non-current player

**Task 2 (R5 Reward Signal — 4 tests):**
5. `test_material_capture_reward` — verifies sign fix: Red captures Black Horse = +0.04, Black captures Red Horse = -0.04, plus Chariot/Cannon/no-capture
6. `test_soldier_pre_river_value` — verifies pre-river soldier value = 1 (reward ±0.01)
7. `test_soldier_post_river_value` — verifies post-river soldier value = 2 (reward ±0.02)
8. `test_reward_sign_correct` — verifies sign correctness: positive for Red captures Black, negative for Black captures Red

## Deviations

None. All 8 tests follow the plan exactly.

## Test Results

```
29 passed in 0.50s
```

- 21 existing tests: all pass
- 4 R4 public API tests: all pass
- 4 R5 reward signal tests: all pass
