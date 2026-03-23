---
phase: 03-endgame-detection
verified: 2026-03-20T12:00:00Z
status: gaps_found
score: 5/6 must-haves verified
gaps:
  - truth: "Stalemate position (no legal moves + not in check) returns opponent wins (困毙)"
    status: partial
    reason: "The specific stalemate-without-check case is not verified by any test. The only stalemate test (test_stalemate_also_loss) has in_check=True — it is a checkmate test, not a stalemate test. The test listed in the plan (test_stalemate_red_trapped_no_check) does not exist in the file. The implementation handles stalemate correctly (same code path as checkmate: both return opponent wins), but the specific 'no legal moves + not in check' boundary is untested."
    artifacts:
      - path: tests/test_endgame.py
        issue: "test_stalemate_red_trapped_no_check listed in plan acceptance criteria but absent from file; test_stalemate_also_loss has in_check=True (checkmate, not stalemate)"
    missing:
      - "A test case with zero legal moves AND is_in_check=False that asserts opponent wins"
      - "test_stalemate_red_trapped_no_check per plan acceptance criteria"
  - truth: "(Requirements traceability gap) END-01/END-02/END-03/END-04 not marked satisfied in REQUIREMENTS.md"
    status: failed
    reason: "REQUIREMENTS.md shows END-01, END-02, END-03, END-04 as [ ] unchecked. Phase 3 implemented these requirements and they should be marked as satisfied."
    artifacts:
      - path: .planning/REQUIREMENTS.md
        issue: "END-01, END-02, END-03, END-04 all show [ ] instead of [x]"
    missing:
      - "REQUIREMENTS.md traceability table: END-01 [x], END-02 [x], END-03 [x], END-04 [x]"
---

# Phase 03: Endgame Detection Verification Report

**Phase Goal:** Endgame determination (终局判定) — detect game-ending conditions including checkmate, stalemate (困毙), threefold repetition, long check (长将), and long chase (长捉)

**Verified:** 2026-03-20
**Status:** gaps_found
**Score:** 5/6 observable truths verified programmatically

## Goal Achievement

### Observable Truths

| #   | Truth   | Status     | Evidence       |
| --- | ------- | ---------- | -------------- |
| 1   | Checkmate position (no legal moves + in check) returns opponent wins | VERIFIED | test_endgame.py::TestCheckmate::test_checkmate_red_loses, test_checkmate_black_loses; programmatically: legal=0, in_check=True, result=BLACK_WINS/RED_WINS |
| 2   | Stalemate position (no legal moves + not in check) returns opponent wins (困毙) | PARTIAL | Implementation correct (same code path as checkmate), but the specific stalemate-without-check case is untested. test_stalemate_also_loss has in_check=True (checkmate test). test_stalemate_red_trapped_no_check absent from file. |
| 3   | Mid-game position with legal moves returns IN_PROGRESS | VERIFIED | test_endgame.py::TestInProgress; programmatically: 44 legal moves, result=IN_PROGRESS |
| 4   | Threefold repetition triggers DRAW before check/stalemate | VERIFIED | test_endgame.py::TestPriorityOrder; test_repetition.py::TestRepetition; programmatically: hash x3 -> DRAW; priority order verified: repetition fires before checkmate |
| 5   | Four consecutive checking moves trigger DRAW before check/stalemate | VERIFIED | test_repetition.py::TestLongCheck; programmatically: consecutive_check_count=4 -> DRAW |
| 6   | Four consecutive chases cause chaser to lose | VERIFIED | test_repetition.py::TestLongChase; programmatically: chase_seq x4 + red=chaser -> BLACK_WINS; black=chaser -> RED_WINS |

**Score:** 5/6 truths verified; 1 partial (Truth 2 implementation correct but specific case untested)

### Required Artifacts

| Artifact | Expected    | Status | Details |
| -------- | ----------- | ------ | ------- |
| `src/xiangqi/engine/endgame.py` | get_game_result(), END-01/END-02 | VERIFIED | 72 lines; exports get_game_result; lazy import of repetition.py; full 6-case priority order implemented |
| `src/xiangqi/engine/repetition.py` | RepetitionState, check_* functions | VERIFIED | 198 lines; exports RepetitionState, check_repetition, check_long_check, check_long_chase, _detect_chase |
| `src/xiangqi/engine/rules.py` | Thin re-export shim | VERIFIED | No function implementations; re-exports from endgame.py and legal.py |
| `tests/test_endgame.py` | END-01/END-02 tests | PARTIAL | 151 lines; has checkmate tests, priority order test, IN_PROGRESS tests; missing test_stalemate_red_trapped_no_check (listed in plan but absent) |
| `tests/test_repetition.py` | END-03/END-04 tests | VERIFIED | 349 lines; 24 tests covering repetition, long check, long chase, RepetitionState.update() |
| `src/xiangqi/engine/legal.py` | __all__ with _generals_face_each_other | VERIFIED | __all__ = [is_in_check, flying_general_violation, _generals_face_each_other, apply_move, is_legal_move, generate_legal_moves] |
| `src/xiangqi/engine/state.py` | __all__ | VERIFIED | __all__ present |

### Key Link Verification

| From | To  | Via | Status | Details |
| ---- | --- | --- | ------ | ------- |
| `endgame.py` | `legal.py` | generate_legal_moves(), is_in_check() | WIRED | `from .legal import generate_legal_moves, is_in_check` confirmed in endgame.py line 6 |
| `endgame.py` | `repetition.py` | RepetitionState, check_*() | WIRED | Lazy import via `_ensure_repetition()` at line 18; all 4 names imported at runtime |
| `rules.py` | `endgame.py` | thin re-export | WIRED | `from .endgame import get_game_result` confirmed in rules.py line 10 |
| `repetition.py` | `legal.py` | is_in_check() | WIRED | `from .legal import is_in_check` confirmed in repetition.py line 11 |
| `repetition.py` | `moves.py` | gen_chariot, gen_cannon, gen_general, gen_soldier | WIRED | `from .moves import ...` confirmed in repetition.py line 12 |
| `test_endgame.py` | `endgame.py` | get_game_result | WIRED | `from src.xiangqi.engine.endgame import get_game_result` confirmed |
| `test_repetition.py` | `repetition.py` | RepetitionState, check_* | WIRED | All imports confirmed; 24 tests use them |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| END-01 | PLAN requirements | Checkmate detection: no legal moves + in check -> opponent wins | SATISFIED | Implementation in endgame.py lines 63-67; test_checkmate_red_loses + test_checkmate_black_loses pass; programmatically verified |
| END-02 | PLAN requirements | Stalemate (困毙) detection: no legal moves -> opponent wins | PARTIAL | Implementation correct (same code path as END-01); specific stalemate-without-check test missing; test_stalemate_red_trapped_no_check absent |
| END-03 | PLAN requirements | Long check (长将) and long chase (长捉) draw rules | SATISFIED | check_long_check() + check_long_chase() in repetition.py; 6+ tests in TestLongCheck and TestLongChase; programmatically verified |
| END-04 | PLAN requirements | Threefold repetition draw | SATISFIED | check_repetition() in repetition.py lines 90-101; 6 tests in TestRepetition; programmatically verified |

**Requirements traceability gap:** REQUIREMENTS.md marks END-01, END-02, END-03, END-04 as `[ ]` (unchecked) in the traceability table. They should be marked `[x]` since Phase 3 implemented them.

### Anti-Patterns Found

| File | Pattern | Severity | Impact |
| ---- | ------- | -------- | ------ |
| None | No placeholder/TODO/FIXME comments in endgame.py, repetition.py | Info | Clean codebase |

### Human Verification Required

None. All verifications are programmatic.

### Test Suite Status

- `pytest tests/test_endgame.py tests/test_repetition.py tests/test_rules.py`: 41 passed
- `pytest tests/ -v` (full suite): 132 passed, 0 failed

### Gaps Summary

**Gap 1 — Truth 2 partial (stalemate-without-check untested):**
The plan's acceptance criteria list `test_stalemate_red_trapped_no_check` but this test does not exist in the file. `test_stalemate_also_loss` is the only stalemate test and it has `in_check=True`, making it a checkmate test. The implementation handles stalemate correctly (Xiangqi rules: both checkmate and stalemate are losses for the player to move, implemented as a single code path), but the specific "no legal moves + NOT in check" boundary is not covered by any test.

**Gap 2 — REQUIREMENTS.md not updated:**
END-01, END-02, END-03, END-04 remain marked `[ ]` in REQUIREMENTS.md. The phase implemented all four but did not update the traceability table.

---

_Verified: 2026-03-20T12:00:00Z_
_Verifier: Claude (gsd-verifier)_
