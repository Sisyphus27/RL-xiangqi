---
status: investigating
trigger: "perft(3) from starting position = 77,508 vs expected 79,666 (CPW); missing 2,158 nodes"
created: 2026-03-20T12:38:00Z
updated: 2026-03-20T12:38:00Z
---

## Current Focus

hypothesis: gen_soldier forward_dr is inverted: `forward_dr = +1 if color == +1 else -1` should be `forward_dr = -1 if color == +1 else +1`
test: Monkey-patched gen_soldier with corrected direction; perft(3) = 79,666 ✓
expecting: Flipping `forward_dr` fixes the bug
next_action: Document findings and write diagnosis

## Symptoms
<!-- IMMUTABLE -->

expected: perft(3) = 79,666 (CPW-verified), perft(2) = 1,920
actual: perft(3) = 77,508, perft(2) = 1,920; gap of 2,158 nodes at depth 3
errors: No Python errors; perft(3) test assertion fails
reproduction: `python3 -m pytest tests/test_perft.py::TestPerftStartingPosition::test_perft_depth_3 -v`
started: All 66 unit tests pass; bug appears only in perft depth 3+

## Eliminated
<!-- APPEND only -->

- hypothesis: is_in_check has wrong soldier attack detection
  evidence: is_in_check unit tests (8 cases) all pass; horse, elephant, face-to-face all verified correct
  timestamp: 2026-03-20

- hypothesis: Perft infrastructure (_apply, _perft) has bugs
  evidence: test_perft._apply and legal.apply_move produce identical results; perft(2)=1920 matches CPW
  timestamp: 2026-03-20

- hypothesis: generate_legal_moves wrong
  evidence: perft(2)=1920 matches CPW; perft divide depth 1 sum = 1,920; 44 legal moves confirmed
  timestamp: 2026-03-20

- hypothesis: gen_chariot/gen_horse/gen_cannon/gen_advisor/gen_elephant have bugs
  evidence: 32 unit tests pass; all move generators individually verified
  timestamp: 2026-03-20

- hypothesis: Horse numpy wrap bug (leg at row-1)
  evidence: gen_horse has bounds check `0 <= leg_r < ROWS` before array access
  timestamp: 2026-03-20

- hypothesis: Cannon screen counting wrong
  evidence: gen_cannon uses exactly-1-screen logic; 3 unit tests pass; perft(2) matches CPW
  timestamp: 2026-03-20

- hypothesis: Flying general rule wrong
  evidence: 3 tests in test_legal.py and 3 in test_rules.py pass; flying_general_violation verified correct
  timestamp: 2026-03-20

- hypothesis: Soldier crossed-river logic wrong
  evidence: Crossed logic `fr <= 4` for red, `fr >= 5` for black is CORRECT; verified by test_moves.py comments. The unit tests for soldier movement all pass. The bug is NOT in crossed logic.
  timestamp: 2026-03-20

- hypothesis: Starting FEN wrong or different from pyffish reference
  evidence: Our `from_fen` and `to_fen` round-trip correctly; pyffish `validate_fen` confirms FEN is FEN_OK=1; perft(2)=1920 confirms starting position is correct
  timestamp: 2026-03-20

- hypothesis: Piece encoding mismatch (CPW uses 'rheakaehr' vs our 'rnbakabnr')
  evidence: Both FEN strings are EQUIVALENT (same numeric values, different letters); verified by `from_fen` parsing both and getting identical board arrays; perft(1)=44 and perft(2)=1920 confirm board state equivalence
  timestamp: 2026-03-20

## Evidence
<!-- APPEND only -->

- timestamp: 2026-03-20
  checked: `moves.py::gen_soldier` lines 182-203
  found: `forward_dr = +1 if color == +1 else -1` — red pawn advances toward increasing row (toward row 9 = bottom = red's home in our board). Black pawn advances toward decreasing row (toward row 0 = top = black's home).
  implication: In standard xiangqi (board with black home at TOP, row 0; red home at BOTTOM, row 9): red should advance toward row 0 (top = decreasing row), black should advance toward row 9 (bottom = increasing row). The current direction is INVERTED for both colors.

- timestamp: 2026-03-20
  checked: Perft divide at starting position
  found: Both our implementation and pyffish (Fairy-Stockfish) produce identical perft(2)=1,920 and identical per-child d2 distribution: {40:2, 41:4, 42:2, 43:6, 44:16, 45:14}. However, the specific depth-1 moves differ: our generates a6a7 (red pawn row 6→7) while pyffish generates a4a5 (red pawn row 6→5). 5 moves differ at depth 1; net d2 sum = 1,920 in both (cancelled out).
  implication: Both implementations have different but equally-sized perft trees. The 5 wrong moves produce different subtree sizes at depth 3.

- timestamp: 2026-03-20
  checked: pyffish (Fairy-Stockfish) perft reference
  found: Built pyffish from Fairy-Stockfish source with LARGEBOARDS + ALLVARS flags. pyffish perft(1)=44, perft(2)=1920, perft(3)=79666. Confirms CPW reference values.
  implication: pyffish is the reference implementation.

- timestamp: 2026-03-20
  checked: Perft divide at a4a5 position (red pawn 6,0→5,0)
  found: From this position (pyffish child with d2=1964), our perft(3)=79,260 vs pyffish perft(3)=81,475. Gap=2,215 at this ONE position. The perft(2) from this position = 1,964 in both (match). So the gap emerges at depth 3 (from depth-2 positions). This means `is_legal_move` or subsequent move generation differs at some depth-2 positions.
  implication: The pawn direction bug cascades: wrong depth-1 moves → wrong depth-1 positions → wrong perft(3) counts at depth 2.

- timestamp: 2026-03-20
  checked: Perft divide at starting position (continued)
  found: Our d3 distribution: {1474:2, 1519:2, 1525:2, 1570:1, 1613:2, 1626:2, 1637:2, 1649:2, 1654:2, 1664:2, 1708:2, 1745:2, 1746:2, 1750:2, 1753:2, 1832:2, 1922:2, 1927:2, 1959:2, 1970:1, 2005:4, 2271:2}. pyffish d3 distribution: {1519:2, 1525:2, 1564:2, 1637:2, 1669:2, 1694:2, 1699:2, 1707:2, 1708:2, 1789:2, 1793:2, 1796:2, 1832:2, 1920:3, 1922:2, 1927:2, 1942:2, 1964:2, 1970:1, 2005:4, 2271:2}. Distributions are DIFFERENT. 2 of our children have d3=1474 (pyffish has none), and pyffish has 2 with d3=1564 (we have none).
  implication: The wrong pawn direction produces wrong depth-1 children whose d3 subtrees are systematically smaller.

- timestamp: 2026-03-20
  checked: Monkey-patched perft with corrected gen_soldier
  found: Using `forward_dr = -1 if color == +1 else +1` (flipped from current): perft(1)=44, perft(2)=1920, perft(3)=79666. ALL match CPW reference exactly.
  implication: The pawn direction inversion is the ONLY bug needed to fix. Single-line fix in gen_soldier.

- timestamp: 2026-03-20
  checked: All unit tests vs the bug
  found: test_moves.py has test_red_soldier_pre_river (row 6 → row 7) and test_red_soldier_crossed_river (row 3 → row 4). These tests PASS with the current (WRONG) direction because: row 6→7 is "forward" in the wrong direction (actually backward), but the tests only check that the generated destination matches the test's expectation (which was also written with the wrong assumption about direction). The unit tests are themselves testing the WRONG direction.
  implication: Unit tests for soldier movement are co-dependent with the buggy implementation. They pass but validate the wrong behavior.

## Resolution
<!-- OVERWRITE when found -->

root_cause: gen_soldier has INVERTED forward direction. `forward_dr = +1 if color == +1 else -1` should be `forward_dr = -1 if color == +1 else +1`. In standard xiangqi with black at the top (row 0) and red at the bottom (row 9), red advances toward row 0 (UP = decreasing row = forward_dr=-1) and black advances toward row 9 (DOWN = increasing row = forward_dr=+1). The current code has it backwards for both colors. This causes red pawns to move toward row 9 (their home) instead of toward row 0 (the enemy/forward), and black pawns to move toward row 0 (their home) instead of toward row 9 (the enemy/forward). All unit tests pass because they validate the wrong direction.

fix: In `src/xiangqi/engine/moves.py` line 186, change `forward_dr = +1 if color == +1 else -1` to `forward_dr = -1 if color == +1 else +1`.

verification: With the fix: perft(1)=44 ✓, perft(2)=1920 ✓, perft(3)=79666 ✓ (all CPW-verified). Verified by monkey-patching gen_soldier with the corrected direction and running perft(1), perft(2), perft(3).

files_changed: src/xiangqi/engine/moves.py
