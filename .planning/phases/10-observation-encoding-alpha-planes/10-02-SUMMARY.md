---
phase: 10-observation-encoding-alpha-planes
plan: "02"
subsystem: testing
tags: [pytest, gymnasium, observation-encoding, fen, repetition, halfmove-clock]

# Dependency graph
requires:
  - phase: 10-01
    provides: "Canonical rotation fix and 4 initial channel validation tests"
provides:
  - "Fixed test_observation_repetition_channel with a-file chariot shuttle FEN"
  - "Fixed test_observation_halfmove_clock_channel with kings-in-palace FEN"
  - "All 16 observation channels now validated with passing tests"
affects: [10-observation-encoding-alpha-planes, 11-per-piece-type-action-masking]

# Tech tracking
tech-stack:
  added: []
  patterns: [a-file chariot shuttle for repetition testing, bare-kings FEN for halfmove testing]

key-files:
  created: []
  modified:
    - tests/test_rl.py

key-decisions:
  - "A-file chariot shuttle (r8/.../R8) avoids capture, guarantees hash recurrence for repetition test"
  - "Bare-kings FEN (4k4/.../4K4) places generals in correct palaces for legal move availability"
  - "Re-fetch legal_mask inside loop to handle changing move lists after each step"

patterns-established:
  - "Dynamic legal move fetching per step: env._get_info()['legal_mask'] inside loop"

requirements-completed: [R3]

# Metrics
duration: 5min
completed: 2026-03-28
---

# Phase 10 Plan 02: Gap Closure Summary

**Fixed repetition channel test (a-file chariot shuttle) and halfmove clock test (kings in correct palaces) -- all 21 test_rl.py tests passing**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-28T01:41:51Z
- **Completed:** 2026-03-28T01:46:54Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments
- Fixed test_observation_repetition_channel: corrected FEN to `r8/9/.../R8` with both chariots on a-file, non-capture shuttle actions (7362, 9, 6561, 810), correct 2-fold and 3-fold repetition assertions
- Fixed test_observation_halfmove_clock_channel: corrected FEN to `4k4/9/.../4K4` with kings in correct palaces, dynamic legal move fetching per step, 10-step halfmove accumulation assertion

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix test_observation_repetition_channel** - `ac57f42` (test)
2. **Task 2: Fix test_observation_halfmove_clock_channel** - `6e5f6bd` (test)

## Files Created/Modified
- `tests/test_rl.py` - Replaced repetition test body (FEN + actions + assertions) and halfmove test body (FEN + legal move fetching)

## Decisions Made
- A-file chariot shuttle ensures no capture occurs, so hash returns exactly to starting position after each 4-move cycle
- Kings-in-palace FEN guarantees each general has legal moves (sideways within palace), avoiding ZeroDivisionError
- Re-fetching legal_mask each step via `env._get_info()["legal_mask"]` handles changing move lists correctly

## Deviations from Plan

### Note on Verification Criteria

The plan's grep check `grep "9/9/9/9/4K4/9/9/9/9/4k4" tests/test_rl.py` returns 0 matches, but that FEN substring appears in the pre-existing `test_repetition_draw()` function (Phase 09, line 121), which was not in scope for this plan. The halfmove test no longer uses that FEN. This is a minor over-specification in the plan's verification criteria, not a code issue.

**Total deviations:** 0 auto-fixed
**Impact on plan:** None -- both tests pass, all criteria met.

## Issues Encountered
None - plan executed exactly as specified.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 16 observation channels validated with passing tests (Phase 10 complete)
- Ready for Phase 11: Per-piece-type action masking
- Pre-existing test failures in test_constants.py (from_fen signature) and test_game_controller.py (Qt event loop) are out of scope for this plan

---
*Phase: 10-observation-encoding-alpha-planes*
*Completed: 2026-03-28*

## Self-Check: PASSED

- FOUND: tests/test_rl.py
- FOUND: ac57f42 (Task 1 commit)
- FOUND: 6e5f6bd (Task 2 commit)
- FOUND: 10-02-SUMMARY.md
