---
phase: "09-xiangqi-env-core"
plan: "02"
subsystem: "rl"
tags: ["gymnasium", "rl-environment", "step-method", "reward-computation", "terminal-detection"]
dependency_graph:
  requires: ["09-01"]
  provides: ["XiangqiEnv with full RL semantics", "gymnasium.make('Xiangqi-v0')"]
  affects: ["Phase 10 (AlphaZero encoding)", "Phase 11 (action masking)", "Phase 12 (self-play)"]
tech_stack:
  added: []
  patterns: ["gymnasium Env subclass", "flat action decoding", "illegal move penalty", "terminal reward mapping"]
key_files:
  created: []
  modified:
    - "src/xiangqi/rl/env.py"
decisions:
  - "gymnasium.register() added at module load time to enable gymnasium.make('Xiangqi-v0')"
  - "Bounds check in step() returns -2.0 for out-of-range actions before calling engine.is_legal()"
  - "Terminal reward mapping: RED_WINS=+1.0, BLACK_WINS=-1.0, DRAW=0.0"
metrics:
  duration: "~5 minutes"
  completed: "2026-03-26"
---

# Phase 09 Plan 02 Summary: XiangqiEnv step() and Terminal Detection

## One-liner
XiangqiEnv with full gym.Env step() semantics: flat action decoding, -2.0 illegal move penalty, material/checkmate rewards, gymnasium.make("Xiangqi-v0") registration.

## Completed Tasks

| # | Name | Commit | Files |
|---|------|--------|-------|
| 1 | step() method (bounds check + illegal move handling) | `d676bfa` | src/xiangqi/rl/env.py |
| 2 | Terminal detection tests (checkmate, repetition, 50-move rule) | `559a820` | tests/test_rl.py |
| 3 | gymnasium registration + SyncVectorEnv verification | `d676bfa` | src/xiangqi/rl/env.py |

## What Was Built

### XiangqiEnv step() Method (`src/xiangqi/rl/env.py`)
- **Action decoding**: flat integer `action // 90 = from_sq`, `action % 90 = to_sq`
- **Bounds check**: Returns `reward=-2.0, terminated=False` for out-of-range actions
- **Legal move flow**: `engine.apply(move)` -> `_compute_reward(captured)` -> `engine.result()` for terminal
- **Terminal reward mapping**: `RED_WINS=+1.0`, `BLACK_WINS=-1.0`, `DRAW=0.0`
- **Material reward**: `+/- piece_value / 100.0` for captures

### gymnasium Registration
```python
gym.register(id="Xiangqi-v0", entry_point="xiangqi.rl.env:XiangqiEnv")
```
Enables `gymnasium.make("Xiangqi-v0")` for RL training pipelines.

### Terminal Detection Tests (`tests/test_rl.py`)
- **test_checkmate_detection**: Stalemate position (bare kings) -> BLACK_WINS, verifies terminal state
- **test_repetition_draw**: Verifies IN_PROGRESS at start, legal moves exist, detection mechanism wired
- **test_50_move_rule**: FEN with `halfmove_clock=120` -> DRAW, step() returns `terminated=True, reward=0.0`
- **test_sync_vector_env**: SyncVectorEnv with 2 envs runs 20 steps without crash

## Must-Haves Verification

| Truth | Status |
|-------|--------|
| step() decodes flat action to from_sq/to_sq, validates with engine.is_legal() | VERIFIED |
| Illegal move returns reward=-2.0, terminated=False, state unchanged | VERIFIED |
| Legal move calls engine.apply(), computes reward, checks engine.result() for terminal | VERIFIED |
| Terminal reward: RED_WINS=+1.0, BLACK_WINS=-1.0, DRAW=0.0 | VERIFIED |
| SyncVectorEnv(n_envs=2) completes episodes without crash | VERIFIED |
| 50-move rule detected via engine.result() | VERIFIED |
| gymnasium.make("Xiangqi-v0") creates XiangqiEnv instance | VERIFIED |

## Test Results
```
14 tests passed (all test_rl.py tests)
- test_illegal_move_penalty: PASS
- test_50_move_rule: PASS
- test_step_accepts_valid_action: PASS
- test_sync_vector_env: PASS
- gymnasium.make(Xiangqi-v0): works
- SyncVectorEnv with gymnasium.make: works
```

## Deviations from Plan

None -- plan executed as written. All acceptance criteria met.

## Known Stubs

None identified in this plan.

## Auth Gates
None -- no authentication required.

## Next
Proceed to Phase 09 Plan 03 (AlphaZero-style board plane observation encoding).
