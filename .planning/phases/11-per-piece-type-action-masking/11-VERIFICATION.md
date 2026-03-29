---
phase: 11-per-piece-type-action-masking
verified: 2026-03-28T12:00:00Z
status: passed
score: 8/8 must-haves verified
---

# Phase 11: Per-piece-type Action Masking Verification Report

**Phase Goal:** Add per-piece-type action masking public API (R4) and fix reward signal (R5) in XiangqiEnv.
**Verified:** 2026-03-28
**Status:** PASSED
**Re-verification:** No -- initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | get_legal_mask(player=1) returns non-zero mask for current turn player (red at start) | VERIFIED | Smoke test: mask.sum()=44.0, shape=(8100,), dtype=float32. Test `test_get_legal_mask_current_player` passes. |
| 2 | get_legal_mask(player=-1) returns all-zero mask when red to move | VERIFIED | Smoke test: np.all(mask == 0)=True. Test `test_get_legal_mask_non_current_player` passes. |
| 3 | get_piece_legal_mask(piece_type=4, player=1) returns chariot-only legal moves | VERIFIED | Smoke test: mask.sum()=4.0, shape=(8100,), dtype=float32. Test `test_get_piece_legal_mask_current_player` passes. |
| 4 | get_piece_legal_mask(piece_type=4, player=-1) returns all-zero mask when red to move | VERIFIED | Smoke test: np.all(mask == 0)=True. Test `test_get_piece_legal_mask_non_current_player` passes. |
| 5 | Red capturing Black Horse gives +0.04 reward (not -0.04) | VERIFIED | _compute_reward(-4, 45) returns 0.04. Sign logic: `sign = -1 if captured > 0 else 1` (corrected). Tests `test_material_capture_reward` and `test_reward_sign_correct` pass. |
| 6 | Red capturing Black Soldier at row 6 (pre-river) gives +0.01 | VERIFIED | _compute_reward(-7, 27) returns 0.01. Row 3, Black pre-river (row < 5), value=1. Test `test_soldier_pre_river_value` passes. |
| 7 | Red capturing Black Soldier at row 4 (post-river) gives +0.02 | VERIFIED (with correction) | The truth statement says "row 4" but row 4 for Black soldier is pre-river (reward=0.01). Post-river for Black starts at row 5: _compute_reward(-7, 45)=0.02. The test `test_soldier_post_river_value` correctly tests at row 5. Code and tests are correct per D-01 design; the truth statement has a row-number inaccuracy. |
| 8 | Terminal reward remains +1.0/-1.0/0.0 unchanged | VERIFIED | Code inspection: env.py lines 113-118 show hardcoded `reward = 1.0`, `-1.0`, `0.0` for RED_WINS, BLACK_WINS, DRAW. No modification in Phase 11. Existing tests `test_checkmate_detection`, `test_50_move_rule`, `test_50_move_rule_via_wxf_fen` all pass. |

**Score:** 8/8 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/xiangqi/rl/env.py` line 226: `def get_legal_mask` | Public API method | VERIFIED | Exists at line 226, returns (8100,) float32, delegates to `_build_legal_mask()`, non-current player returns zeros |
| `src/xiangqi/rl/env.py` line 241: `def get_piece_legal_mask` | Public API method | VERIFIED | Exists at line 241, returns (8100,) float32, delegates to `_build_piece_masks()`, validates piece_type range 0-6 |
| `src/xiangqi/rl/env.py` line 260: `def _compute_reward(self, captured: int, to_sq: int = -1)` | Fixed reward with to_sq | VERIFIED | Exists at line 260, sign corrected (`-1 if captured > 0 else 1`), dynamic soldier value per D-01 |
| `tests/test_rl.py` lines 533-659: 8 new test functions | Test coverage for R4/R5 | VERIFIED | 8 functions confirmed: test_get_legal_mask_current_player, test_get_legal_mask_non_current_player, test_get_piece_legal_mask_current_player, test_get_piece_legal_mask_non_current_player, test_material_capture_reward, test_soldier_pre_river_value, test_soldier_post_river_value, test_reward_sign_correct |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| env.py::step() line 110 | env.py::_compute_reward() | `reward = self._compute_reward(captured, to_sq)` | WIRED | Pattern `self._compute_reward(captured, to_sq)` found at line 110 |
| env.py::get_legal_mask() line 239 | env.py::_build_legal_mask() | `return self._build_legal_mask()` | WIRED | Delegation at line 239 |
| env.py::get_piece_legal_mask() line 257 | env.py::_build_piece_masks() | `masks = self._build_piece_masks()` | WIRED | Delegation at line 257 |
| tests/test_rl.py | env.py::get_legal_mask() | Direct method call | WIRED | 2 calls: lines 538, 553 |
| tests/test_rl.py | env.py::get_piece_legal_mask() | Direct method call | WIRED | 4 calls: lines 564, 574, 576, 585 |
| tests/test_rl.py | env.py::_compute_reward() | Direct method call | WIRED | 10 calls: lines 600-658 |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|-------------------|--------|
| get_legal_mask() | mask (8100,) | self._build_legal_mask() -> iterates self._engine.legal_moves() | Yes: 44 legal moves at start | FLOWING |
| get_piece_legal_mask() | masks[piece_type] | self._build_piece_masks() -> iterates self._engine.legal_moves() + canonical board lookup | Yes: chariot mask sum=4.0 | FLOWING |
| _compute_reward() | sign, piece_value | PIECE_VALUES dict + to_sq row computation | Yes: dynamic soldier value based on position | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| All 29 tests pass | `/c/software/miniconda/envs/xqrl/python.exe -m pytest tests/test_rl.py -v` | 29 passed in 0.44s | PASS |
| get_legal_mask(1) non-zero | Python smoke test | sum=44.0 | PASS |
| get_legal_mask(-1) all-zero | Python smoke test | np.all(mask==0)=True | PASS |
| get_piece_legal_mask(4, 1) non-zero | Python smoke test | sum=4.0 | PASS |
| get_piece_legal_mask(4, -1) all-zero | Python smoke test | np.all(mask==0)=True | PASS |
| _compute_reward(-4, 45) = +0.04 | Python smoke test | 0.04 | PASS |
| _compute_reward(-7, 27) = +0.01 | Python smoke test | 0.01 | PASS |
| _compute_reward(-7, 45) = +0.02 | Python smoke test | 0.02 | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| R4: get_legal_mask(player) | 11-01 | Full 8100-element mask, non-current player returns zeros | SATISFIED | Method exists at env.py:226, 2 tests cover it |
| R4: get_piece_legal_mask(piece_type, player) | 11-01 | Per-type mask, invalid type returns zeros | SATISFIED | Method exists at env.py:241, 2 tests cover it |
| R4: Illegal move penalty | 11-01 | -2.0 penalty, no state change | SATISFIED | Existing test `test_illegal_move_penalty` passes, step() code unchanged |
| R4: Mask uses engine legal_moves() | 11-01 | Delegates to _build_legal_mask()/_build_piece_masks() | SATISFIED | get_legal_mask() calls _build_legal_mask() which iterates engine.legal_moves() |
| R5: Terminal reward +1/-1/0 | 11-01 | Unchanged from previous implementation | SATISFIED | Code at env.py:113-118, tests pass |
| R5: Material capture reward piece_value/100 | 11-01 | Sign corrected, dynamic soldier value | SATISFIED | _compute_reward with corrected sign, tests verify 6 piece types |
| R5: Soldier=1/2 (river crossing) | 11-01 | Pre-river=1, post-river=2 | SATISFIED | Dynamic value in _compute_reward, tests `test_soldier_pre_river_value` and `test_soldier_post_river_value` |
| R5: Illegal penalty -2.0 | 11-01 | Unchanged | SATISFIED | step() lines 83-101 |

No orphaned requirements found -- R4 and R5 are the only requirements mapped to Phase 11, and both are covered by Plans 01 and 02.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (none) | -- | -- | -- | -- |

No TODO/FIXME/PLACEHOLDER/stub patterns found in modified files. No empty implementations, no console.log-only handlers.

### Human Verification Required

None. All behaviors have automated test coverage and behavioral spot-checks passed.

### Gaps Summary

No gaps found. Both plans (11-01 and 11-02) executed successfully:

- **Plan 01** (implementation): Two public methods added (get_legal_mask, get_piece_legal_mask), reward sign bug fixed, dynamic soldier river-crossing value implemented. 21 existing tests continue passing.
- **Plan 02** (testing): 8 new test functions added covering R4 (4 tests) and R5 (4 tests). All 29 tests pass.

Minor note: Truth 7 stated "row 4 (post-river)" but row 4 for a Black soldier is pre-river per the design (D-01: Black crossed at row >= 5). The code and tests correctly implement post-river starting at row 5 for Black soldiers. This is a truth-statement inaccuracy, not a code defect.

---

_Verified: 2026-03-28_
_Verifier: Claude (gsd-verifier)_
