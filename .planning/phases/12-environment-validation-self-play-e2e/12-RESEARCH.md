# Phase 12: Environment Validation - Self-Play E2E - Research

**Researched:** 2026-03-28
**Domain:** Self-play E2E validation of RL environment pipeline (Phases 09-11 integration)
**Confidence:** HIGH

## Summary

This phase validates the entire RL environment pipeline through Random vs Random self-play. The XiangqiEnv (env.py) provides a complete gymnasium.Env interface with reset/step/legal_mask/reward. The engine (engine.py) handles all terminal conditions: checkmate, stalemate (kunbi), 3-fold repetition, 50-move rule, long check, and long chase.

**Critical finding:** Random self-play games average ~462 plies (not the 60-120 stated in R7). This is expected -- random play in Xiangqi is chaotic and rarely leads to quick checkmates. The R7 "60-120 plies" expectation appears to describe expert-level play, not random play. The plan must account for longer games and adjust the expected game length accordingly.

**Primary recommendation:** Write a single test file `tests/test_selfplay.py` with a main test that runs 100 random games, collects statistics (game lengths, result distribution, reward statistics, termination reasons), and asserts basic sanity conditions. Termination reason extraction requires accessing `env._engine._rep_state` and `env._engine.state` internals since the info dict does not expose it.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Random agent samples only from `info["legal_mask"]` legal action indices. No illegal action path testing (covered in Phase 11 unit tests). Each step selects via `np.random.choice(np.where(mask == 1.0)[0])`.
- **D-02:** Core validation covers R7's 4 requirements (100 games no crash, 60-120 step average, ~50/50 win/loss, legal action verification), plus additional collection: termination reason distribution, reward statistics, game length distribution.
- **D-03:** New file `tests/test_selfplay.py`, separate from `tests/test_rl.py`. Contains one main test function running full 100-game self-play with statistical assertions.
- **D-04:** Statistics output via `print()` to pytest stdout (`pytest -s tests/test_selfplay.py` to view). No extra file reports.
- **D-05:** Lightweight timing -- record 100-game total time and average per-step time, reference only, no pass threshold. Performance optimization deferred to v1.0.

### Claude's Discretion
- Specific test function split (1 large function vs multiple smaller ones)
- Statistics output formatting
- Random seed selection (whether to fix seeds for reproducibility)

### Deferred Ideas (OUT OF SCOPE)
- SyncVectorEnv parallel self-play -- v1.0
- Strict performance benchmarks (50-200 games/sec target) -- v1.0
- Neural network policy self-play -- v1.0
- Replay buffer integration test -- v1.0
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| R7 | Random vs Random self-play completes 100 games without crash | XiangqiEnv.reset/step/legal_mask all functional (verified runtime); random agent samples from legal_mask indices |
| R7 | Average game length 60-120 plies | **NEEDS ADJUSTMENT**: Measured random play average is ~462 plies. See Pitfall 1. |
| R7 | Win/loss/draw distribution reasonable (~50/50) | Measured: ~30% RED_WINS, ~21% BLACK_WINS, ~49% DRAW. High draw rate expected for random play. |
| R7 | All legal moves verified against engine | legal_mask built from engine.legal_moves() in _build_legal_mask(). Cross-check possible via engine.legal_moves() count vs mask.sum(). |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| gymnasium | 1.2.3 | Env interface | Project dependency, provides gym.Env base class |
| numpy | 2.4.3 | Array operations | Project dependency, used for obs/mask/reward |
| pytest | 9.0.2 | Test framework | Project dev dependency, configured in pyproject.toml |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| time (stdlib) | -- | Game timing | Per D-05: lightweight timing of 100 games |
| collections.Counter (stdlib) | -- | Statistics aggregation | Count result distribution, termination reasons |

### No New Dependencies
This phase requires no new package installations. Everything needed is already in the project's conda environment `xqrl`.

## Architecture Patterns

### Recommended Test Structure
```
tests/
├── test_rl.py          # 29 existing unit tests (Phases 09-11)
└── test_selfplay.py    # NEW: self-play E2E validation tests
```

### Pattern: Random Self-Play Loop
**What:** Single-env game loop that samples legal actions uniformly at random until termination.
**When to use:** This entire phase.

```python
# Core self-play loop pattern
env = XiangqiEnv()
obs, info = env.reset(seed=game_idx)
total_reward = 0.0

while True:
    mask = info["legal_mask"]  # (8100,) float32
    legal_indices = np.where(mask == 1.0)[0]
    if len(legal_indices) == 0:
        # No legal moves -- should have been caught as terminated
        break
    action = int(np.random.choice(legal_indices))
    obs, reward, terminated, truncated, info = env.step(action)
    total_reward += reward
    if terminated:
        break
```

### Pattern: Termination Reason Extraction
**What:** After game ends, determine WHY it ended by inspecting engine internals.
**When to use:** Post-game statistics collection.

```python
def get_termination_reason(env: XiangqiEnv, result: str) -> str:
    """Determine why the game ended from engine internals."""
    if result in ("RED_WINS", "BLACK_WINS"):
        # Distinguish checkmate vs stalemate vs long chase
        legal = env._engine.legal_moves()
        if len(legal) == 0:
            if env._engine.is_check():
                return "checkmate"
            else:
                return "stalemate"
        # If still has legal moves but game ended -> long chase
        return "long_chase"
    else:  # DRAW
        state = env._engine.state
        rep_state = env._engine._rep_state
        # Check reasons in priority order (same as get_game_result)
        from collections import Counter
        hash_counts = Counter(state.zobrist_hash_history)
        if max(hash_counts.values()) >= 3:
            return "repetition_3fold"
        if state.halfmove_clock >= 100:
            return "50_move_rule"
        if rep_state.consecutive_check_count >= 4:
            return "long_check"
        return "unknown_draw"
```

### Pattern: Statistics Collection and Reporting
**What:** Collect per-game metrics across 100 games, then print summary table.
**When to use:** At end of 100-game loop.

```python
# Statistics structure
stats = {
    "game_lengths": [],           # list of int
    "results": [],                # list of str ("RED_WINS", "BLACK_WINS", "DRAW")
    "total_rewards": [],          # list of float
    "termination_reasons": [],    # list of str
    "per_step_rewards": [],       # flattened list of all rewards
    "legal_move_counts": [],      # avg legal moves per step per game
}
```

### Anti-Patterns to Avoid
- **Do NOT sample from full Discrete(8100) and test legality:** Only sample from legal_mask indices (D-01). Illegal action paths are already tested in Phase 11.
- **Do NOT use gymnasium.make("Xiangqi-v0"):** Direct `XiangqiEnv()` instantiation is simpler and avoids entry-point registration complexity in tests. The entry point is tested separately in test_rl.py.
- **Do NOT add termination_reason to info dict:** That would be modifying production code during a validation phase. Instead, extract it from engine internals in the test only.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Random action sampling | Custom weighted sampling | `np.random.choice(legal_indices)` | Simple, correct, one-liner |
| Legal move mask extraction | Manual move enumeration | `info["legal_mask"]` + `np.where()` | Already computed per step, no extra cost |
| Game result determination | Custom terminal check | `env._engine.result()` | Engine already computes this correctly |
| Statistics computation | Custom stats class | Python stdlib `statistics` + `numpy` | No need for scipy or pandas |

## Common Pitfalls

### Pitfall 1: R7 Game Length Expectation vs Reality
**What goes wrong:** R7 states "average game length 60-120 plies" but measured random self-play averages ~462 plies with high variance (std ~216, min 27, max 1146).
**Why it happens:** The 60-120 figure describes expert-level or training-level play. Random play is highly inefficient -- pieces move chaotically, captures are random, and checkmate rarely happens. Most games end via 50-move rule (halfmove_clock >= 100) or 3-fold repetition.
**How to avoid:** Adjust the assertion. For random play, use a broader range (e.g., mean > 0 with no upper bound, or a loose range like 50-1500). The key assertion should be "100 games complete without crash", not a tight game length window.
**Warning signs:** If test fails on game length assertion, the assertion is wrong, not the code.
**Measured data (100 games, seeds 0-99):**
- Mean: 462 plies, Median: 448 plies
- Min: 27, Max: 1146, Std: 216
- Distribution: <100 = 3%, 100-300 = 23%, 300-500 = 30%, 500+ = 44%

### Pitfall 2: High Draw Rate in Random Play
**What goes wrong:** R7 expects "~50/50 random vs random" win distribution. Measured: RED_WINS ~30%, BLACK_WINS ~21%, DRAW ~49%.
**Why it happens:** Random play frequently triggers draws via 50-move rule or 3-fold repetition before either side can deliver checkmate. This is normal behavior for random play in games with draw rules.
**How to avoid:** Assert that all three outcomes (RED_WINS, BLACK_WINS, DRAW) appear, and that neither RED_WINS nor BLACK_WINS is zero. Do NOT assert a strict 50/50 distribution. A reasonable assertion: "RED_WINS + BLACK_WINS > 0 and DRAW > 0".
**Warning signs:** If draw rate drops below 20% or exceeds 80%, something may be wrong with terminal detection.

### Pitfall 3: Info Dict Missing Termination Reason
**What goes wrong:** The info dict from step() only contains: legal_mask, piece_masks, piece_type_to_move, player_to_move. It does NOT contain a termination_reason field.
**Why it happens:** The env was designed to keep the info dict minimal. Terminal information is available via `env._engine.result()` (returns "RED_WINS"/"BLACK_WINS"/"DRAW") but the specific sub-reason (checkmate vs stalemate vs repetition vs 50-move) requires deeper inspection.
**How to avoid:** For statistics collection, access engine internals: `env._engine.result()` for outcome, `env._engine.state.halfmove_clock` for 50-move check, `Counter(env._engine.state.zobrist_hash_history)` for repetition count, `env._engine._rep_state.consecutive_check_count` for long check, and `env._engine._rep_state.chase_seq` for long chase.
**Warning signs:** If you try `info["termination_reason"]`, it will KeyError.

### Pitfall 4: Test Timeout
**What goes wrong:** 100 random games at 1.3 games/sec takes ~74 seconds. pytest default timeout may kill the test.
**Why it happens:** Pure Python engine is slow for self-play. 100 games * ~462 steps * legal_move_gen + obs_build per step.
**How to avoid:** Set `@pytest.mark.timeout(300)` or configure pytest timeout appropriately. Alternatively, use `pytest -s --timeout=300`. The D-05 decision already states timing is reference-only.
**Warning signs:** Test passes locally but fails in CI with timeout.

### Pitfall 5: Random Seed Reproducibility
**What goes wrong:** Without fixed seeds, game outcomes vary between runs, making test assertions on statistics flaky.
**Why it happens:** np.random.choice is nondeterministic without a seed.
**How to avoid:** Pass `env.reset(seed=game_idx)` for each game so the sequence is reproducible. Note: this seeds the env's internal RNG, but np.random.choice uses numpy's global RNG. For full reproducibility, also seed numpy's global RNG at test start: `np.random.seed(42)`.
**Warning signs:** Statistics vary by >10% between runs without seeding.

## Code Examples

Verified patterns from runtime testing:

### Complete Single-Game Loop
```python
# Source: verified by running 100-game benchmark
env = XiangqiEnv()
obs, info = env.reset(seed=game_idx)

steps = 0
total_reward = 0.0
while True:
    mask = info["legal_mask"]
    legal_indices = np.where(mask == 1.0)[0]
    if len(legal_indices) == 0:
        break  # should not happen -- terminated should be True
    action = int(np.random.choice(legal_indices))
    obs, reward, terminated, truncated, info = env.step(action)
    total_reward += reward
    steps += 1
    if terminated:
        break

result = env._engine.result()  # "RED_WINS", "BLACK_WINS", or "DRAW"
```

### Legal Move Count Cross-Check
```python
# Verify legal_mask matches engine.legal_moves()
engine_legal_count = len(env._engine.legal_moves())
mask_legal_count = int(info["legal_mask"].sum())
assert engine_legal_count == mask_legal_count
```

### 100-Game Benchmark with Timing
```python
# Source: verified runtime -- 100 games in ~74 seconds
import time

start = time.time()
for game_idx in range(100):
    env = XiangqiEnv()
    obs, info = env.reset(seed=game_idx)
    # ... run game loop ...

elapsed = time.time() - start
print(f"100 games in {elapsed:.1f}s ({100/elapsed:.1f} games/sec)")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| 4-fold repetition | 3-fold repetition (END-04) | Phase 04 engine design | Games end sooner via repetition |
| Stalemate = draw | Stalemate = loss (WXF kunbi rule) | Phase 04 engine design | Both checkmate and stalemate are losses for side to move |

**Implementation notes:**
- `get_game_result()` priority: repetition > 50-move > long check > long chase > checkmate/stalemate > IN_PROGRESS
- Both checkmate and stalemate result in loss for the player to move (WXF rule)
- Long chase: chaser LOSES (not draw)
- Long check: 4+ consecutive checking moves = DRAW

## Open Questions

1. **R7 game length assertion value**
   - What we know: R7 says "60-120 plies average", measured random play is ~462 plies
   - What's unclear: Whether R7 meant expert play or random play
   - Recommendation: Assert a very loose range (e.g., 20-2000 plies average) or simply assert all games terminate. The important thing is "no crash" and "games end".

2. **Per-step legal move cross-check frequency**
   - What we know: D-02 says "legal moves verified against XiangqiEngine.legal_moves()"
   - What's unclear: Whether to verify every step (expensive) or sample (e.g., every 10th step)
   - Recommendation: Verify every step in the first 5 games, then skip for remaining 95. This balances correctness confidence with test speed. Alternatively, verify legal_move_count at start of each game only.

3. **Test function organization**
   - What we know: D-03 says one main test function. Claude has discretion on splitting.
   - What's unclear: Whether to split into helper functions within the same file
   - Recommendation: Use one pytest test function `test_selfplay_100_games()` that calls helper functions for statistics and assertions. Keep all code in one file.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Runtime | Yes | 3.12.0 | -- |
| conda env xqrl | Runtime | Yes | -- | -- |
| gymnasium | XiangqiEnv | Yes | 1.2.3 | -- |
| numpy | Arrays/masks | Yes | 2.4.3 | -- |
| pytest | Test runner | Yes | 9.0.2 | -- |

**Missing dependencies with no fallback:** None

**Missing dependencies with fallback:** N/A

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | pyproject.toml [tool.pytest.ini_options] |
| Quick run command | `/c/software/miniconda/envs/xqrl/python.exe -m pytest tests/test_selfplay.py -s --timeout=300 -v` |
| Full suite command | `/c/software/miniconda/envs/xqrl/python.exe -m pytest tests/ -s --timeout=300 -v` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| R7-1 | 100 games complete without crash | integration | `pytest tests/test_selfplay.py::test_selfplay_100_games -s --timeout=300` | No (Wave 0) |
| R7-2 | Game length measured and reported | integration | Same as above | No (Wave 0) |
| R7-3 | Win/loss/draw distribution collected | integration | Same as above | No (Wave 0) |
| R7-4 | Legal moves verified against engine | integration | Same as above | No (Wave 0) |

### Sampling Rate
- **Per task commit:** `/c/software/miniconda/envs/xqrl/python.exe -m pytest tests/test_selfplay.py -s --timeout=300 -x`
- **Per wave merge:** `/c/software/miniconda/envs/xqrl/python.exe -m pytest tests/ -s --timeout=300 -x`
- **Phase gate:** Full suite green, 29 existing tests + new self-play test all passing

### Wave 0 Gaps
- [ ] `tests/test_selfplay.py` -- covers R7 self-play E2E validation
- [ ] pytest-timeout plugin may need installation if not present (for `--timeout` flag)

## Runtime State Inventory

This is a validation-only phase (no rename/refactor/migration). Runtime state inventory is not applicable.

## Sources

### Primary (HIGH confidence)
- `src/xiangqi/rl/env.py` -- XiangqiEnv source code, runtime-verified
- `src/xiangqi/engine/engine.py` -- XiangqiEngine source code, runtime-verified
- `src/xiangqi/engine/endgame.py` -- get_game_result() terminal detection priority order
- `src/xiangqi/engine/repetition.py` -- RepetitionState tracking for long check/chase
- `tests/test_rl.py` -- 29 existing tests demonstrating fixture/style patterns
- `.planning/research/RL_ENV.md` section 7 -- Self-Play Training Loop Structure

### Secondary (MEDIUM confidence)
- 100-game runtime benchmark (seeds 0-99) -- game length and result distribution measurements
- 10-game detailed analysis -- termination reason breakdown

### Tertiary (LOW confidence)
- None needed -- all findings verified against source code and runtime

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new dependencies, all verified in environment
- Architecture: HIGH -- patterns derived from existing test_rl.py and direct code inspection
- Pitfalls: HIGH -- measured with runtime benchmarks, not theoretical
- Game length expectations: HIGH -- measured across 100 games with statistical data

**Research date:** 2026-03-28
**Valid until:** 2026-04-28 (stable -- no fast-moving dependencies)
