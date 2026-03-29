---
phase: 10-observation-encoding-alpha-planes
plan: "01"
subsystem: rl
tags: [numpy, gymnasium, observation-encoding, canonical-rotation, alphazero-planes]

# Dependency graph
requires:
  - phase: 09-xiangqi-env-core
    provides: XiangqiEnv gym.Env with reset/step/observation/action_masks
provides:
  - Fixed _canonical_board() with piece value negation for black-to-move
  - 4 regression tests validating all 16-channel observation encoding behaviors
  - Verified FEN encodings and action encodings for midgame test positions
affects: [11-per-piece-type-action-masking, 12-self-play-e2e]

# Tech tracking
tech-stack:
  added: []
  patterns: [canonical-board-negation, zobrist-repetition-tracking, halfmove-normalization]

key-files:
  created: []
  modified:
    - src/xiangqi/rl/env.py
    - tests/test_rl.py

key-decisions:
  - "Used different-file chariot positions (7r1/.../R8) for repetition and canonical rotation tests to avoid same-file capture complications"
  - "Used Red King + Cannon + Black King FEN for halfmove test to ensure enough legal moves without stalemate"
  - "Starting position repetition channel is 1/3 (count=1 normalized), not 0.0"

patterns-established:
  - "Canonical rotation: -np.rot90(board, k=2) negates piece values so active player always in channels 0-6"
  - "Test FENs: use 10-rank format with correct piece column positions (9 columns per rank)"
  - "Repetition cycle: place chariots on different files, use forward/back 4-move cycle"

requirements-completed: [R3]

# Metrics
duration: 12min
completed: 2026-03-28
---

# Phase 10 Plan 01: Canonical Rotation Bug Fix + 16-Channel Validation Tests

**Fixed canonical rotation with piece value negation and validated all 16 AlphaZero board plane channels with corrected FEN/action encodings**

## Performance

- **Duration:** 12 min
- **Started:** 2026-03-28T01:25:01Z
- **Completed:** 2026-03-28T01:37:39Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Fixed `_canonical_board()` to negate piece values after 180-degree rotation so active player's pieces always appear in channels 0-6
- Removed dead code (`engine_piece`, `piece_val` variables in `_build_piece_masks()`)
- Added 4 comprehensive test functions validating: starting piece distribution (32 pieces across 14 channels), canonical rotation for black-to-move, repetition channel normalization (2-fold=2/3, 4-fold=1.0), and halfmove clock normalization (0-100 range)
- Discovered and corrected incorrect FEN encodings and action encodings in the plan

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix canonical rotation bug + remove unused variable** - `aa7a469` (fix)
2. **Task 2: Add 4 observation encoding tests** - `5de7956` (test)

## Files Created/Modified
- `src/xiangqi/rl/env.py` - Fixed `_canonical_board()` negation, removed dead code from `_build_piece_masks()`
- `tests/test_rl.py` - Added 4 new test functions for 16-channel observation encoding validation

## Decisions Made
- Used different-file chariot positions (FEN `7r1/9/.../R8`) instead of same-file positions for repetition and canonical rotation tests, avoiding same-file capture complications that prevented cycle completion
- Used Red King + Cannon + Black King FEN (`3k5/.../C3K4`) for halfmove test since bare-kings-on-e-file creates flying general (stalemate) with zero legal moves
- Starting position repetition channel correctly shows 1/3 (first occurrence of current hash), not 0.0

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed incorrect FEN encodings in test functions**
- **Found during:** Task 2 (test writing)
- **Issue:** Plan provided FEN `1r1a1R1/9/.../9` which only described row 0 (7 positions, not 9 columns) and placed Red Chariot on row 0 instead of row 9. Plan also provided FEN `r9/9/.../R9/9/.../9` with 19 slashes (20 ranks instead of 10). Plan used `9/9/9/9/4K4/9/9/9/9/4k4` for halfmove test which has kings on same file (flying general = stalemate, zero legal moves).
- **Fix:** Corrected FENs: used `7r1/9/9/9/9/9/9/9/9/R8` for canonical rotation and repetition tests (10-rank format, chariots on different files), and `3k5/9/9/9/9/9/9/9/9/C3K4` for halfmove test (kings on different files with cannon for legal move variety).
- **Files modified:** tests/test_rl.py
- **Verification:** All 4 tests pass, full test_rl.py suite green
- **Committed in:** 5de7956 (Task 2 commit)

**2. [Rule 1 - Bug] Fixed incorrect action encodings in repetition test**
- **Found during:** Task 2 (test writing)
- **Issue:** Plan used action formula `72*90+81=6561` for Red a1->a2 but the correct formula is `from_sq*90+to_sq = 81*90+72=7362`. Plan also used a10=sq=4 when a10=(0,0)=sq=0. The plan's cycle required captures which prevented returning to the starting position.
- **Fix:** Used correct action encoding `from_sq*90+to_sq` with different-file chariot cycle (forward/back, no captures needed): Red (9,0)->(8,0), Black (0,7)->(1,7), Red (8,0)->(9,0), Black (1,7)->(0,7). Actions: 7362, 646, 6561, 1447.
- **Files modified:** tests/test_rl.py
- **Verification:** Repetition test passes with correct 2-fold (2/3) and 4-fold (1.0) values
- **Committed in:** 5de7956 (Task 2 commit)

**3. [Rule 1 - Bug] Fixed halfmove test to re-fetch legal actions per step**
- **Found during:** Task 2 (test writing)
- **Issue:** Plan's test computed legal_actions once and reused them across all 10 steps via modular indexing. After each step, the legal action set changes, so stale legal_actions produced illegal moves or the same move repeatedly without actually advancing the halfmove clock.
- **Fix:** Re-fetch legal_mask and legal_actions inside the loop on each iteration, always picking the first available legal action.
- **Files modified:** tests/test_rl.py
- **Verification:** Halfmove clock correctly increments to 10 after 10 non-capture moves
- **Committed in:** 5de7956 (Task 2 commit)

**4. [Rule 2 - Missing Critical] Corrected starting piece count from 14 to 32**
- **Found during:** Task 2 (test writing)
- **Issue:** Plan's must_haves stated "14 pieces at starting position" and test code checked `pieces_per_channel.sum() == 14`. Xiangqi starting position has 32 pieces (16 per side, 7 types with counts [1,2,2,2,2,2,5] per side).
- **Fix:** Changed total pieces assertion to 32. Also corrected channel 14 assertion from 0.0 to 1/3 (first occurrence of hash is count=1, normalized=1/3).
- **Files modified:** tests/test_rl.py
- **Verification:** Starting position test passes with correct counts
- **Committed in:** 5de7956 (Task 2 commit)

---

**Total deviations:** 4 auto-fixed (4 bugs from incorrect plan data)
**Impact on plan:** All auto-fixes were necessary because the plan contained incorrect FEN encodings, wrong action encoding formulas, and wrong piece counts. Tests were rewritten from scratch with verified-correct values. No scope creep -- all tests validate the same intended behaviors.

## Issues Encountered
- Pre-existing test failures in test_constants.py (5 tests) and test_game_controller.py (2 tests) due to Phase 09's from_fen() returning 3 values instead of 2 -- out of scope for Phase 10-01

## Known Stubs
None - all data flows are fully wired.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Canonical rotation fix enables correct observation encoding for both red-to-move and black-to-move positions
- All 16 channels validated: piece types (0-13), repetition (14), halfmove (15)
- Ready for Phase 10 Plan 02 (gap closure plan for remaining issues)
- Pre-existing test failures in test_constants.py need to be addressed in a future phase

## Self-Check: PASSED

All claimed files exist, all commit hashes verified, all acceptance criteria confirmed.

---
*Phase: 10-observation-encoding-alpha-planes*
*Completed: 2026-03-28*
