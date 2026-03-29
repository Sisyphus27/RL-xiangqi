# Phase 09: XiangqiEnv Core - Research

**Researched:** 2026-03-26
**Domain:** Gymnasium RL environment interface wrapping XiangqiEngine
**Confidence:** HIGH (engine API fully understood, RL_ENV.md provides patterns; gymnasium API is well-documented)

---

## Summary

Phase 09 wraps `XiangqiEngine` as a `gym.Env` subclass. The critical finding is that **gymnasium is not yet in project dependencies** -- it must be added alongside numpy. The RL action is `from_sq * 90 + to_sq` (flat 0-8099), which is distinct from the engine's internal 16-bit `encode_move()`. The engine's `legal_moves()` returns 16-bit encoded moves that must be decoded to build action masks. Terminal detection delegates entirely to `engine.result()`. Thread safety (D-08) means one env instance per process, not thread-safe within a process.

**Primary recommendation:** Implement `XiangqiEnv` at `src/xiangqi/rl/env.py` as a thin wrapper. Add `gymnasium` to `pyproject.toml` dependencies. Use `engine.legal_moves()` + `decode_move()` to build `piece_masks`. Canonical rotation (D-10) rotates board 180 deg when black to move.

---

## User Constraints (from 09-CONTEXT.md)

### Locked Decisions
- **D-01:** `XiangqiEnv` at `src/xiangqi/rl/env.py`, new `rl/` submodule
- **D-02:** Wraps `XiangqiEngine` internally, lazy imports to avoid circular deps
- **D-03:** `Discrete(8100)`, action = `from_sq * 90 + to_sq` (NOT engine's 16-bit encode)
- **D-04:** `info["piece_masks"]` dict {piece_type: np.ndarray} 7 keys (0-6), 8100-element float32
- **D-05:** `info["piece_type_to_move"]` int 0-6 indicating which piece type is proposing
- **D-06:** Illegal move: `reward=-2.0`, `terminated=False`, state unchanged, `info["illegal_move"]=True`
- **D-07:** Terminal detection delegates to `engine.result()`
- **D-08:** NOT thread-safe -- one env per process; SyncVectorEnv workers each get own instance
- **D-09:** `reset(seed, options)` returns obs (16,10,9) float32; raw planes (not AlphaZero encoding -- Phase 10)
- **D-10:** Canonical board rotation -- active player always sees red at bottom

### Claude's Discretion
- Exact `render()` implementation (not needed for RL training)
- Internal method naming conventions
- Whether to use `__slots__` for memory efficiency

### Deferred Ideas (OUT OF SCOPE)
- AlphaZero observation encoding (Phase 10)
- Per-piece-type action masking implementation details (Phase 11)
- Self-play E2E validation (Phase 12)
- `render()` implementation (Phase 09 or 12)
- Gymnasium registration with `gymnasium.make()` (Phase 09 implementation detail)

---

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| R1 | Multi-Agent Gymnasium Env Interface | gymnasium.Env subclass with reset/step/observation_space/action_space |
| R2 | Multi-Agent Action Spaces (piece_masks dict) | D-04: 7-key dict with 8100-element float32 masks per piece type |
| R6 | Terminal Detection | D-07: delegates to engine.result() -- already implements WXF rules |
| R8 | Thread Safety for SyncVectorEnv | D-08: one env instance per process, not thread-safe |

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| gymnasium | 1.0.x (not yet installed) | RL env interface | Required by R1; gymnasium.make() compatible |
| numpy | >=2.0,<3.0 (in pyproject.toml) | Board arrays, action masks | Already in dependencies |

### Installation Required
```bash
# Add to pyproject.toml dependencies:
gymnasium>=1.0,<2.0
```

**Note:** gymnasium is NOT currently in project dependencies. This is a blocking gap.

### Project Source (Wrapping)
| Module | Purpose |
|--------|---------|
| `src/xiangqi/engine/engine.py` | XiangqiEngine facade: reset(), apply(), undo(), is_legal(), legal_moves(), is_check(), result(), board, turn |
| `src/xiangqi/engine/state.py` | XiangqiState: board (np.ndarray 10x9), turn, zobrist_hash_history |
| `src/xiangqi/engine/legal.py` | generate_legal_moves(), is_legal_move(), is_in_check() |
| `src/xiangqi/engine/endgame.py` | get_game_result() terminal detection (repetition, long-check, long-chase, checkmate) |
| `src/xiangqi/engine/types.py` | encode_move/decode_move (16-bit), Piece IntEnum, ROWS=10, COLS=9, NUM_SQUARES=90 |
| `src/xiangqi/engine/constants.py` | STARTING_FEN, from_fen(), to_fen() |
| `src/xiangqi/engine/moves.py` | all_pieces_of_color() |

---

## Architecture Patterns

### Recommended Project Structure
```
src/xiangqi/
├── rl/
│   ├── __init__.py       # exports XiangqiEnv
│   └── env.py            # XiangqiEnv gym.Env subclass
└── engine/
    ├── engine.py         # XiangqiEngine (existing)
    ├── types.py          # encode/decode move constants
    └── ...
```

### Pattern 1: Gymnasium Env Wrapper
**What:** `XiangqiEnv` inherits `gym.Env`, implements `reset()` and `step()`
**When to use:** For all RL training and evaluation
**Example:**
```python
# Source: RL_ENV.md §1, gymnasium docs
class XiangqiEnv(gym.Env):
    action_space: gym.spaces.Discrete  # set to 8100
    observation_space: gym.spaces.Box   # (16, 10, 9) float32

    def reset(self, seed=None, options=None):
        # Initialize engine, apply FEN if options["fen"] provided
        # Set self._np_random from seed
        obs = self._get_observation()   # (16, 10, 9) float32
        info = self._get_info()          # legal_mask, piece_masks, etc.
        return obs, info

    def step(self, action):
        # Decode flat action -> from_sq, to_sq
        # Validate with engine.is_legal()
        # Apply with engine.apply()
        # Handle illegal move (reward=-2.0, no state change)
        # Check terminal via engine.result()
        # Return (obs, reward, terminated, truncated, info)
```

### Pattern 2: Action Decoding
**What:** Flat RL action integer -> engine 16-bit move
**When to use:** In `step()` to convert gym action to engine move
**Example:**
```python
# D-03: action = from_sq * 90 + to_sq
from_sq = action // 90   # 0-89
to_sq = action % 90      # 0-89

# Convert to engine's 16-bit encoding (from types.py)
from_xq import encode_move
move = encode_move(from_sq, to_sq)  # 16-bit engine move
```

### Pattern 3: Legal Mask Building
**What:** Build full 8100-element and per-piece-type masks from engine legal moves
**When to use:** In `_get_info()` and `_get_legal_mask()`
**Example:**
```python
# D-04: piece_masks = {piece_type: np.zeros(8100, dtype=np.float32)}
# Engine returns 16-bit encoded moves; need decode_move
from_xq import decode_move
for move in self._engine.legal_moves():
    from_sq, to_sq, _ = decode_move(move)
    action_idx = from_sq * 90 + to_sq
    # Determine piece type from board at from_sq
    fr, fc = divmod(from_sq, 9)
    piece = abs(self._board[fr, fc])  # 1-7
    piece_masks[piece - 1][action_idx] = 1.0
    full_mask[action_idx] = 1.0
```

### Pattern 4: Canonical Observation Rotation
**What:** Rotate board 180 deg when black to move so red is always at bottom
**When to use:** In `_get_observation()` before encoding to planes
**Example:**
```python
# D-10: Canonical rotation
board = self._engine.board.copy()  # (10, 9)
if self._engine.turn == -1:  # black to move
    board = np.rot90(board, k=2)  # 180 deg rotation
# Then encode board to (16, 10, 9) planes
```

### Pattern 5: Illegal Move Handling
**What:** Illegal move returns penalty but does NOT update state
**When to use:** In `step()` when action is not legal
**Example:**
```python
# D-06
if not self._engine.is_legal(move):
    return (
        self._get_observation(),
        -2.0,
        False,   # terminated=False (game continues)
        False,   # truncated=False
        {**self._get_info(), "illegal_move": True}
    )
# State unchanged -- do NOT call engine.apply()
```

### Pattern 6: SyncVectorEnv Worker Pattern
**What:** Each worker process gets its own env instance
**When to use:** When using gymnasium.vector.SyncVectorEnv
**Example:**
```python
# D-08: NOT thread-safe; each worker gets own instance
def make_env(rank):
    def _init():
        env = XiangqiEnv()
        env.reset(seed=rank)
        return env
    return _init

vec_env = gym.vector.SyncVectorEnv([make_env(i) for i in range(n_envs)])
```

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Terminal detection | Custom checkmate/stalemate logic | `engine.result()` | Already implements WXF rules including perpetual check/chase |
| Repetition tracking | Custom Zobrist hash counter | `engine.state.zobrist_hash_history` | Already implemented in state.py |
| Legal move generation | Custom move validators | `engine.legal_moves()` | Already complete via generate_legal_moves() with king-safety |
| Board encoding | Custom FEN parser | `from_fen()` / `to_fen()` from constants.py | Already implemented |

**Key insight:** The engine is a complete, self-contained game state manager. The RL env is a thin wrapper that translates between gymnasium's array interface and the engine's API.

---

## Common Pitfalls

### Pitfall 1: Confusing engine's 16-bit encode_move with RL flat action encoding
**What goes wrong:** `step(action)` passes the flat RL action integer directly to `engine.apply()`, but engine expects 16-bit encoded move.
**Why it happens:** Engine's `encode_move(from_sq, to_sq)` produces a 16-bit integer with bits for from_sq, to_sq, and is_capture. RL uses `from_sq * 90 + to_sq` as a flat integer. These are different encodings.
**How to avoid:** In `step()`, decode the flat action first: `from_sq = action // 90`, `to_sq = action % 90`, then `move = encode_move(from_sq, to_sq)`, then `engine.apply(move)`.

### Pitfall 2: Mask building ignores canonical rotation
**What goes wrong:** `piece_masks` built from board without rotation are incorrect when black to move.
**Why it happens:** The RL loop expects masks from active player's perspective (D-10). If black to move, board is rotated 180 deg for the observation, but masks might be built from raw engine board.
**How to avoid:** Always build masks from the same board state used for the observation (canonical rotated or not rotated depending on whose turn it is).

### Pitfall 3: Missing lazy import causing circular dependency
**What goes wrong:** `from .engine import XiangqiEngine` at module top level causes circular import error.
**Why it happens:** engine.py imports from state.py, legal.py, etc. The rl/ package may not exist yet when engine imports.
**How to avoid:** Per D-02, import engine at method call time (lazy import): `from src.xiangqi.engine import XiangqiEngine` inside `__init__` or `reset()` not at module top level.

### Pitfall 4: Mutable default argument for info dict
**What goes wrong:** Returning a mutable default dict that gets mutated later.
**Why it happens:** `def _get_info(self): return {"legal_mask": ...}` -- returning same dict object each call.
**How to avoid:** Always create a new dict in `_get_info()`: `return {"legal_mask": ..., "piece_masks": ..., ...}`.

### Pitfall 5: Forgetting to convert piece_type to 0-6 range for mask dict keys
**What goes wrong:** Using piece value directly (1-7) as dict key instead of (0-6).
**Why it happens:** Piece IntEnum values are 1-7 (Piece.R_SHUAI=1, ..., Piece.R_BING=7). Mask dict keys per D-04 are 0-6.
**How to avoid:** Use `abs(piece) - 1` to convert from board piece values (1-7) to mask indices (0-6).

---

## Code Examples

### Action decoding from RL integer to engine move
```python
# src/xiangqi/engine/types.py
def encode_move(from_sq: int, to_sq: int, is_capture: bool = False) -> int:
    """16-bit encoding for engine internal use."""
    return (from_sq & 0x1FF) | ((to_sq << 9) & 0xFE00) | (int(is_capture) << 16)

def decode_move(move: int) -> Tuple[int, int, bool]:
    """Reverse the 16-bit encoding."""
    from_sq =  move        & 0x1FF
    to_sq   = (move >> 9)  & 0x7F
    capture =  (move >> 16) & 0x1
    return from_sq, to_sq, bool(capture)

# In XiangqiEnv.step():
from_sq = action // 90   # RL flat action
to_sq = action % 90      # RL flat action
move = encode_move(from_sq, to_sq)  # convert to engine format
```

### Legal mask building
```python
# Build full 8100-element legal mask
def _get_legal_mask(self) -> np.ndarray:
    mask = np.zeros(8100, dtype=np.float32)
    for move in self._engine.legal_moves():
        from_sq, to_sq, _ = decode_move(move)
        mask[from_sq * 90 + to_sq] = 1.0
    return mask

# Build per-piece-type masks
def _get_piece_masks(self) -> dict[int, np.ndarray]:
    masks = {pt: np.zeros(8100, dtype=np.float32) for pt in range(7)}
    for move in self._engine.legal_moves():
        from_sq, to_sq, _ = decode_move(move)
        action_idx = from_sq * 90 + to_sq
        fr, fc = divmod(from_sq, 9)
        piece_val = int(self._engine.board[fr, fc])
        pt_idx = abs(piece_val) - 1  # 0-6
        masks[pt_idx][action_idx] = 1.0
    return masks
```

### Canonical observation
```python
# RL_ENV.md §3: Canonical rotation
def _canonical_board(self) -> np.ndarray:
    """Return board with canonical rotation (active player sees red at bottom)."""
    board = self._engine.board.copy()  # (10, 9)
    if self._engine.turn == -1:  # black to move
        board = np.rot90(board, k=2)  # 180 deg
    return board
```

### Terminal detection via engine.result()
```python
# D-07: Terminal detection delegates to engine.result()
# engine.result() returns: 'RED_WINS' | 'BLACK_WINS' | 'DRAW' | 'IN_PROGRESS'
result = self._engine.result()
if result == 'IN_PROGRESS':
    terminated = False
else:
    terminated = True
    if result == 'RED_WINS':
        reward = 1.0   # red wins from red's perspective
    elif result == 'BLACK_WINS':
        reward = -1.0  # black wins from red's perspective
    else:  # DRAW
        reward = 0.0
```

### Gymnasium registration
```python
# Registration enables gymnasium.make("Xiangqi-v0")
# Can be done in env.py __init__ or a separate registration module
import gymnasium as gym

gym.register(
    id="Xiangqi-v0",
    entry_point="xiangqi.rl.env:XiangqiEnv",
)
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| gym==0.26.x (old step API) | gymnasium 1.0.x | Gymnasium rebranding | `step()` returns 5-tuple (obs, reward, terminated, truncated, info); old API (done, info) deprecated |
| gym.Env | gymnasium.Env | Gymnasium fork | Same interface, modernized |
| Manual Zobrist | Built into XiangqiState | Phase 04 | Repetition detection is automatic via engine |
| Single-agent action space | Multi-agent piece_masks in info dict | Phase 09 | Enables per-piece-type policy networks |

**Deprecated/outdated:**
- `gym==0.26.x` or earlier: No longer supported; use `gymnasium>=1.0`
- Custom move validators: Not needed; engine legal.py is complete

---

## Open Questions

1. **Should gymnasium registration happen in `env.py` `__init__` or a separate `rl/__init__.py`?**
   - What we know: D-01 says registration done in the rl/ submodule
   - What's unclear: Best practice location within rl/
   - Recommendation: Do it in `env.py` `__init__` (self-registering class pattern) for simplicity

2. **What should Phase 09's raw observation channels 14-15 contain before Phase 10?**
   - What we know: D-09 says raw planes (not AlphaZero encoding); R3 says channel 14=repetition, channel 15=halfmove
   - What's unclear: Whether to populate these with actual values or zeros
   - Recommendation: Populate with actual values from engine state (repetition count, halfmove clock) since they're readily available and correct; Phase 10 changes encoding not data

3. **Should reward be returned from active player's perspective or canonical (red) perspective?**
   - What we know: RL_ENV.md §4 returns reward for "the acting player"; canonical rotation means active player sees red at bottom
   - What's unclear: When black acts, does reward=-1.0 mean "black loses" or "black got negative reward"?
   - Recommendation: Reward is always from red's perspective (+1 = red wins), matching `engine.result()` semantics. Black's reward is the negative of red's.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| gymnasium | XiangqiEnv base class | NO | -- | **Must install: `pip install gymnasium>=1.0,<2.0`** |
| numpy | Board arrays, masks | **YES** (xqrl env) | >=2.0,<3.0 | None needed |
| Python >=3.11 | pyproject.toml requirement | **YES** | 3.12 | None needed |

**Missing dependencies with no fallback:**
- `gymnasium>=1.0,<2.0` -- required by R1 (gym.Env interface). **Must be added to `pyproject.toml` dependencies before Phase 09 implementation begins.**

**Missing dependencies with fallback:**
- None identified

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (existing project) |
| Config file | `pyproject.toml` [tool.pytest.ini_options] |
| Quick run command | `pytest tests/test_rl.py -x -q` |
| Full suite command | `pytest tests/ -q --tb=short` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command |
|--------|----------|-----------|------------------|
| R1 | XiangqiEnv.reset returns valid obs (16,10,9) + info | unit | `pytest tests/test_rl.py::test_reset_returns_correct_shapes -x` |
| R1 | XiangqiEnv.step accepts Discrete(8100) action | unit | `pytest tests/test_rl.py::test_step_accepts_valid_action -x` |
| R2 | info["piece_masks"] has 7 keys, each 8100-element float32 | unit | `pytest tests/test_rl.py::test_piece_masks_shape -x` |
| R6 | Terminal detected after checkmate | unit | `pytest tests/test_rl.py::test_checkmate_detection -x` |
| R6 | Terminal detected for repetition draw | unit | `pytest tests/test_rl.py::test_repetition_draw -x` |
| R8 | SyncVectorEnv with n_envs=2 produces valid episodes | integration | `pytest tests/test_rl.py::test_sync_vector_env -x` |

### Sampling Rate
- **Per task commit:** quick run command
- **Per wave merge:** full suite command
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_rl.py` -- test XiangqiEnv basic functionality
- [ ] `tests/conftest.py` -- shared fixtures if needed
- [ ] Add `gymnasium` to `pyproject.toml` dependencies

*(If no gaps: "None -- existing test infrastructure covers all phase requirements")*

---

## Sources

### Primary (HIGH confidence)
- `src/xiangqi/engine/engine.py` -- XiangqiEngine public API, confirmed 7 methods + 3 properties
- `src/xiangqi/engine/types.py` -- encode_move/decode_move, Piece IntEnum, ROWS/COLS/NUM_SQUARES constants
- `src/xiangqi/engine/legal.py` -- generate_legal_moves(), is_legal_move(), is_in_check()
- `src/xiangqi/engine/endgame.py` -- get_game_result() terminal detection logic
- `src/xiangqi/engine/state.py` -- XiangqiState board representation, zobrist_hash_history
- `src/xiangqi/engine/moves.py` -- all_pieces_of_color(), pseudo-legal generators
- `.planning/research/RL_ENV.md` -- gym.Env patterns, action space design, canonical rotation
- `gymnasium 1.0.x documentation` -- gym.Env interface specification

### Secondary (MEDIUM confidence)
- gymnasium GitHub -- Maskableppo wrapper patterns, vector env patterns
- AlphaZero paper (Silver et al., PNAS 2018) -- board plane representation rationale

### Tertiary (LOW confidence)
- None

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- gymnasium API is stable, numpy already in project
- Architecture: HIGH -- engine API fully understood, wrapping pattern clear
- Pitfalls: HIGH -- identified key encoding mismatch and rotation issues

**Research date:** 2026-03-26
**Valid until:** 2026-04-25 (30 days -- gymnasium API is stable)
