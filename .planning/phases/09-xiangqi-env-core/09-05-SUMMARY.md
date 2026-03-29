---
phase: 09-xiangqi-env-core
plan: "05"
subsystem: engine/fen-parser
tags: [gap-closure, halfmove-clock, WXF-FEN, regression]
dependency_graph:
  requires: []
  provides:
    - FEN parser correctly reads halfmove_clock from WXF 5-field format
    - FEN serializer includes halfmove_clock in output
    - Regression tests prevent recurrence of WXF FEN halfmove bug
  affects:
    - tests/test_rl.py (new tests)
    - src/xiangqi/engine/constants.py (from_fen + to_fen)
    - src/xiangqi/engine/engine.py (to_fen)
tech_stack: [Python, numpy, pytest]
key_files:
  created: []
  modified:
    - src/xiangqi/engine/constants.py
    - src/xiangqi/engine/engine.py
    - tests/test_rl.py
decisions:
  - id: "09-05-D1"
    decision: "Detect WXF 5-field by checking parts[3][0].isdigit() (halfmove starts with digit) vs standard 6-field where parts[3] is en_passant (letter or '-')"
    rationale: "parts[3] is always a digit in WXF format (halfmove value) but never a digit in standard FEN (en_passant square). This is the cleanest distinguishing feature."
    alternatives: "Check len(parts)==5 vs len(parts)==6, but 5-part WXF with extra garbage would be misclassified."
  - id: "09-05-D2"
    decision: "to_fen() accepts optional halfmove_clock=0 param, defaulting to 0 for backward compatibility with callers that don't track it"
    rationale: "Existing callers of to_fen() (like engine.py before this fix) don't pass halfmove_clock. Default=0 ensures no breakage; callers that do track it pass the value explicitly."
key_accuracy_metrics:
  - test_fen_halfmove_parsing: PASS (WXF=120, Standard=120, STARTING=0, WXF 0=0)
  - test_50_move_rule_via_wxf_fen: PASS (WXF FEN halfmove=120 -> DRAW)
  - test_50_move_rule: PASS (no regression on standard FEN)
  - test_rl.py full suite: 18 passed
  - test_api.py full suite: 31 passed
execution_time_seconds: ~60
completed_date: "2026-03-27"
---

# Phase 09 Plan 05: WXF FEN halfmove_clock Parsing Fix Summary

## One-liner

Fixed FEN parser to correctly detect WXF 5-field format (no en passant) vs standard 6-field, ensuring halfmove_clock is read from parts[3] for WXF and parts[4] for standard, then added regression tests closing UAT Test 8 gap.

## What Was Done

### Bug Root Cause
`from_fen()` unconditionally read `parts[4]` as halfmove_clock. WXF FEN omits the en passant field (5 fields: pieces/side/castling/halfmove/fullmove), so in WXF format parts[3]=halfmove and parts[4]=fullmove. The parser was reading fullmove(1) as halfmove, causing halfmove=1 instead of 120. This broke the 50-move rule check (`halfmove_clock >= 100`).

### Changes

**1. `src/xiangqi/engine/constants.py` - `from_fen()` WXF detection**
- Added format detection: if `parts[3][0].isdigit()` -> WXF 5-field (parts[3]=halfmove), else -> standard 6-field (parts[4]=halfmove)
- WXF: `'... w - 120 1'` -> parts[3]='120' -> halfmove=120 ✓
- Standard: `'... w - - 120 1'` -> parts[3]='-' -> parts[4]='120' -> halfmove=120 ✓
- STARTING_FEN: `'... w - 0 1'` -> parts[3]='0' -> halfmove=0 ✓

**2. `src/xiangqi/engine/constants.py` - `to_fen()` halfmove_clock param**
- Signature: `to_fen(board, turn, halfmove_clock=0)` (default=0 for backward compatibility)
- Output: `'... w - {halfmove_clock} 1'` instead of hardcoded `'0'`

**3. `src/xiangqi/engine/engine.py` - `to_fen()` method**
- Passes `self._state.halfmove_clock` to constants `to_fen()`
- FEN roundtrip (to_fen -> from_fen) now preserves halfmove_clock

**4. `tests/test_rl.py` - Regression tests**
- `test_fen_halfmove_parsing`: verifies from_fen handles both WXF and standard FEN formats
- `test_50_move_rule_via_wxf_fen`: UAT regression - WXF FEN halfmove>=100 triggers DRAW

## Deviations from Plan

### Auto-fixed Issue

**1. [Rule 1 - Bug Fix] Corrected plan's WXF detection rule**

- **Found during:** Task 1 implementation
- **Issue:** Plan's detection rule was `parts[3][0].isdigit() or parts[3] == '-'`. The `or parts[3] == '-'` clause would incorrectly classify standard FEN `'w - - 120 1'` (parts[3]='-') as WXF, then crash when trying `int('-')`.
- **Fix:** Changed condition to `parts[3][0].isdigit()` only. In standard FEN, parts[3] is the en_passant field which is never purely numeric (either '-' or a square like 'e3').
- **Files modified:** `src/xiangqi/engine/constants.py`
- **Commit:** a6f02e4

## Truths Verified

- [x] `from_fen('... w - 120 1')` (WXF 5-field) returns halfmove=120
- [x] `from_fen('... w - - 120 1')` (standard 6-field) returns halfmove=120
- [x] `from_fen(STARTING_FEN)` returns halfmove=0 (no regression)
- [x] `engine.to_fen()` roundtrip preserves halfmove_clock
- [x] `test_fen_halfmove_parsing` passes
- [x] `test_50_move_rule_via_wxf_fen` passes (the UAT regression)
- [x] `test_50_move_rule` still passes (existing test, no regression)
- [x] All tests in `tests/test_rl.py` pass (18 tests)
- [x] All tests in `tests/test_api.py` pass (31 tests)

## Commits

| Hash | Message |
|------|---------|
| a6f02e4 | fix(09-05): from_fen detects WXF 5-field vs standard 6-field format |
| c7a5542 | feat(09-05): to_fen includes halfmove_clock for FEN roundtrip fidelity |
| 859486d | test(09-05): add regression tests for WXF 5-field FEN halfmove parsing |

## Gap Closure

**Original Gap:** UAT Test 8 FAILS -- halfmove_clock=0 instead of 120 when loading FEN with halfmove_clock=120. 50-move rule never triggers.

**Resolution:** Gap closed. WXF 5-field FEN now correctly parses halfmove_clock from parts[3]. Regression tests prevent recurrence.
