---
phase: 13-fix-test-suite-pre-existing-failures
plan: 01
subsystem: testing
tags: [pytest, unittest.mock, from_fen, QThread, flaky-tests]

# Dependency graph
requires:
  - phase: 09
    provides: "from_fen() 3-tuple return (board, turn, halfmove_clock)"
provides:
  - "All 314 tests passing, zero failures"
  - "Deterministic controller tests (no random side assignment flakiness)"
affects: [test-constants, controller-tests]

# Tech tracking
tech-stack:
  added: []
  patterns: ["patch.object on class method during construction to prevent QThread leaks"]

key-files:
  created: []
  modified:
    - tests/test_constants.py
    - tests/controller/test_game_controller.py

key-decisions:
  - "D-01: Use _ placeholder for unused halfmove_clock in from_fen unpacking"
  - "D-02: Mock _start_ai_turn to prevent real QThread spawning in tests"
  - "D-03: Set controller._human_side=1 explicitly for deterministic AI turn test"

patterns-established:
  - "Patch _start_ai_turn during GameController construction to prevent random-side thread leaks"

requirements-completed: [FIX-01, FIX-02, FIX-03, FIX-04, FIX-05, FIX-06, FIX-07]

# Metrics
duration: 13min
completed: 2026-03-29
---

# Phase 13: Fix Test Suite Pre-existing Failures Summary

Fix 7 test failures across 2 files by updating from_fen() unpacking to 3-tuple and mocking _start_ai_turn to prevent QThread leaks in controller tests.

## Performance

- **Duration:** 13 min
- **Started:** 2026-03-29T01:35:54Z
- **Completed:** 2026-03-29T01:49:49Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Fixed all 5 TestStartingFen failures by updating from_fen() calls from 2-value to 3-value unpacking (halfmove_clock added in Phase 09)
- Fixed 2 controller test failures by mocking _start_ai_turn to prevent real QThread creation during tests
- Full test suite green: 314 passed, 1 skipped, 0 failures in 132.57s

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix from_fen() 3-tuple unpacking in test_constants.py** - `552985e` (fix)
2. **Task 2: Mock _start_ai_turn to prevent thread leaks in test_game_controller.py** - `1a7354b` (fix)

## Files Created/Modified

- `tests/test_constants.py` - Updated all 6 from_fen() calls to unpack 3 values (board, turn, _ = from_fen(...))
- `tests/controller/test_game_controller.py` - Added patch.object(_start_ai_turn) during construction in all 5 tests; set _human_side=1 for deterministic AI turn test

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Constructor _start_ai_turn not mocked**
- **Found during:** Task 2 verification
- **Issue:** Plan only specified mocking _start_ai_turn in _on_move_applied calls. However, the GameController constructor also calls _start_ai_turn (when random side assigns human=Black). This caused intermittent test failures.
- **Fix:** Added patch.object(GameController, '_start_ai_turn') during construction in all 5 controller tests, not just tests 2 and 3.
- **Files modified:** tests/controller/test_game_controller.py
- **Commit:** 1a7354b

**2. [Rule 1 - Bug] Random _human_side causes flaky assertion**
- **Found during:** Task 2 verification
- **Issue:** Test 3 (test_controller_starts_ai_on_black_turn) asserts _start_ai_turn is called once, but when _human_side randomly equals -1 (human=Black), AI is Red and _start_ai_turn is NOT called after a Red move (Red is AI but it was already AI's turn before the move).
- **Fix:** Set controller._human_side = 1 explicitly after construction to make human always Red and AI always Black, ensuring deterministic behavior.
- **Files modified:** tests/controller/test_game_controller.py
- **Commit:** 1a7354b

**3. [Rule 2 - Missing critical functionality] Tests 1, 4, 5 lack thread leak protection**
- **Found during:** Task 2 (extending fix from Rule 1 discovery)
- **Issue:** All 5 controller tests construct GameController, which can spawn real QThreads via constructor. Tests 1, 4, and 5 were not covered by the plan's mock fix but had the same vulnerability.
- **Fix:** Added patch.object(GameController, '_start_ai_turn') during construction in tests 1, 4, and 5 as well.
- **Files modified:** tests/controller/test_game_controller.py
- **Commit:** 1a7354b

## Verification

Full test suite result: **314 passed, 1 skipped, 0 failures** in 132.57s

## Self-Check: PASSED

- FOUND: tests/test_constants.py
- FOUND: tests/controller/test_game_controller.py
- FOUND: .planning/phases/13-fix-test-suite-pre-existing-failures/13-01-SUMMARY.md
- FOUND: commit 552985e (Task 1)
- FOUND: commit 1a7354b (Task 2)
- FOUND: commit f5e6c1c (metadata)
