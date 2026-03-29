# Phase 11: Per-piece-type Action Masking - Research

**Researched:** 2026-03-28
**Domain:** Gymnasium RL environment action masking and reward signal design
**Confidence:** HIGH

## Summary

Phase 11 upgrades XiangqiEnv's action masking and reward signal from internal implementation to a public API. Two public methods (`get_legal_mask` and `get_piece_legal_mask`) wrap existing internal methods. The reward signal needs two fixes: (1) the sign logic in `_compute_reward` is inverted -- Red capturing Black pieces currently produces negative reward instead of positive, and (2) soldier piece values must become dynamic based on river-crossing status (pre-river=1, post-river=2).

The existing codebase provides solid foundations: `_build_legal_mask()` and `_build_piece_masks()` are already fully implemented and tested. The primary work is thin public wrappers, the reward sign fix, soldier river-crossing value distinction, and test coverage for all of the above.

**Primary recommendation:** Wrap existing internal methods as public API with minimal code; fix the reward sign bug and add soldier crossing logic to `_compute_reward`; add targeted tests for each fix.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Soldier river crossing: pre-river Soldier=1, post-river Soldier=2. Red soldier row <= 4 = crossed, Black soldier row >= 5 = crossed. Material capture reward = piece_value / 100
- **D-02:** No check reward -- Phase 11 only keeps terminal reward (+1/-1/0) + material capture + illegal penalty (-2.0). Team/cooperation rewards deferred to v1.0
- **D-03:** `get_legal_mask(player=1|-1)` -- public method, only supports querying current turn player's legal mask. Non-current player returns all-zero mask (no error)
- **D-04:** `get_piece_legal_mask(piece_type, player)` -- public method, only supports querying current turn player's piece type mask. Non-current player returns all-zero mask. piece_type is 0-6 index
- **D-05:** Existing `_build_legal_mask()` and `_build_piece_masks()` internal methods retained; public methods wrap them
- **D-06:** Basic correctness tests -- mask shape validation, reward value validation (material reward per piece type), illegal action handling, soldier pre/post-river value distinction

### Claude's Discretion
- Internal method refactoring details
- Specific FEN and action encoding choices for test cases
- Specific implementation of river-crossing check (row number comparison)

### Deferred Ideas (OUT OF SCOPE)
- Check reward (+0.05) -- deferred to v1.0 team reward design
- Opponent mask query (querying any side's legal moves) -- not needed for current RL training; opponent modeling in v1.0
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| R4 | Legal move masking: `get_legal_mask(player)`, `get_piece_legal_mask(piece_type, player)`, illegal move penalty | Existing `_build_legal_mask()` and `_build_piece_masks()` provide complete implementations; public methods are thin wrappers returning all-zero for non-current player |
| R5 | Basic reward signal: terminal +1/-1/0, material capture piece_value/100, soldier 1/2, illegal penalty -2.0 | Current `_compute_reward()` has a sign bug (inverted) and static soldier value; fix requires passing `to_sq` for river-crossing row lookup |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| gymnasium | 1.2.3 | Env base class, Discrete/Box spaces | Project dependency since Phase 09 |
| numpy | 2.4.3 | Array operations for masks and observations | Project dependency, float32 arrays |
| pytest | 9.0.2 | Test framework | Project test runner |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| XiangqiEngine | (internal) | Legal move generation, game state | All mask and reward operations delegate to engine |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Row comparison for river crossing | Board zone lookup table | Row comparison is simpler and sufficient (single if-check) |

**Installation:** No new packages needed. All dependencies already installed in conda env `xqrl`.

## Architecture Patterns

### Recommended Project Structure
```
src/xiangqi/rl/
    env.py          # XiangqiEnv -- add get_legal_mask, get_piece_legal_mask, fix _compute_reward
tests/
    test_rl.py      # Add new test functions for Phase 11
```

### Pattern 1: Public API Wrapping Internal Methods
**What:** Public methods delegate to existing private methods with player validation.
**When to use:** For `get_legal_mask` and `get_piece_legal_mask`.
**Example:**
```python
def get_legal_mask(self, player: int = 1) -> np.ndarray:
    """Public API: return full legal mask for current turn player.

    Non-current player returns all-zero mask (no error raised).
    """
    if self._engine is None or player != self._engine.turn:
        return np.zeros(8100, dtype=np.float32)
    return self._build_legal_mask()

def get_piece_legal_mask(self, piece_type: int, player: int) -> np.ndarray:
    """Public API: return per-piece-type legal mask for current turn player.

    piece_type: 0-6 index (0=General, 1=Advisor, ..., 6=Soldier)
    Non-current player returns all-zero mask.
    """
    if self._engine is None or player != self._engine.turn:
        return np.zeros(8100, dtype=np.float32)
    if not (0 <= piece_type <= 6):
        return np.zeros(8100, dtype=np.float32)
    masks = self._build_piece_masks()
    return masks[piece_type]
```

### Pattern 2: Dynamic Soldier Value with River Crossing Check
**What:** Soldier value depends on board row at capture time.
**When to use:** In `_compute_reward` when `abs(captured) == 7`.
**Example:**
```python
def _compute_reward(self, captured: int, to_sq: int = -1) -> float:
    """Compute shaping reward for captured piece (red perspective)."""
    if captured == 0:
        return 0.0

    piece_type = abs(captured)  # 1-7

    # Dynamic soldier value based on river crossing
    if piece_type == 7 and to_sq >= 0:
        to_row = to_sq // 9
        # Red soldier (+7): crossed river if to_row <= 4
        # Black soldier (-7): crossed river if to_row >= 5
        if captured > 0:  # Red soldier captured
            piece_value = 2.0 if to_row <= 4 else 1.0
        else:  # Black soldier captured
            piece_value = 2.0 if to_row >= 5 else 1.0
    else:
        piece_value = self.PIECE_VALUES.get(piece_type, 0)

    # Reward from red perspective: capturing enemy (captured < 0) = positive
    sign = -1 if captured > 0 else 1
    return sign * piece_value / 100.0
```

### Anti-Patterns to Avoid
- **Calling `_build_piece_masks()` twice in `get_piece_legal_mask`:** If called independently, it recomputes all 7 masks just to return one. Consider caching or accepting the cost (cheap for single env). For Phase 11, the simple approach is fine.
- **Modifying `_compute_reward` signature without updating `step()` call site:** The new `to_sq` parameter must be passed from `step()` where it is already decoded.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Legal mask construction | Custom move-to-index mapping | Existing `_build_legal_mask()` | Already handles encode_move/decode_move correctly |
| Per-piece mask construction | Manual piece-type-to-move mapping | Existing `_build_piece_masks()` | Handles canonical rotation correctly |
| Action encoding | Custom flat index math | `from_sq * 90 + to_sq` pattern | Established in Phase 09, used throughout |

## Common Pitfalls

### Pitfall 1: Reward Sign Inversion (CONFIRMED BUG)
**What goes wrong:** Current `_compute_reward` returns negative reward when Red captures Black pieces.
**Why it happens:** `sign = 1 if captured > 0 else -1` treats captured piece sign as the reward sign. But from Red's perspective, capturing a Black piece (captured < 0) should give positive reward.
**How to avoid:** Use `sign = -1 if captured > 0 else 1` (negated). Red capturing Black = captured < 0 = sign = 1 = positive reward.
**Warning signs:** Red agent learns to avoid capturing pieces; material reward has wrong sign in training.

### Pitfall 2: Missing `to_sq` in `_compute_reward`
**What goes wrong:** Cannot determine soldier river-crossing status without knowing the captured piece's row.
**Why it happens:** `_compute_reward(captured)` only receives the piece value, not its position.
**How to avoid:** Add `to_sq` parameter to `_compute_reward`; pass it from `step()` where `to_sq = action % 90` is already computed.
**Warning signs:** Soldier value always returns 1.0 regardless of board position.

### Pitfall 3: `_build_piece_masks()` Rebuild Overhead
**What goes wrong:** Calling `get_piece_legal_mask` rebuilds all 7 piece masks even if only one is needed.
**Why it happens:** `_build_piece_masks()` has no caching; each call iterates all legal moves.
**How to avoid:** Accept the overhead for Phase 11 (legal_moves() is fast, ~0.5ms). Cache optimization deferred.
**Warning signs:** Performance degradation only matters at >10K calls/second, not relevant for Phase 11.

### Pitfall 4: Canonical Rotation Confusion in Piece Masks
**What goes wrong:** Tests using raw engine coordinates instead of canonical coordinates when verifying piece masks.
**Why it happens:** Piece masks are built on the canonical (rotated) board, but test FEN positions may be set up thinking in raw coordinates.
**How to avoid:** When red to move, canonical = raw. When black to move, canonical = rotated 180. Tests should verify using `_get_info()` which already handles this.
**Warning signs:** Piece mask test fails only for black-to-move positions.

## Code Examples

### Adding Public API Methods to env.py
```python
# In class XiangqiEnv:

def get_legal_mask(self, player: int = 1) -> np.ndarray:
    """Public API (R4): full 8100-element legal move mask.

    Args:
        player: +1 for red, -1 for black. Only current turn player
                returns non-zero mask.

    Returns:
        np.ndarray (8100,) float32 -- 1.0 for legal actions, 0.0 otherwise.
        Returns all-zero mask if player != current turn player.
    """
    if self._engine is None or player != self._engine.turn:
        return np.zeros(8100, dtype=np.float32)
    return self._build_legal_mask()

def get_piece_legal_mask(self, piece_type: int, player: int) -> np.ndarray:
    """Public API (R4): per-piece-type legal move mask.

    Args:
        piece_type: int in [0, 6] (0=General, 1=Advisor, ..., 6=Soldier)
        player: +1 for red, -1 for black. Only current turn player
                returns non-zero mask.

    Returns:
        np.ndarray (8100,) float32 -- 1.0 for legal actions of that piece type.
        Returns all-zero mask if player != current turn player or invalid piece_type.
    """
    if self._engine is None or player != self._engine.turn:
        return np.zeros(8100, dtype=np.float32)
    if not (0 <= piece_type <= 6):
        return np.zeros(8100, dtype=np.float32)
    masks = self._build_piece_masks()
    return masks[piece_type]
```

### Fixing _compute_reward
```python
def _compute_reward(self, captured: int, to_sq: int = -1) -> float:
    """Compute shaping reward for captured piece (red perspective).

    Args:
        captured: piece value on target square (0=no capture, >0=red piece, <0=black piece)
        to_sq: flat square index of target (needed for soldier river-crossing check)
    """
    if captured == 0:
        return 0.0

    piece_type = abs(captured)

    # Dynamic soldier value based on river crossing
    if piece_type == 7 and to_sq >= 0:
        to_row = to_sq // 9
        if captured > 0:   # Red soldier captured by Black
            piece_value = 2.0 if to_row <= 4 else 1.0
        else:               # Black soldier captured by Red
            piece_value = 2.0 if to_row >= 5 else 1.0
    else:
        piece_value = self.PIECE_VALUES.get(piece_type, 0)

    # Red perspective: capturing enemy (captured < 0) = positive reward
    sign = -1 if captured > 0 else 1
    return sign * piece_value / 100.0
```

### Updated step() Call Site
```python
# In step(), change the _compute_reward call:
# OLD: reward = self._compute_reward(captured)
# NEW:
reward = self._compute_reward(captured, to_sq)
```

### Test: Soldier Pre/Post-River Value
```python
def test_soldier_pre_river_value():
    """D-01: Soldier value = 1 before crossing river."""
    # Red soldier at starting position (row 6, not crossed): value = 1
    # Use FEN with chariot that can capture soldier at row 6
    # After capture: reward should be +0.01 (1/100) from red perspective
    ...

def test_soldier_post_river_value():
    """D-01: Soldier value = 2 after crossing river."""
    # Red soldier at row 3 (crossed river): value = 2
    # After capture: reward should be +0.02 (2/100) from red perspective
    ...
```

### Test: Public API Non-Current Player Returns Zero Mask
```python
def test_get_legal_mask_non_current_player():
    """D-03: querying opponent's mask returns all-zero array."""
    env = XiangqiEnv()
    env.reset()
    # Red to move, query black's mask
    mask = env.get_legal_mask(player=-1)
    assert np.all(mask == 0.0)
    assert mask.shape == (8100,)

def test_get_piece_legal_mask_non_current_player():
    """D-04: querying opponent's piece mask returns all-zero array."""
    env = XiangqiEnv()
    env.reset()
    # Red to move, query black's chariot mask
    mask = env.get_piece_legal_mask(piece_type=4, player=-1)
    assert np.all(mask == 0.0)
    assert mask.shape == (8100,)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Static PIECE_VALUES dict | Dynamic soldier value via river-crossing check | Phase 11 (this phase) | Soldier captures now correctly valued at 1 or 2 |
| Inverted reward sign | Fixed sign logic in _compute_reward | Phase 11 (this phase) | Material capture rewards now correctly signed |

**Bugs being fixed:**
- `_compute_reward` sign inversion: Red capturing Black pieces was giving negative reward. Fix: negate sign logic.

## Open Questions

1. **PIECE_VALUES dict cleanup**
   - What we know: The static dict `{0:0, 1:0, 2:2, 3:2, 4:4, 5:9, 6:4.5, 7:1}` is used for non-soldier pieces. Key 7 (soldier) is still present but no longer used as-is.
   - What's unclear: Whether to remove key 7 from the dict or keep it as default fallback.
   - Recommendation: Keep key 7 as fallback (value 1) in PIECE_VALUES for safety, but the dynamic path overrides it. No harm in keeping it.

2. **`get_piece_legal_mask` calls `_build_piece_masks()` for all 7 types**
   - What we know: Current implementation builds all 7 masks even when only one is needed.
   - What's unclear: Whether this matters for Phase 11 performance.
   - Recommendation: Accept the overhead. The `_build_piece_masks()` call is fast (<1ms). Caching is an optimization for later.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| conda env `xqrl` | All operations | Yes | Python 3.12.0 | -- |
| gymnasium | Env interface | Yes | 1.2.3 | -- |
| numpy | Array operations | Yes | 2.4.3 | -- |
| pytest | Test runner | Yes | 9.0.2 | -- |
| XiangqiEngine | Legal move generation | Yes | (internal) | -- |

**Missing dependencies with no fallback:** None.

**Missing dependencies with fallback:** None.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | pyproject.toml |
| Quick run command | `/c/software/miniconda/envs/xqrl/python.exe -m pytest tests/test_rl.py -x -q` |
| Full suite command | `/c/software/miniconda/envs/xqrl/python.exe -m pytest tests/test_rl.py -v` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| R4 | get_legal_mask returns correct shape for current player | unit | `pytest tests/test_rl.py::test_get_legal_mask_current_player -x` | No -- Wave 0 |
| R4 | get_legal_mask returns all-zero for non-current player | unit | `pytest tests/test_rl.py::test_get_legal_mask_non_current_player -x` | No -- Wave 0 |
| R4 | get_piece_legal_mask returns correct per-type mask | unit | `pytest tests/test_rl.py::test_get_piece_legal_mask_current_player -x` | No -- Wave 0 |
| R4 | get_piece_legal_mask returns all-zero for non-current player | unit | `pytest tests/test_rl.py::test_get_piece_legal_mask_non_current_player -x` | No -- Wave 0 |
| R5 | Material capture reward correct for each piece type | unit | `pytest tests/test_rl.py::test_material_capture_reward -x` | No -- Wave 0 |
| R5 | Soldier pre-river value = 1 | unit | `pytest tests/test_rl.py::test_soldier_pre_river_value -x` | No -- Wave 0 |
| R5 | Soldier post-river value = 2 | unit | `pytest tests/test_rl.py::test_soldier_post_river_value -x` | No -- Wave 0 |
| R5 | Illegal move penalty = -2.0 | unit | `pytest tests/test_rl.py::test_illegal_move_penalty -x` | Yes (existing) |
| R5 | Terminal reward +1/-1/0 | unit | `pytest tests/test_rl.py::test_checkmate_detection -x` | Yes (existing) |

### Sampling Rate
- **Per task commit:** `/c/software/miniconda/envs/xqrl/python.exe -m pytest tests/test_rl.py -x -q`
- **Per wave merge:** `/c/software/miniconda/envs/xqrl/python.exe -m pytest tests/test_rl.py -v`
- **Phase gate:** Full suite green (21 existing + new tests) before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `test_get_legal_mask_current_player` -- covers R4 public API
- [ ] `test_get_legal_mask_non_current_player` -- covers D-03 zero-mask behavior
- [ ] `test_get_piece_legal_mask_current_player` -- covers R4 per-type mask
- [ ] `test_get_piece_legal_mask_non_current_player` -- covers D-04 zero-mask behavior
- [ ] `test_material_capture_reward` -- covers R5 reward per piece type
- [ ] `test_soldier_pre_river_value` -- covers D-01 pre-river value
- [ ] `test_soldier_post_river_value` -- covers D-01 post-river value
- [ ] `test_reward_sign_correct` -- covers R5 sign fix verification

## Sources

### Primary (HIGH confidence)
- `src/xiangqi/rl/env.py` -- Full source code of XiangqiEnv, all methods analyzed line-by-line
- `src/xiangqi/engine/types.py` -- Piece IntEnum, encode_move/decode_move verified
- `src/xiangqi/engine/engine.py` -- XiangqiEngine.apply() returns captured piece value confirmed
- `.planning/REQUIREMENTS.md` -- R4 and R5 requirement specifications
- `.planning/research/RL_ENV.md` -- Section 4 (reward design), Section 2 (action space), Section 10 (multi-agent)

### Secondary (MEDIUM confidence)
- Live verification: reward sign bug confirmed via interactive Python test (Red captures Black Horse returns -0.04 instead of +0.04)
- Live verification: soldier positions at starting position confirmed (Red row=6, Black row=3)
- Live verification: 21 existing tests all passing

### Tertiary (LOW confidence)
- None -- all findings verified against source code or live testing

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new dependencies, all existing verified
- Architecture: HIGH -- existing code analyzed, patterns clear
- Pitfalls: HIGH -- reward sign bug confirmed with live test, soldier crossing logic verified against coordinate system

**Research date:** 2026-03-28
**Valid until:** 2026-04-28 (stable, internal codebase changes are the only risk)
