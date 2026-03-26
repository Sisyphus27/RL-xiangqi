---
phase: 06-piece-interaction
plan: "00"
subsystem: testing
tags: [pytest, pyqt6, xiangqi, fixture]

# Dependency graph
requires:
  - phase: 05-board-rendering
    provides: QXiangqiBoard + PieceItem rendering; existing board(qtbot) fixture
provides:
  - board_with_engine fixture with XiangqiEngine access
  - 8 test stubs covering UI-03, UI-04, UI-05 interaction behaviors
affects:
  - Phase 06 (06-01, 06-02, 06-03) — all subsequent plans implement against these stubs

# Tech tracking
tech-stack:
  added: []
  patterns:
    - board_with_engine fixture pattern: engine owns state, board receives both state and engine reference
    - Stub-first TDD: test scaffold before implementation

key-files:
  created:
    - tests/ui/test_board_interaction.py
  modified:
    - src/xiangqi/engine/engine.py
    - tests/ui/conftest.py

key-decisions:
  - "XiangqiEngine.state property added (private _state made accessible) for board fixture contract"

patterns-established:
  - "board_with_engine fixture: QXiangqiBoard(state=engine.state, engine=engine) pattern for Phase 06 interaction tests"

requirements-completed: [UI-03, UI-04, UI-05]

# Metrics
duration: ~3min
completed: 2026-03-25
---

# Phase 06 Plan 00: Test Scaffold Summary

**Test scaffold established for piece interaction: board_with_engine fixture + 8 stub tests covering select/highlight/move/deselect (UI-03/04/05)**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-03-25T02:36:38Z (from STATE.md last_updated)
- **Completed:** 2026-03-25
- **Tasks:** 1
- **Files modified:** 3 created/modified

## Accomplishments

- Added XiangqiEngine.state property (private _state exposed as read-only property)
- Created board_with_engine fixture in tests/ui/conftest.py with engine reference
- Created tests/ui/test_board_interaction.py with 8 pass-only stubs
- All 8 stubs discoverable via pytest --collect-only

## Task Commits

Each task was committed atomically:

1. **Task 1: update fixture and create test stubs** - `2057f53` (feat)

**Plan metadata:** (final metadata commit follows this summary)

## Files Created/Modified

- `src/xiangqi/engine/engine.py` - Added `state` property (Rule 3: blocking issue for fixture contract)
- `tests/ui/conftest.py` - Added board_with_engine fixture with engine + state parameters
- `tests/ui/test_board_interaction.py` - 8 stub tests for UI-03/04/05 behaviors

## Decisions Made

- **XiangqiEngine.state property added:** The plan fixture specification uses `engine.state`, but the engine only exposed `engine.board` (ndarray) and `engine.turn` (int), not the full state object. Added `state` property as XiangqiState access point so the fixture contract matches the spec. (Rule 3 — blocking issue: fixture could not work without this)
- **QXiangqiBoard(engine=...) accepted as future contract:** The current QXiangqiBoard.__init__ does not accept `engine`; this will be added in 06-01. Fixture is written to the future API spec so 06-01 can implement against it.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added XiangqiEngine.state property**
- **Found during:** Task 1 (fixture creation)
- **Issue:** Plan fixture uses `engine.state` but XiangqiEngine had no public state property (only private `_state`)
- **Fix:** Added `@property def state(self) -> XiangqiState: return self._state` after the board property
- **Files modified:** src/xiangqi/engine/engine.py
- **Verification:** pytest --collect-only on test_board_interaction.py returns 8 tests
- **Committed in:** 2057f53 (task commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Essential for fixture contract — without this the board_with_engine fixture could not be written as specified.

## Issues Encountered

None — execution was straightforward.

## Known Stubs

The following stubs are intentionally empty (implementation in 06-01/06-02):

| Test | Stub | File | Line | Implementation Plan |
|------|------|------|------|---------------------|
| test_select_piece_shows_ring | pass | test_board_interaction.py | 13 | 06-01 |
| test_select_piece_shows_legal_moves | pass | test_board_interaction.py | 18 | 06-01 |
| test_click_legal_target_moves_piece | pass | test_board_interaction.py | 23 | 06-02 |
| test_move_emits_signal | pass | test_board_interaction.py | 28 | 06-02 |
| test_click_illegal_deselects | pass | test_board_interaction.py | 33 | 06-01 |
| test_click_empty_deselects | pass | test_board_interaction.py | 38 | 06-01 |
| test_black_turn_disabled | pass | test_board_interaction.py | 43 | 06-01 |
| test_piece_index_lookup | pass | test_board_interaction.py | 48 | 06-01 |

## Next Phase Readiness

- board_with_engine fixture ready for 06-01 implementation
- 8 test stubs discovered by pytest, ready for implementation
- QXiangqiBoard.__init__ signature update planned for 06-01 (engine parameter)
- No blockers

---
*Phase: 06-piece-interaction*
*Plan: 00*
*Completed: 2026-03-25*
