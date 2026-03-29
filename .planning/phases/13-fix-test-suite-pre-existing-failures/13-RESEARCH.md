# Phase 13: Fix Test Suite Pre-Existing Failures - Research

**Researched:** 2026-03-28
**Domain:** Test fixing / refactoring (pytest + PyQt6)
**Confidence:** HIGH

## Summary

Phase 13 fixes pre-existing test failures caused by two distinct root causes introduced during Phase 09's `from_fen()` signature change, plus a Qt thread race condition in the game controller tests. The actual failure count is **5 `test_constants.py` failures** (all `from_fen()` unpacking) plus **2 `test_game_controller.py` failures** (async thread leak), totaling **7 test failures** -- not the 6 originally documented in CONTEXT.md. The discrepancy comes from `test_controller_emits_turn_changed_on_user_move` also being affected by the race, which was not called out separately.

**Primary recommendation:** Fix the 5 `from_fen()` calls mechanically (2-tuple to 3-tuple), then mock `_start_ai_turn` in the 2 controller tests that trigger real thread spawning to eliminate the race.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Update all `from_fen()` calls to unpack 3 values: `board, turn, halfmove_clock = from_fen(...)` or `board, turn, _ = from_fen(...)` depending on whether halfmove_clock is used in the test
- **D-02:** Mock AI worker to avoid spawning real threads in tests, preventing signal leakage between test cases

### Claude's Discretion
- Exact mock strategy for AI worker (patch `_start_ai_turn`, mock QThread, or use qtbot.waitSignal)
- Whether to add explicit thread cleanup in conftest.py

### Deferred Ideas (OUT OF SCOPE)
- UI bugs documented in `.planning/debug/` (click-offset, click-no-response, second-selection-no-legal-moves) -- these are v0.2 UI issues, not test failures, tracked separately
- Phase 11-02 (R4/R5 test coverage, 8 tests) -- still unexecuted plan in ROADMAP.md, deferred for future work
</user_constraints>

<phase_requirements>
## Phase Requirements

This is a bug-fix phase with no formal requirement IDs. The requirements are implied by the phase description:
- Fix all pre-existing test failures in `test_constants.py` (5 tests)
- Fix all pre-existing test failures in `test_game_controller.py` (2 tests)
- Full test suite passes: all tests green
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | 9.0.2 | Test runner | Already in use, configured in pyproject.toml |
| pytest-qt | 4.5.0 | Qt signal testing | Already in use for PyQt6 signal/slot tests |
| PyQt6 | 6.10.2 | Qt framework | Project's UI framework |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| unittest.mock | stdlib | Mocking `AIWorker` and `_start_ai_turn` | Controller tests to prevent thread spawning |

## Architecture Patterns

### Test File Organization
```
tests/
├── conftest.py                     # Shared fixtures (empty_board, starting_board, starting_state)
├── test_constants.py               # 9 tests: 4 BoundaryMasks + 5 StartingFen (5 FAIL)
├── controller/
│   ├── conftest.py                 # Session-scoped qapp fixture
│   ├── test_ai_worker.py           # 4 tests (PASS -- compute() called synchronously)
│   └── test_game_controller.py     # 5 tests (2 FAIL via thread leak)
```

### Pattern 1: from_fen() 3-tuple Unpacking
**What:** `from_fen()` now returns `(board, turn, halfmove_clock)` -- a 3-tuple
**When to use:** Every call site that unpacks `from_fen()` must accept 3 values
**Example:**
```python
# WRONG (pre-Phase 09):
board, turn = from_fen(STARTING_FEN)

# CORRECT (post-Phase 09):
board, turn, halfmove_clock = from_fen(STARTING_FEN)
# Or if halfmove_clock is unused:
board, turn, _ = from_fen(STARTING_FEN)
```

### Pattern 2: Mocking Thread-Spawning Methods
**What:** Patch `_start_ai_turn` on the controller to prevent real QThread creation
**When to use:** Any test that calls `_on_move_applied()` when it's the AI's turn
**Example:**
```python
# Prevent real thread spawning while still testing signal flow
with patch.object(controller, '_start_ai_turn'):
    controller._on_move_applied(from_sq, to_sq, 0)
```

### Anti-Patterns to Avoid
- **Spawning real QThreads in unit tests:** The test `_on_move_applied` -> `_start_ai_turn` path creates real threads. The thread's `move_ready` signal fires asynchronously, corrupting subsequent tests. Always mock thread creation.
- **Relying on test execution order:** Tests that pass in isolation but fail in the full suite indicate order-dependent state (thread leakage). Fix the root cause, don't reorder tests.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Thread cleanup in tests | Custom QThread.wait() loops | `patch.object(controller, '_start_ai_turn')` | Mocking eliminates the thread entirely; cleanup code is fragile |
| Signal waiting | Manual QEventLoop | `qtbot.waitSignal()` (already available) | pytest-qt provides this; but for these tests, mocking is simpler |

## Common Pitfalls

### Pitfall 1: from_fen() Unpacking -- Using `_` for Unused Halfmove Clock
**What goes wrong:** Some tests need `halfmove_clock`, others don't. Mixing `board, turn =` with `board, turn, _ =` can cause confusion.
**Why it happens:** The signature change was made in Phase 09 plan 09-05 but tests in `test_constants.py` were not updated.
**How to avoid:** Use `board, turn, _ = from_fen(...)` for tests that don't need halfmove_clock; use `board, turn, halfmove_clock = from_fen(...)` only when the test asserts on it.
**Warning signs:** `ValueError: too many values to unpack (expected 2)` at any `from_fen()` call.

### Pitfall 2: to_fen() Also Changed Signature
**What goes wrong:** `to_fen(board, turn)` still works because `halfmove_clock` has a default of 0. But `test_fen_roundtrip` calls `to_fen(board, turn)` which will produce `halfmove_clock=0` -- this may or may not match the FEN being tested.
**Why it happens:** The test only compares rank strings and color, not halfmove/fullmove, so the default of 0 is acceptable.
**How to avoid:** Verify that the roundtrip test assertion doesn't check halfmove_clock. It doesn't -- it only checks `split()[0]` (ranks) and `split()[1]` (color). The `to_fen` 2-arg call is safe.
**Warning signs:** If someone later adds a halfmove assertion to the roundtrip test.

### Pitfall 3: Thread Race is Order-Dependent
**What goes wrong:** Controller tests pass in isolation (5/5 green) but fail when run after other tests. The exact number of failures depends on which tests ran before and whether their threads have finished.
**Why it happens:** `test_controller_starts_ai_on_black_turn` calls `_on_move_applied()` which triggers `_start_ai_turn()`, creating a real QThread. The thread's `_on_ai_move_ready` signal fires during teardown or the next test, calling `is_legal()` on a stale engine.
**How to avoid:** Mock `_start_ai_turn` in any test that would trigger AI thread creation. The test's purpose is to verify `ai_thinking_started` signal emission, not thread mechanics.
**Warning signs:** `ValueError: AI returned illegal move` in Qt event loop during teardown; `assert 0 == 1` for signal tracking assertions.

### Pitfall 4: Actual Failure Count is 7, Not 6
**What goes wrong:** CONTEXT.md says 6 failures but the actual count is 7. `test_controller_emits_turn_changed_on_user_move` also fails due to thread leakage from the `TestGameControllerAIThinking` test.
**Why it happens:** The thread from `test_controller_starts_ai_on_black_turn` fires `move_ready` signal during the next test's execution, causing `ValueError` in the Qt event loop.
**How to avoid:** Both controller tests that trigger `_on_move_applied` when it's AI's turn need mocking. The fix for D-02 must cover both tests.

## Code Examples

### Fix 1: test_constants.py -- 5 Tests (Lines 48, 55, 69, 83, 99/105)

All 5 `TestStartingFen` tests need the same pattern change:

```python
# Line 48 - test_starting_fen_parsed
# BEFORE:
board, turn = from_fen(STARTING_FEN)
# AFTER:
board, turn, _ = from_fen(STARTING_FEN)

# Lines 55, 69, 83 - red_back_rank, black_back_rank, pawns
# BEFORE:
board, _ = from_fen(STARTING_FEN)
# AFTER:
board, _, _ = from_fen(STARTING_FEN)

# Lines 99, 105 - test_fen_roundtrip
# BEFORE:
board, turn = from_fen(STARTING_FEN)
board2, turn2 = from_fen("rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR b - 0 1")
# AFTER:
board, turn, _ = from_fen(STARTING_FEN)
board2, turn2, _ = from_fen("rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR b - 0 1")
```

### Fix 2: test_game_controller.py -- 2 Tests

**test_controller_starts_ai_on_black_turn (line 86):** This test checks that `ai_thinking_started` signal fires when it's AI's turn. The `_on_move_applied` handler calls `_start_ai_turn()` which spawns a real thread. Mock it.

```python
# Option A: Patch _start_ai_turn (RECOMMENDED -- simplest, most targeted)
from unittest.mock import patch

def test_controller_starts_ai_on_black_turn(self, qapp, qtbot):
    # ... setup controller ...
    thinking_started = []
    controller.ai_thinking_started.connect(lambda: thinking_started.append(True))

    # Apply red move, trigger handler
    move = engine.legal_moves()[0]
    engine.apply(move)
    from_sq = move & 0x1FF
    to_sq = (move >> 9) & 0x7F

    # Mock _start_ai_turn to prevent thread spawning
    with patch.object(controller, '_start_ai_turn'):
        controller._on_move_applied(from_sq, to_sq, 0)

    assert len(thinking_started) == 1
```

**test_controller_emits_turn_changed_on_user_move (line 44):** This test calls `_on_move_applied` when it becomes black's turn. If the controller's human_side is Red (random), this triggers `_start_ai_turn`. It also needs mocking.

```python
def test_controller_emits_turn_changed_on_user_move(self, qapp, qtbot):
    # ... setup controller ...
    emitted_turns = []
    controller.turn_changed.connect(lambda t: emitted_turns.append(t))

    move = engine.legal_moves()[0]
    engine.apply(move)
    from_sq = move & 0x1FF
    to_sq = (move >> 9) & 0x7F

    with patch.object(controller, '_start_ai_turn'):
        controller._on_move_applied(from_sq, to_sq, 0)

    assert len(emitted_turns) == 1
    assert emitted_turns[0] == -1
```

Note: `_start_ai_turn` emits `ai_thinking_started` itself. When mocked, this signal won't fire. But this test doesn't check `ai_thinking_started` -- it only checks `turn_changed`. The `turn_changed` signal is emitted by `_on_move_applied` before `_start_ai_turn` is called, so mocking `_start_ai_turn` doesn't affect the assertion.

Wait -- examining the code flow more carefully:

```python
# game_controller.py _on_move_applied:
def _on_move_applied(self, from_sq, to_sq, captured):
    result = self._engine.result()
    if result != "IN_PROGRESS":
        self._handle_game_over(result)
        return
    self.turn_changed.emit(self._engine.turn)  # emits turn_changed
    if self._engine.turn != self._human_side:
        self._start_ai_turn()  # spawns thread
```

So `turn_changed` is emitted before `_start_ai_turn`. Mocking `_start_ai_turn` is safe for both tests:
- `test_controller_emits_turn_changed_on_user_move` checks `turn_changed` -- emitted before mock kicks in
- `test_controller_starts_ai_on_black_turn` checks `ai_thinking_started` -- this is emitted INSIDE `_start_ai_turn`, so mocking it means the signal won't fire

For `test_controller_starts_ai_on_black_turn`, the test needs to verify that `_start_ai_turn` was called (proving the flow reaches it), rather than checking the signal. Alternative: emit `ai_thinking_started` manually before or after the mock.

**Best approach for `test_controller_starts_ai_on_black_turn`:**
```python
with patch.object(controller, '_start_ai_turn') as mock_start:
    controller._on_move_applied(from_sq, to_sq, 0)
    mock_start.assert_called_once()
```

This tests the actual behavior under test (that `_start_ai_turn` is invoked on black's turn) without spawning threads.

## Verified Failure Analysis

### Test Run Results (2026-03-28)

**test_constants.py:** 5 FAIL, 4 PASS
| Test | Error | Fix |
|------|-------|-----|
| `test_starting_fen_parsed` (L48) | `ValueError: too many values to unpack` | `board, turn, _ = from_fen(...)` |
| `test_starting_fen_red_back_rank` (L55) | `ValueError: too many values to unpack` | `board, _, _ = from_fen(...)` |
| `test_starting_fen_black_back_rank` (L69) | `ValueError: too many values to unpack` | `board, _, _ = from_fen(...)` |
| `test_starting_fen_pawns` (L83) | `ValueError: too many values to unpack` | `board, _, _ = from_fen(...)` |
| `test_fen_roundtrip` (L99, L105) | `ValueError: too many values to unpack` | Both `from_fen()` calls need 3-tuple |

**test_game_controller.py (in full suite):** 2 FAIL (+ 1 ERROR at teardown)
| Test | Error | Root Cause | Fix |
|------|-------|------------|-----|
| `test_controller_emits_turn_changed_on_user_move` | Thread race: `ValueError: AI returned illegal move: 35416` in Qt event loop | Prior test's AI thread fires signal during this test | Mock `_start_ai_turn` |
| `test_controller_starts_ai_on_black_turn` | `assert 0 == 1` (signal never caught) + teardown `ValueError` | Spawns real thread; `move_ready` fires async in wrong test context | Mock `_start_ai_turn` |

**test_game_controller.py (in isolation):** 5 PASS, 0 FAIL -- confirms race condition

### Important: Test Contamination Chain

The thread race follows this chain:
1. `test_controller_starts_ai_on_black_turn` calls `_on_move_applied` -> `_start_ai_turn()` spawns QThread
2. Test ends but thread is still running
3. Thread's `_on_ai_move_ready` signal fires during teardown or next test's execution
4. Signal handler calls `is_legal()` on the old engine (which may have been GC'd or in a different state)
5. `ValueError: AI returned illegal move: 35416` is raised in Qt event loop
6. pytest-qt catches this as a test error

The contamination affects tests that run AFTER any test spawning an AI thread. With proper mocking, no threads are spawned and the chain breaks.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `from_fen() -> (board, turn)` | `from_fen() -> (board, turn, halfmove_clock)` | Phase 09 plan 09-05 | All callers must unpack 3 values |
| `to_fen(board, turn)` | `to_fen(board, turn, halfmove_clock=0)` | Phase 09 plan 09-05 | Backward compatible (default arg) |

## Open Questions

1. **Should we add thread-cleanup to conftest.py?**
   - What we know: CONTEXT.md lists this as Claude's discretion. The mock approach eliminates threads entirely.
   - Recommendation: No conftest cleanup needed if all tests mock `_start_ai_turn`. A cleanup fixture would be defense-in-depth but adds complexity.
   - Confidence: HIGH

2. **Should `test_controller_validates_ai_move` also be protected?**
   - What we know: It calls `_on_ai_move_ready()` directly (not via thread), so it doesn't spawn threads. In isolation, it passes. In the full suite, it can be contaminated by threads from other tests.
   - Recommendation: If the other 2 tests are fixed (no more thread spawning), this test will be fine. No changes needed.
   - Confidence: HIGH

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| conda env `xqrl` | All tests | True | Python 3.12.0 | -- |
| pytest | Test runner | True | 9.0.2 | -- |
| pytest-qt | Qt signal tests | True | 4.5.0 | -- |
| PyQt6 | Qt framework | True | 6.10.2 | -- |
| numpy | Board arrays | True | >=2.0 | -- |

**Missing dependencies with no fallback:** None

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `conda activate xqrl && python -m pytest tests/test_constants.py tests/controller/test_game_controller.py -q --tb=short` |
| Full suite command | `conda activate xqrl && python -m pytest -q --tb=short` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FIX-01 | from_fen 3-tuple unpacking in test_starting_fen_parsed | unit | `pytest tests/test_constants.py::TestStartingFen::test_starting_fen_parsed -v` | Yes (needs fix) |
| FIX-02 | from_fen 3-tuple unpacking in test_starting_fen_red_back_rank | unit | `pytest tests/test_constants.py::TestStartingFen::test_starting_fen_red_back_rank -v` | Yes (needs fix) |
| FIX-03 | from_fen 3-tuple unpacking in test_starting_fen_black_back_rank | unit | `pytest tests/test_constants.py::TestStartingFen::test_starting_fen_black_back_rank -v` | Yes (needs fix) |
| FIX-04 | from_fen 3-tuple unpacking in test_starting_fen_pawns | unit | `pytest tests/test_constants.py::TestStartingFen::test_starting_fen_pawns -v` | Yes (needs fix) |
| FIX-05 | from_fen 3-tuple unpacking in test_fen_roundtrip | unit | `pytest tests/test_constants.py::TestStartingFen::test_fen_roundtrip -v` | Yes (needs fix) |
| FIX-06 | No thread leak in test_controller_emits_turn_changed_on_user_move | unit | `pytest tests/controller/test_game_controller.py::TestGameControllerTurnChanged -v` | Yes (needs fix) |
| FIX-07 | No thread leak in test_controller_starts_ai_on_black_turn | unit | `pytest tests/controller/test_game_controller.py::TestGameControllerAIThinking -v` | Yes (needs fix) |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/test_constants.py tests/controller/test_game_controller.py -q --tb=short`
- **Per wave merge:** `python -m pytest -q --tb=short`
- **Phase gate:** Full suite green, including `python -m pytest tests/test_constants.py tests/controller/test_game_controller.py tests/test_rl.py tests/test_selfplay.py -v`

### Wave 0 Gaps
None -- existing test infrastructure covers all phase requirements. The files exist, they just need code fixes.

## Sources

### Primary (HIGH confidence)
- Direct code inspection: `tests/test_constants.py`, `tests/controller/test_game_controller.py`, `src/xiangqi/engine/constants.py`, `src/xiangqi/controller/game_controller.py`
- Live test execution confirmed 7 failures (5 constants + 2 controller)
- CONTEXT.md canonical references verified against actual code

### Secondary (MEDIUM confidence)
- pytest-qt documentation for signal testing patterns
- Phase 09 STATE.md context for `from_fen()` signature change rationale

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all tools already in use, versions verified by running tests
- Architecture: HIGH - code read directly, failure mechanism fully understood
- Pitfalls: HIGH - confirmed by running tests in both isolation and full suite

**Research date:** 2026-03-28
**Valid until:** 2026-04-27 (stable, code-level changes only)
