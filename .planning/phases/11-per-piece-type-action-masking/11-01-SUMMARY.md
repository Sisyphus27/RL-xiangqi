---
phase: 11-per-piece-type-action-masking
plan: 01
subsystem: rl
tags: [gymnasium, action-masking, reward-signal, numpy]

# Dependency graph
requires:
  - phase: 10-observation-encoding-alpha-planes
    provides: XiangqiEnv base class with step/reset, observation encoding, _build_legal_mask, _build_piece_masks
provides:
  - get_legal_mask(player) public method for full legal move mask
  - get_piece_legal_mask(piece_type, player) public method for per-type mask
  - Fixed _compute_reward with correct sign and dynamic soldier river-crossing value
affects: [11-02, testing, multi-agent-training]

# Tech tracking
tech-stack:
  added: []
  patterns: [public-api-wrapping-internal-methods, dynamic-piece-value-by-position]

key-files:
  created: []
  modified:
    - src/xiangqi/rl/env.py

key-decisions:
  - "Public API methods wrap existing internal methods per D-05"
  - "Non-current player returns all-zero mask (no error) per D-03/D-04"
  - "Reward sign corrected: captured<0 (Black piece) = positive reward for Red"
  - "Soldier dynamic value: pre-river=1, post-river=2 per D-01"

patterns-established:
  - "Public API wrapping: public methods delegate to internal _build_* methods with player validation"
  - "Dynamic piece values: position-dependent piece valuation in _compute_reward"

requirements-completed: [R4, R5]

# Metrics
duration: 5min
completed: 2026-03-28
---

# Phase 11 Plan 01: Action Masking API and Reward Fix Summary

**Public action masking API (get_legal_mask, get_piece_legal_mask) and fixed reward signal with correct sign and dynamic soldier river-crossing value**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-28T02:56:17Z
- **Completed:** 2026-03-28T03:01:21Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments
- Added `get_legal_mask(player)` and `get_piece_legal_mask(piece_type, player)` public API methods for multi-agent RL training
- Fixed reward sign inversion bug: Red capturing Black pieces now correctly gives positive reward
- Added dynamic soldier value based on river-crossing status (pre-river=1, post-river=2)
- All 21 existing tests continue to pass with no regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Add get_legal_mask and get_piece_legal_mask public API methods** - `6ade68b` (feat)
2. **Task 2: Fix _compute_reward sign bug and add soldier river-crossing value** - `1af0654` (fix)

## Files Created/Modified
- `src/xiangqi/rl/env.py` - Added two public methods (get_legal_mask, get_piece_legal_mask) and rewrote _compute_reward with to_sq parameter, corrected sign logic, and dynamic soldier value

## Decisions Made
- Followed D-05: public methods wrap existing `_build_legal_mask()` and `_build_piece_masks()` without modifying internals
- Followed D-03/D-04: non-current player and invalid piece_type return all-zero masks (no errors raised)
- Followed D-01: soldier value is position-dependent (row-based river-crossing check via `to_sq // 9`)
- Kept PIECE_VALUES dict key 7 (soldier=1) as static fallback; dynamic path overrides it when to_sq >= 0

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Worktree initially lacked the `src/xiangqi/rl/` directory (branch was behind v0.3-in-progress); resolved by merging the v0.3 branch into worktree before starting execution.

## Next Phase Readiness
- Ready for Plan 02 (testing phase) which will add test coverage for the public API and reward fixes
- The public API is immediately usable by multi-agent RL training code

---
*Phase: 11-per-piece-type-action-masking*
*Completed: 2026-03-28*

## Self-Check: PASSED
