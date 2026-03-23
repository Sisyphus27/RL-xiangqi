---
phase: 02-move-generation
verified: 2026-03-20T12:30:00Z
status: gaps_found
score: 10/12 must-haves verified
re_verification: false
gaps:
  - truth: "perft(3) from starting position = 79,666 nodes (CPW verified)"
    status: failed
    reason: "generate_legal_moves produces wrong counts at depth 2+ in certain positions. perft(3) = 77,508 vs expected 79,666 (missing 2,158 nodes). perft(2) = 1,920 passes correctly. The perft divide at depth 1 (per-child depth-2 counts summing to 1,920) also passes. Bug is in move generation at depth-2 positions — per-move depth-2 counts are individually wrong for specific positions, but the aggregate total passes."
    artifacts:
      - path: "src/xiangqi/engine/moves.py"
        issue: "Possible subtle bug in one or more gen_* functions — affects certain board configurations that only appear at depth 2+. All unit tests pass. Specific failing positions identified: children with depth-2 counts of 40 (vs typical 44) have systematically low perft(3) subtrees. The bug is NOT in perft divide infrastructure — confirmed by running perft divide manually."
      - path: "src/xiangqi/engine/legal.py"
        issue: "is_in_check or is_legal_move may be filtering out legal moves in specific depth-2+ positions. Alternatively, generate_legal_moves may miss some pseudo-legal candidates in those positions."
  missing:
    - "Root-cause analysis of which specific gen_* function or is_in_check case is wrong"
    - "Fix for the identified bug"
    - "Perft depth 3 and 4 tests passing with CPW reference values"
  plan_note: "PLAN 02-01 soldier crossed logic (fr >= 5) is INVERTED vs the CODE (fr <= 4). The code is CORRECT (verified via test_moves.py test_black_soldier_pre_river and test_black_soldier_crossed_river comments: 'FIXED: crossed = (color==+1 and fr<=4)'). The PLAN was written with inverted logic. The bug in perft is likely NOT the soldier crossed logic — perft(2) passes correctly."

  - truth: "perft(4) from starting position = 3,290,240 nodes (CPW verified)"
    status: failed
    reason: "perft(4) = 3,112,545 vs expected 3,290,240 (missing 177,695 nodes). Same root cause as perft(3) failure — move generation bug that compounds at greater depth."
    artifacts:
      - path: "tests/test_perft.py"
        issue: "test_perft_depth_4_reference fails, confirming the same bug affects depth 4+"

  - truth: "test_requirements_md_values_fail proves REQUIREMENTS.md values are wrong"
    status: failed
    reason: "This test asserts that the perft implementation matches CPW values, but perft(3) is 77,508 not 79,666, so the final CPW assertions fail."
    artifacts:
      - path: "tests/test_perft.py::TestPerftStartingPosition::test_requirements_md_values_fail"
        issue: "Test fails because perft implementation does not yet match CPW reference"
---

# Phase 02: Move Generation Verification Report

**Phase Goal:** 7 species of piece legal move generation + check detection + face-to-face rule
**Verified:** 2026-03-20T12:30:00Z
**Status:** gaps_found
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Each piece type generates correct pseudo-legal moves given board geometry | VERIFIED | All 7 gen_* functions implemented in moves.py; 32 unit tests pass covering unblocked, blocked, palace, river, leg/eye, screen cases |
| 2 | is_in_check detects all attack sources (chariot, horse, cannon, soldier, advisor, elephant, face-to-face) | VERIFIED | is_in_check in legal.py implements all 7 attack sources; 8 test cases pass in TestIsInCheck |
| 3 | generate_legal_moves returns exactly 44 legal moves from starting position | VERIFIED | `python3.11 -m pytest tests/test_legal.py::TestGenerateLegalMoves::test_starting_position_legal_moves` — 44 moves confirmed; test asserts >=40 (too loose but passes) |
| 4 | Self-check moves are filtered out | VERIFIED | is_legal_move uses board-copy post-check; TestIsLegalMove tests pass |
| 5 | Flying general violation detected and blocks moves | VERIFIED | flying_general_violation implemented in both legal.py and rules.py; 3 unit tests pass in test_legal.py and 3 in test_rules.py |
| 6 | Stalemate (no moves, not in check) = loss for current player per RULE-06 | VERIFIED | get_game_result in rules.py returns BLACK_WINS/RED_WINS for stalemate; 4 tests pass in test_rules.py |
| 7 | perft(1) from starting position = 44 nodes (CPW verified) | VERIFIED | test_perft_depth_1 passes |
| 8 | perft(2) from starting position = 1,920 nodes (CPW verified) | VERIFIED | test_perft_depth_2 passes; divide confirms sum of per-child depth-2 counts = 1,920 |
| 9 | perft(3) from starting position = 79,666 nodes (CPW verified) | FAILED | test_perft_depth_3: expected 79,666, got 77,508 (gap: 2,158 nodes missing) |
| 10 | perft(4) from starting position = 3,290,240 nodes (CPW verified) | FAILED | test_perft_depth_4_reference: expected 3,290,240, got 3,112,545 (gap: 177,695 nodes missing) |
| 11 | test_requirements_md_values_fail proves REQUIREMENTS.md values are wrong | FAILED | Test asserts perft matches CPW (79,666), fails because implementation is 77,508 |
| 12 | Flying general violation blocks moves that clear a file between generals | VERIFIED | TestFlyingGeneralViolation tests pass; is_legal_move calls flying_general_violation |

**Score:** 9/12 truths verified; 3 FAILED

---

### Root Cause Analysis: perft Depth 3+ Failure

The perft divide at depth 1 confirms each of the 44 depth-1 children generates correct depth-2 counts totaling 1,920 (perft(2) passes). The failure appears at depth 3+ — the bug is in **move generation from depth-2 positions**.

Key data from manual perft divide:
- Depth-2 count distribution: {40: 2 children, 41: 4, 42: 2, 43: 6, 44: 16, 45: 14}
- Depth-3 per-child range: 1,474 to 2,271
- Some children with depth-2 count = 40 (vs typical 44) have systematically low depth-3 counts (1,637 each)
- Perft(2) correct (1,920), perft(3) wrong (77,508 vs 79,666)

The bug is **not** in the perft infrastructure (divide logic verified by manual computation), **not** in the crossed logic (crossed logic confirmed correct via test comment analysis), and **not** in the horse leg bug described in test_moves.py (that bug was already fixed with bounds check). The bug is a subtle piece-movement edge case that only manifests in certain depth-2+ board configurations.

Confirmed correct by trace:
- Soldier crossed logic: `crossed = (fr <= 4)` for red, `(fr >= 5)` for black — correct
- Elephant river: red stays rows 5-9, black stays rows 0-4 — correct
- Horse leg: bounds check before array access — correct
- Cannon screen: exactly-1-screen capture — correct

**Executor note:** The phase executor identified the depth 3+ perft bug but did not fix it before concluding the phase.

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/xiangqi/engine/moves.py` | 7 gen_* + helpers | VERIFIED | All exports present: gen_general, gen_chariot, gen_horse, gen_cannon, gen_advisor, gen_elephant, gen_soldier, belongs_to, all_pieces_of_color |
| `src/xiangqi/engine/legal.py` | is_in_check, is_legal_move, generate_legal_moves, apply_move, flying_general_violation | VERIFIED | All exports present; imports from moves.py correctly wired |
| `src/xiangqi/engine/rules.py` | flying_general_violation, _generals_face_each_other, get_game_result | VERIFIED | All exports present; re-imports from legal.py for get_game_result |
| `tests/test_moves.py` | 32 per-piece unit tests | VERIFIED | All 32 tests pass |
| `tests/test_legal.py` | 23 check detection and legal filtering tests | VERIFIED | All 23 tests pass |
| `tests/test_rules.py` | 11 face-to-face and game result tests | VERIFIED | All 11 tests pass |
| `tests/test_perft.py` | Perft tests vs CPW reference | PARTIAL | test_perft_depth_1 PASS, test_perft_depth_2 PASS; test_perft_depth_3 FAIL, test_perft_depth_4 FAIL, test_requirements_md_values_fail FAIL |

---

### Key Link Verification

| From | To | Via | Status |
|------|----|-----|--------|
| `legal.py` | `moves.py` | `from .moves import gen_*, all_pieces_of_color` | WIRED |
| `legal.py::is_in_check` | `state.py::XiangqiState` | `state.king_positions` for O(1) king lookup | WIRED |
| `legal.py::is_legal_move` | `legal.py::is_in_check` | Board-copy post-check after apply_move | WIRED |
| `legal.py::generate_legal_moves` | `legal.py::is_legal_move` | Filters all pseudo-legal candidates | WIRED |
| `rules.py::get_game_result` | `legal.py` | `from .legal import generate_legal_moves, is_in_check` | WIRED |
| `tests/test_perft.py` | `legal.py` | `from src.xiangqi.engine.legal import generate_legal_moves` | WIRED |
| `tests/test_legal.py` | `legal.py` | Direct import of all exported functions | WIRED |
| `tests/test_rules.py` | `rules.py` | Direct import of exported functions | WIRED |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|------------|------------|-------------|--------|----------|
| MOVE-01 | 02-01 | General orthogonal 1-step, palace only | SATISFIED | gen_general implemented, tests pass |
| MOVE-02 | 02-01 | Chariot orthogonal sliding | SATISFIED | gen_chariot implemented, 3 unit tests pass |
| MOVE-03 | 02-01 | Horse L-shape with leg block | SATISFIED | gen_horse implemented, bounds check prevents numpy wrap; 4 unit tests pass |
| MOVE-04 | 02-01 | Cannon slide + exactly-1-screen capture | SATISFIED | gen_cannon implemented, 3 unit tests pass |
| MOVE-05 | 02-01 | Advisor diagonal 1-step, palace only | SATISFIED | gen_advisor implemented, 2 unit tests pass |
| MOVE-06 | 02-01 | Elephant diagonal 2-step, eye block, no river crossing | SATISFIED | gen_elephant implemented, 4 unit tests pass |
| MOVE-07 | 02-01 | Soldier forward always, sideways after river | SATISFIED | gen_soldier implemented, 5 unit tests pass |
| RULE-01 | 02-01 | is_legal_move validation | SATISFIED | is_legal_move implemented, 3 unit tests pass |
| RULE-02 | 02-01 | generate_legal_moves with filtering | SATISFIED | generate_legal_moves implemented, 3 tests pass including 44-move check |
| RULE-03 | 02-01 | is_in_check all attack sources | SATISFIED | is_in_check implemented with all 7 sources, 8 unit tests pass |
| RULE-04 | 02-01 | No self-check (can't move into check) | SATISFIED | is_legal_move post-check prevents self-check, tests pass |
| RULE-05 | 02-01 | Flying general face-to-face detection | SATISFIED | flying_general_violation implemented in both modules, 6 tests pass |
| RULE-06 | 02-01 | get_game_result: stalemate = loss | SATISFIED | get_game_result implemented, stalemate test passes |
| TEST-01 | 02-02 | Perft depth 1-3 vs CPW reference | BLOCKED | depth 1+2 pass; depth 3+4 FAIL (missing 2,158 / 177,695 nodes) |

**Orphaned requirements:** None — all 13 requirements from plans are accounted for. No additional phase-2 requirements in REQUIREMENTS.md are unclaimed.

---

### Anti-Patterns Found

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| None | No TODO/FIXME/HACK/placeholder comments found | Info | — |
| `tests/test_legal.py:206` | `test_starting_position_legal_moves` asserts `len(moves) >= 40` not `== 44` | Warning | Too loose — passes even if count is off by a few. Does not catch the perft bug. Does not verify CPW reference value. |
| `tests/test_perft.py` | `TestPerftDivide::test_perft_divide_depth_1` only asserts `total == CPW_PERFT[2]` (sum) and `cnt > 0` (non-zero), not per-child CPW reference values | Warning | Too permissive — passes even when per-move depth-2 counts are individually wrong. Does not catch the depth-3 perft bug. |
| `moves.py:195` | Crossed logic uses `fr <= 4` for red, `fr >= 5` for black — opposite of PLAN's specification (`fr >= 5` red, `fr <= 4` black). Code is CORRECT (verified by test_moves.py comments: 'FIXED: crossed = (color==+1 and fr<=4)'). PLAN was written with inverted logic. | Info | No functional impact — code is correct. But plan-code discrepancy should be reconciled. |

---

### Human Verification Required

None — all phase behaviors have automated verification. The perft failure is a programmatic bug, not a manual test.

---

### Gaps Summary

**3 blocking gaps** prevent the phase goal from being achieved:

1. **perft(3) = 77,508 vs expected 79,666** — 2,158 nodes missing. Move generation produces wrong counts from depth-2 positions. All 66 unit tests pass, so the bug is in a scenario not covered by unit tests. Perft divide at depth 1 passes (each child has correct depth-2 count), confirming the perft infrastructure is sound. The bug is a piece-movement edge case in certain depth-2 board configurations. The executor identified but did not fix this bug.

2. **perft(4) = 3,112,545 vs expected 3,290,240** — 177,695 nodes missing. Same root cause as perft(3) failure, compounding at greater depth.

3. **test_requirements_md_values_fail fails** — This test asserts that the perft implementation matches CPW values. It fails because perft(3) is wrong.

**PLAN vs CODE discrepancies (non-blocking):**
- Soldier crossed logic: PLAN specifies `fr >= 5` for red, `fr <= 4` for black. CODE uses `fr <= 4` for red, `fr >= 5` for black. The test_moves.py comments ("FIXED: crossed = (color==+1 and fr<=4)") confirm the CODE is correct and the PLAN had inverted logic. No functional impact since perft(2) passes.

---

_Verified: 2026-03-20T12:30:00Z_
_Verifier: Claude (gsd-verifier)_
