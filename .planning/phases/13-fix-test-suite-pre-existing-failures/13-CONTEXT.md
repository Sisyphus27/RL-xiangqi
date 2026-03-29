# Phase 13: Fix Test Suite Pre-Existing Failures - Context

**Gathered:** 2026-03-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Fix 6 pre-existing test failures across 2 files with 2 distinct root causes. Both failures were introduced by Phase 09's `from_fen()` signature change and an async AI thread race condition in the game controller test. No new features — pure test fix.

**Out of scope:** New test coverage, UI bug fixes (debug docs in `.planning/debug/` are v0.2 UI issues, not test failures), performance optimization.

</domain>

<decisions>
## Implementation Decisions

### from_fen 3-tuple fix (5 tests in test_constants.py)
- **D-01:** Update all `from_fen()` calls to unpack 3 values: `board, turn, halfmove_clock = from_fen(...)` or `board, turn, _ = from_fen(...)` depending on whether halfmove_clock is used in the test
- Root cause: Phase 09 plan 09-05 changed `from_fen()` return from `(board, turn)` to `(board, turn, halfmove_clock)` to support WXF 5-field FEN parsing

### Async AI thread race fix (1 test in test_game_controller.py)
- **D-02:** Mock AI worker to avoid spawning real threads in tests, preventing signal leakage between test cases
- Root cause: `test_controller_starts_ai_on_black_turn` starts a real AI thread via `_on_move_applied` → `_start_ai_turn()`. The thread's `_on_ai_move_ready` signal fires asynchronously during subsequent tests, calling `is_legal()` on a stale/different engine instance

### Claude's Discretion
- Exact mock strategy for AI worker (patch `_start_ai_turn`, mock QThread, or use qtbot.waitSignal)
- Whether to add explicit thread cleanup in conftest.py

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Failing test files
- `tests/test_constants.py` — 5 failing `TestStartingFen` tests (lines 46-106): `from_fen()` unpacking
- `tests/controller/test_game_controller.py` — 1 failing `test_controller_validates_ai_move` (line 127): async race

### Source code (root causes)
- `src/xiangqi/engine/constants.py` lines 52-88 — `from_fen()` now returns `(board, turn, halfmove_clock)` 3-tuple
- `src/xiangqi/controller/game_controller.py` lines 130-156 — `_on_ai_move_ready()` with `is_legal()` guard and thread cleanup

### Related Phase 09 fix
- `.planning/phases/09-xiangqi-env-core/09-CONTEXT.md` — Phase 09 context where `from_fen()` signature was changed

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `tests/conftest.py` — existing `qapp` and `qtbot` fixtures for Qt test isolation
- `RandomAI(seed=42)` — deterministic AI used in game controller tests

### Established Patterns
- `from_fen(STARTING_FEN)` returns `(board, turn, halfmove_clock)` — new 3-tuple interface
- Game controller uses `QThread` + worker pattern for AI computation — signals (`_on_ai_move_ready`) cross thread boundary via Qt event loop
- Tests in `test_game_controller.py` use `Mock()` for board and window, real `XiangqiEngine` and `RandomAI`

### Integration Points
- `from_fen()` callers: `test_constants.py` (5 calls), `test_rl.py` (uses via env), `env.py` (via engine)
- `_on_ai_move_ready` signal handler in `game_controller.py` line 130 — the point where the race manifests

</code_context>

<specifics>
## Specific Ideas

- The 6 test failures are fully diagnosed — no investigation needed
- `test_constants.py` fix is a pure mechanical unpacking change (2→3 values)
- `test_game_controller.py` fix needs careful mock to prevent thread spawning while still testing the signal flow
- The `test_fen_roundtrip` test at line 105 also calls `from_fen()` with a custom FEN — needs same fix

</specifics>

<deferred>
## Deferred Ideas

- UI bugs documented in `.planning/debug/` (click-offset, click-no-response, second-selection-no-legal-moves) — these are v0.2 UI issues, not test failures, tracked separately
- Phase 11-02 (R4/R5 test coverage, 8 tests) — still unexecuted plan in ROADMAP.md, deferred for future work

</deferred>

---

*Phase: 13-fix-test-suite-pre-existing-failures*
*Context gathered: 2026-03-28*
