---
phase: "09-xiangqi-env-core"
plan: "03"
subsystem: "rl"
tags: ["gymnasium", "rl-environment", "xiangqi", "endgame"]

dependency_graph:
  requires:
    - phase: "09-02"
      provides: "XiangqiEnv.step() with terminal detection"
  provides:
    - "SyncVectorEnv integration test (R8)"
    - "50-move rule detection (R6)"
    - "halfmove_clock FEN parsing"
  affects: ["Phase 10 (AlphaZero encoding)", "Phase 11 (action masking)", "Phase 12 (self-play)"]

tech_stack:
  added: []
  patterns: ["gymnasium.vector.SyncVectorEnv", "50-move rule draw condition", "FEN halfmove_clock parsing"]

key-files:
  created: []
  modified:
    - "src/xiangqi/engine/constants.py"
    - "src/xiangqi/engine/state.py"
    - "src/xiangqi/engine/endgame.py"
    - "tests/test_rl.py"

key-decisions:
  - "50-move rule check added at priority 2 in get_game_result(), after repetition but before long check"
  - "FEN parser returns (board, turn, halfmove_clock) tuple to preserve halfmove info"

requirements-completed: ["R6", "R8"]

metrics:
  duration: "~4 min"
  completed: "2026-03-26"
---

# Phase 09 Plan 03 Summary: SyncVectorEnv and 50-Move Rule Validation

**SyncVectorEnv with 2 parallel envs runs 20+ self-play steps without deadlock; 50-move rule (halfmove_clock >= 100) triggers DRAW with terminated=True and reward=0.0**

## Performance

- **Duration:** ~4 min
- **Started:** 2026-03-26T13:43:56Z
- **Completed:** 2026-03-26T13:47:18Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Comprehensive SyncVectorEnv integration test with 20-step self-play verification
- 50-move rule implemented in get_game_result() (halfmove_clock >= 100 -> DRAW)
- FEN parser now correctly extracts and returns halfmove_clock (was always hardcoded to 0)
- Both R6 (50-move rule) and R8 (SyncVectorEnv) validation requirements satisfied

## Task Commits

1. **Task 1: SyncVectorEnv integration test** - `559a820` (feat)
2. **Task 2: 50-move rule test** - `559a820` (same commit as Task 1)

**Plan metadata:** `559a820` (docs: complete plan)

## Files Created/Modified

- `src/xiangqi/engine/constants.py` - from_fen() now returns halfmove_clock from FEN 5th field
- `src/xiangqi/engine/state.py` - XiangqiState.from_fen() uses parsed halfmove_clock instead of 0
- `src/xiangqi/engine/endgame.py` - get_game_result() now checks halfmove_clock >= 100 for DRAW
- `tests/test_rl.py` - Updated test_sync_vector_env (20-step test) and test_50_move_rule

## Decisions Made

- 50-move rule check inserted at priority 2 in get_game_result(), after threefold repetition check but before long check/chase checks
- FEN parser returns 3-tuple (board, turn, halfmove_clock) - breaking change to constants.py from_fen() interface but necessary for correctness

## Deviations from Plan

None - plan executed exactly as written.

## Auto-fixed Issues

**1. [Rule 2 - Missing Critical] 50-move rule not implemented in get_game_result()**
- **Found during:** Task 2 (50-move rule test implementation)
- **Issue:** get_game_result() never checked halfmove_clock >= 100 for DRAW. The field was tracked but never used for draw detection.
- **Fix:** Added `if state.halfmove_clock >= 100: return 'DRAW'` check at priority position 2
- **Files modified:** src/xiangqi/engine/endgame.py
- **Verification:** test_50_move_rule passes with terminated=True, reward=0.0
- **Committed in:** `559a820` (Task 2 commit)

**2. [Rule 2 - Missing Critical] FEN parser ignored halfmove_clock field**
- **Found during:** Task 2 (50-move rule test implementation)
- **Issue:** from_fen() returned only (board, turn), ignoring the 5th FEN field containing halfmove_clock. XiangqiState.from_fen() always set halfmove_clock=0.
- **Fix:** Updated from_fen() to parse and return halfmove_clock; XiangqiState.from_fen() uses the parsed value
- **Files modified:** src/xiangqi/engine/constants.py, src/xiangqi/engine/state.py
- **Verification:** FEN with halfmove=120 correctly sets engine.state.halfmove_clock=120
- **Committed in:** `559a820` (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (both Rule 2 - missing critical functionality)
**Impact on plan:** Both auto-fixes essential for correctness. 50-move rule is a standard Chinese chess draw condition; FEN halfmove parsing is required for test reproducibility.

## Issues Encountered

None - both tasks executed cleanly after auto-fixes were applied.

## Known Stubs

None identified.

## Auth Gates

None - no authentication required.

## Next Phase Readiness

- Phase 09 complete (all 3 plans finished)
- XiangqiEnv core with gym.Env interface, step/reset, 50-move rule, and SyncVectorEnv support ready
- Phase 10 (AlphaZero board planes encoding) can now proceed

---
*Phase: 09-xiangqi-env-core*
*Completed: 2026-03-26*
