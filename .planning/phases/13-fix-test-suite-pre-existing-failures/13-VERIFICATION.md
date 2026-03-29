---
phase: 13-fix-test-suite-pre-existing-failures
verified: 2026-03-29T10:15:00Z
status: passed
score: 3/3 must-haves verified
re_verification: false
---

# Phase 13: Fix Test Suite Pre-existing Failures Verification Report

**Phase Goal:** Fix all 7 pre-existing test failures across 2 test files (test_constants.py and test_game_controller.py). Root causes fully diagnosed: from_fen() 3-tuple mismatch and QThread race condition. Expected outcome: zero failures in full test suite.
**Verified:** 2026-03-29T10:15:00Z
**Status:** passed
**Re-verification:** No -- initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | All 5 TestStartingFen tests pass (from_fen 3-tuple unpacking) | VERIFIED | `pytest tests/test_constants.py::TestStartingFen -v` -- 5 passed in 0.02s |
| 2 | Both controller tests pass without spawning real QThreads | VERIFIED | `pytest tests/controller/test_game_controller.py -v` -- 5 passed in 0.10s; all 5 tests patch _start_ai_turn during construction |
| 3 | Full test suite is green (zero failures) | VERIFIED | `pytest -q` -- 314 passed, 1 skipped, 0 failures in 130.40s |

**Score:** 3/3 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `tests/test_constants.py` | 5 fixed TestStartingFen tests with 3-tuple from_fen unpacking | VERIFIED | All 6 from_fen calls use 3-tuple unpacking (2x `board, turn, _`, 3x `board, _, _`, 1x `board2, turn2, _`). Zero 2-value unpacking remains. |
| `tests/controller/test_game_controller.py` | 2 fixed controller tests with _start_ai_turn mocking | VERIFIED | 5 constructor-level patches (`patch.object(GameController, '_start_ai_turn')`), 2 runtime patches (`patch.object(controller, '_start_ai_turn')`). Deterministic via `controller._human_side = 1`. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `tests/test_constants.py` | `src/xiangqi/engine/constants.py::from_fen` | direct function call | WIRED | 6 calls to `from_fen()` all unpack 3 values matching `Tuple[np.ndarray, int, int]` return type |
| `tests/controller/test_game_controller.py` | `src/xiangqi/controller/game_controller.py::_start_ai_turn` | patch.object mock | WIRED | 7 patch.object references total: 5 at class level during construction, 2 at instance level wrapping _on_move_applied calls |

### Data-Flow Trace (Level 4)

Not applicable -- this is a test-fixing phase, not a data-flow phase. The artifacts are test files that verify existing production code, not components that render dynamic data.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| TestStartingFen tests pass | `python -m pytest tests/test_constants.py::TestStartingFen -v` | 5 passed in 0.02s | PASS |
| Controller tests pass | `python -m pytest tests/controller/test_game_controller.py -v` | 5 passed in 0.10s | PASS |
| Full suite green | `python -m pytest -q` | 314 passed, 1 skipped, 0 failures | PASS |
| No 2-value from_fen unpacking | `grep "board, turn = from_fen\|board, _ = from_fen(" tests/test_constants.py` | No output (0 matches) | PASS |
| Constructor thread protection in all 5 tests | `grep -c "patch.object(GameController, '_start_ai_turn')" tests/controller/test_game_controller.py` | 5 | PASS |
| Commit 552985e exists | `git show --stat 552985e` | Valid commit, 6 insertions, 6 deletions in test_constants.py | PASS |
| Commit 1a7354b exists | `git show --stat 1a7354b` | Valid commit, 47 insertions, 33 deletions in test_game_controller.py | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| FIX-01 | 13-01 | from_fen 3-tuple unpacking in test_starting_fen_parsed | SATISFIED | Line 48: `board, turn, _ = from_fen(STARTING_FEN)`, test passes |
| FIX-02 | 13-01 | from_fen 3-tuple unpacking in test_starting_fen_red_back_rank | SATISFIED | Line 55: `board, _, _ = from_fen(STARTING_FEN)`, test passes |
| FIX-03 | 13-01 | from_fen 3-tuple unpacking in test_starting_fen_black_back_rank | SATISFIED | Line 69: `board, _, _ = from_fen(STARTING_FEN)`, test passes |
| FIX-04 | 13-01 | from_fen 3-tuple unpacking in test_starting_fen_pawns | SATISFIED | Line 83: `board, _, _ = from_fen(STARTING_FEN)`, test passes |
| FIX-05 | 13-01 | from_fen 3-tuple unpacking in test_fen_roundtrip | SATISFIED | Lines 99, 105: both use 3-tuple unpacking, test passes |
| FIX-06 | 13-01 | No thread leak in test_controller_emits_turn_changed_on_user_move | SATISFIED | Constructor + runtime patch of _start_ai_turn, test passes |
| FIX-07 | 13-01 | No thread leak in test_controller_starts_ai_on_black_turn | SATISFIED | Constructor + runtime patch with mock_start.assert_called_once(), test passes |

**Note:** FIX-01 through FIX-07 are phase-local requirement IDs defined in 13-RESEARCH.md. They are not in REQUIREMENTS.md (which uses R1-R8 milestone-level IDs). All 7 IDs from the PLAN frontmatter are accounted for.

**Orphaned requirements:** None. All FIX IDs in the PLAN appear in the RESEARCH.md traceability table.

### Anti-Patterns Found

No anti-patterns detected. Scanned both modified files for:
- TODO/FIXME/placeholder comments: 0 matches
- Empty implementations (return null/{}): 0 matches
- Hardcoded empty data: 0 matches
- Console.log-only handlers: 0 matches

### Human Verification Required

None. All phase requirements are test fixes verified by automated test execution. No visual, real-time, or external service behaviors to verify.

### Gaps Summary

No gaps found. All 7 test failures have been fixed:

1. **from_fen() 3-tuple mismatch (FIX-01 through FIX-05):** All 6 `from_fen()` calls in `tests/test_constants.py` updated from 2-value to 3-value unpacking, matching the Phase 09 signature change (`def from_fen(fen: str) -> Tuple[np.ndarray, int, int]`).

2. **QThread race condition (FIX-06, FIX-07):** All 5 tests in `tests/controller/test_game_controller.py` now patch `_start_ai_turn` during GameController construction (preventing random-side thread leaks). The 2 tests that call `_on_move_applied` also wrap those calls with runtime-level patches.

3. **Full suite result:** 314 passed, 1 skipped, 0 failures -- goal achieved.

**Deviations from plan (all auto-fixed during execution, all beneficial):**
- Constructor-level mocking extended to all 5 tests (plan only specified 2) -- prevents thread leaks from random side assignment
- `_human_side=1` set explicitly in test 3 -- eliminates flaky assertion from random side assignment
- Thread leak protection extended to tests 1, 4, 5 -- consistent protection across all tests

---

_Verified: 2026-03-29T10:15:00Z_
_Verifier: Claude (gsd-verifier)_
