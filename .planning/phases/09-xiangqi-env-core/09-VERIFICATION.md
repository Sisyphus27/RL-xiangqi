---
phase: 09-xiangqi-env-core
verified: 2026-03-27T00:00:00Z
status: passed
score: 16/16 must-haves verified
re_verification: true
previous_verification: 2026-03-26T15:00:00Z
previous_status: passed
previous_score: 13/13
gaps_closed:
  - "WXF 5-field FEN halfmove_clock correctly parsed from parts[3] (plan 09-05)"
  - "Standard 6-field FEN halfmove_clock still correctly parsed from parts[4] (plan 09-05)"
  - "to_fen() roundtrip preserves halfmove_clock (plan 09-05)"
  - "test_fen_halfmove_parsing regression test added (plan 09-05)"
  - "test_50_move_rule_via_wxf_fen UAT regression test added (plan 09-05)"
gaps_remaining: []
regressions: []
---

# Phase 09: XiangqiEnv Core Verification Report

**Phase Goal:** RL Environment Core — Gymnasium XiangqiEnv with legal move mask, canonical observation, step/reward/reset, and SyncVectorEnv support

**Verified:** 2026-03-27T00:00:00Z
**Status:** passed
**Re-verification:** Yes — after plan 09-05 gap closure (WXF FEN halfmove_clock fix)

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | XiangqiEnv.reset() returns obs (16,10,9) float32 and info with legal_mask and piece_masks | VERIFIED | All 17 pytest tests pass; obs.shape==(16,10,9) confirmed |
| 2 | XiangqiEnv.action_space is Discrete(8100) | VERIFIED | test_action_space_discrete_8100 passes; action_space.n==8100 |
| 3 | XiangqiEnv.observation_space is Box(0.0, 1.0, (16,10,9), float32) | VERIFIED | test_observation_space_box passes; Box properties verified |
| 4 | info['piece_masks'] is dict with keys 0-6, each np.ndarray (8100,) float32 | VERIFIED | test_piece_masks_shape passes; union==legal_mask verified programmatically |
| 5 | Two XiangqiEnv instances maintain independent state | VERIFIED | test_env_instances_independent passes |
| 6 | step() decodes flat action to from_sq/to_sq, validates with engine.is_legal() | VERIFIED | env.py lines 76-101 decode action//90, action%90, then is_legal(); test_step_accepts_valid_action passes |
| 7 | Illegal move returns reward=-2.0, terminated=False, state unchanged | VERIFIED | test_illegal_move_penalty passes; obs_before==obs_after after step(9999) |
| 8 | Legal move calls engine.apply(), computes reward, checks engine.result() for terminal | VERIFIED | step() lines 104-118 implement full flow; test_step_accepts_valid_action confirms |
| 9 | Terminal reward: RED_WINS=+1.0, BLACK_WINS=-1.0, DRAW=0.0 | VERIFIED | step() lines 113-118; test_50_move_rule verifies DRAW=0.0 |
| 10 | SyncVectorEnv(n_envs=2) completes episodes without crash | VERIFIED | test_sync_vector_env runs 20 steps with alternating actions; passes |
| 11 | 50-move rule detected via engine.result() | VERIFIED | test_50_move_rule: halfmove=120 -> DRAW -> terminated=True, reward=0.0 |
| 12 | Entry point registered in pyproject.toml for gymnasium discoverability | VERIFIED | [project.entry-points."gymnasium.envs"] Xiangqi=xiangqi.rl.env:XiangqiEnv |
| 13 | gymnasium.make('Xiangqi-v0') works after xiangqi import triggers registration | VERIFIED | test_gymnasium_make_no_import passes in isolated subprocess |
| 14 | WXF 5-field FEN (no en passant) correctly parses halfmove_clock from parts[3] | VERIFIED | from_fen('... w - 120 1') returns halfmove=120; test_fen_halfmove_parsing passes |
| 15 | Standard 6-field FEN (with en passant) still correctly parses halfmove_clock from parts[4] | VERIFIED | from_fen('... w - - 120 1') returns halfmove=120; test_fen_halfmove_parsing passes |
| 16 | FEN with halfmove_clock>=100 via reset(options={'fen': ...}) triggers DRAW on step() | VERIFIED | test_50_move_rule_via_wxf_fen passes: halfmove=120 -> engine.result()=='DRAW' -> terminated=True, reward=0.0 |

**Score:** 16/16 truths verified

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/xiangqi/rl/env.py` | XiangqiEnv gym.Env subclass | VERIFIED | 243 lines; reset/step/_get_observation/_get_info/_build_legal_mask/_build_piece_masks/_canonical_board/_compute_reward all present |
| `src/xiangqi/rl/__init__.py` | rl package exports XiangqiEnv | VERIFIED | 4 lines; imports and re-exports XiangqiEnv from env.py |
| `src/xiangqi/__init__.py` | Top-level re-export | VERIFIED | 4 lines; re-exports XiangqiEnv from xiangqi.rl |
| `tests/test_rl.py` | RL environment tests | VERIFIED | 363 lines; 17 test functions; all pass |
| `pyproject.toml` | gymnasium dependency + entry points | VERIFIED | gymnasium>=1.0,<2.0 in dependencies; [project.entry-points."gymnasium.envs"] Xiangqi=xiangqi.rl.env:XiangqiEnv |
| `src/xiangqi/engine/constants.py` | from_fen() with WXF 5-field detection | VERIFIED | lines 73-83: checks parts[3][0].isdigit() for WXF detection |
| `src/xiangqi/engine/engine.py` | to_fen() passes halfmove_clock | VERIFIED | line 208: to_fen(self._state.board, self._state.turn, self._state.halfmove_clock) |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| XiangqiEnv | gym.Env | inheritance | WIRED | class XiangqiEnv(gym.Env) |
| XiangqiEnv.reset() | XiangqiEngine | lazy import _get_engine_class() | WIRED | Line 56 in env.py |
| step() | engine.is_legal() | encode_move(from_sq, to_sq) | WIRED | Bounds check, then is_legal() at line 94 |
| step() | engine.apply() | move encoding | WIRED | Called at line 104 after is_legal() check |
| step() | engine.result() | terminal detection | WIRED | Called at line 107; maps to terminal reward |
| pyproject.toml entry-point | gymnasium registry | pip install -e . | WIRED | Xiangqi entry found via importlib.metadata; gymnasium.make works |
| env.py | gym.register() | module-level call | WIRED | gym.register() at line 242 |
| SyncVectorEnv | XiangqiEnv | gymnasium.make("Xiangqi-v0") | WIRED | Registration at module load enables make() |
| from_fen() | halfmove_clock | WXF 5-field detection | WIRED | parts[3] for WXF, parts[4] for standard; both verified |
| engine.to_fen() | constants.to_fen() | halfmove_clock argument | WIRED | passes self._state.halfmove_clock; roundtrip verified |

---

## Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|-------------------|--------|
| XiangqiEnv.reset() | obs (16,10,9) | _get_observation() from engine.board | YES | Computed from actual engine board state |
| XiangqiEnv._get_info() | legal_mask (8100,) | _build_legal_mask() from engine.legal_moves() | YES | Computed from actual legal moves |
| XiangqiEnv._get_info() | piece_masks dict | _build_piece_masks() from engine.legal_moves() | YES | Per-type masks from actual legal moves; union==legal_mask |
| XiangqiEnv.step() | reward (float) | _compute_reward(captured) or terminal_reward | YES | Material reward from captured piece; terminal from engine.result() |
| from_fen() | halfmove_clock | WXF or standard FEN parsing | YES | Correctly from parts[3] (WXF) or parts[4] (standard) |
| engine.to_fen() | FEN string | self._state.board + halfmove_clock | YES | Produces real FEN; roundtrip preserves halfmove_clock |

---

## Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| WXF 5-field FEN halfmove=120 parsed | from_fen('... w - 120 1') | halfmove=120 | PASS |
| Standard 6-field FEN halfmove=120 parsed | from_fen('... w - - 120 1') | halfmove=120 | PASS |
| STARTING_FEN halfmove=0 | from_fen(STARTING_FEN) | halfmove=0 | PASS |
| Engine at halfmove>=100 returns DRAW | engine.result() at halfmove=120 | "DRAW" | PASS |
| FEN roundtrip preserves halfmove_clock | starting().to_fen().from_fen() | halfmove=0 preserved | PASS |
| Illegal move returns -2.0 | env.step(9999) | reward=-2.0, terminated=False, illegal_move=True | PASS |
| State unchanged after illegal move | obs_before vs obs_after | equal | PASS |
| piece_masks union equals legal_mask | np.maximum union vs legal_mask | equal | PASS |
| Entry point discoverable | importlib.metadata.entry_points() | Xiangqi=xiangqi.rl.env:XiangqiEnv | PASS |
| gymnasium.make('Xiangqi-v0') | subprocess isolation test | obs.shape=(16,10,9), piece_masks in info | PASS |
| All 17 RL tests | pytest tests/test_rl.py -x -q | 17 passed in 0.38s | PASS |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| R1 | 09-01, 09-02, 09-04 | Gymnasium Env Interface (reset/step/spaces/make) | SATISFIED | XiangqiEnv inherits gym.Env; all methods implemented; gymnasium.make works |
| R2 | 09-01 | piece_masks dict (7 keys 0-6, (8100,) float32) | SATISFIED | test_piece_masks_shape passes; union==legal_mask verified |
| R3 | 09-01 | AlphaZero board planes (16 channels + canonical rotation) | SATISFIED | _get_observation() builds all 16 planes; _canonical_board() implements rot90 for black |
| R4 | 09-01 | Legal move masking (info['legal_mask'], is_legal() check) | SATISFIED | _build_legal_mask from engine.legal_moves(); step uses is_legal() |
| R5 | 09-02 | Reward signal (terminal +/-1.0/0.0; material +/-piece/100; illegal -2.0) | SATISFIED | step() lines 107-118, 228-238; test_illegal_move_penalty passes |
| R6 | 09-02, 09-03, 09-05 | Terminal detection (checkmate/stalemate/50-move/repetition) | SATISFIED | engine.result() handles all; test_50_move_rule, test_fen_halfmove_parsing, test_50_move_rule_via_wxf_fen pass |
| R7 | Phase 12 | Self-play E2E validation (100-game random vs random) | ORPHANED | Phase 12 scope, not Phase 09 |
| R8 | 09-01, 09-02, 09-03 | SyncVectorEnv thread safety | SATISFIED | test_sync_vector_env passes 20 steps; test_env_instances_independent passes |

**Note on R7:** Self-play E2E validation is Phase 12 scope. Not a gap for Phase 09.

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| None | — | No TODO/FIXME/PLACEHOLDER comments | Info | Clean codebase |
| None | — | No stub return patterns (return null, {}, []) | Info | All methods have substantive implementations |
| None | — | No hardcoded empty data in rendering paths | Info | All data flows from actual engine state |

---

## Human Verification Required

None. All observable behaviors have automated verification. XiangqiEnv is a library (no UI), so no visual/human testing is needed.

---

## Gaps Summary

No gaps found. All 16 must-haves verified (13 from initial verification + 3 new from plan 09-05 gap closure). The phase goal is fully achieved.

**Plan 09-05 gap closure verified:**
- from_fen() WXF 5-field detection: parts[3][0].isdigit() correctly identifies WXF format
- Standard 6-field still works: parts[4] correctly parsed for en-passant-present format
- to_fen() includes actual halfmove_clock: roundtrip preserves value
- Regression tests: test_fen_halfmove_parsing and test_50_move_rule_via_wxf_fen added and passing

**Plan completion summary:**

| Plan | Status | Key deliverables |
|------|--------|-----------------|
| 09-01 | COMPLETE | XiangqiEnv core: reset, obs/action spaces, piece_masks, info dict |
| 09-02 | COMPLETE | step() with action decoding, illegal move penalty, terminal detection |
| 09-03 | COMPLETE | SyncVectorEnv integration, 50-move rule validation |
| 09-04 | COMPLETE | gymnasium entry point registration in pyproject.toml |
| 09-05 | COMPLETE | WXF FEN halfmove_clock parsing fix + regression tests |

---

_Verified: 2026-03-27T00:00:00Z_
_Verifier: Claude (gsd-verifier)_
