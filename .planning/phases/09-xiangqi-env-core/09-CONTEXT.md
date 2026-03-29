# Phase 09: XiangqiEnv Core - Context

**Gathered:** 2026-03-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Build `XiangqiEnv` as a `gym.Env` subclass wrapping the existing XiangqiEngine. Phase 09 delivers the core RL environment interface with: `reset()`, `step()`, `observation_space`, `action_space`, `info["piece_masks"]` for multi-agent action masking, `info["piece_type_to_move"]`, terminal detection, and thread/process safety for `gymnasium.vector.SyncVectorEnv`.

**Out of scope for Phase 09:**
- AlphaZero observation encoding (Phase 10)
- Per-piece-type action masking implementation (Phase 11)
- Self-play E2E validation (Phase 12)

</domain>

<decisions>
## Implementation Decisions

### Module Location
- **D-01:** `XiangqiEnv` lives at `src/xiangqi/rl/env.py`
- New `rl/` submodule created under `src/xiangqi/`
- `gymnasium.make("Xiangqi-v0")` compatible registration done here

### State Management
- **D-02:** `XiangqiEnv` wraps an internal `_engine: XiangqiEngine` instance
- All move generation, validation, and terminal detection delegate to engine
- Board state (np.ndarray 10×9), turn, history managed by engine
- No state duplication — engine is source of truth
- Avoids circular imports by importing engine at method call time (lazy import)

### Action Space
- **D-03:** Flat `gym.spaces.Discrete(8100)` — `action = from_sq * 90 + to_sq`
- Decoding: `from_sq = action // 90`, `to_sq = action % 90`
- Full 8100-element boolean mask returned via `info["legal_mask"]`

### Multi-Agent Interface
- **D-04:** `info["piece_masks"]` — dict `{piece_type: np.ndarray}` with 7 keys (0-6)
  - GENERAL=0, ADVISOR=1, ELEPHANT=2, HORSE=3, CHARIOT=4, CANNON=5, SOLDIER=6
  - Each mask is 8100-element float32, 1.0 = legal move for that piece type
- **D-05:** `info["piece_type_to_move"]` — int 0-6 indicating which piece type is proposing
  - Active player is always red perspective (canonical rotation applied before encoding)
  - RL loop reads this to select the corresponding `piece_masks` entry

### Illegal Move Handling
- **D-06:** Illegal move in `step()`: returns `reward=-2.0`, `terminated=False`
- State is NOT updated — board remains unchanged
- `info["illegal_move"] = True` — flag for logging/debugging
- Game continues, allowing policy to explore without fatal episodes

### Terminal Detection
- **D-07:** Delegates entirely to `XiangqiEngine.result()`
- Conditions: checkmate, stalemate (kunbi → player to move loses), 4-fold repetition, 50-move rule, WXF perpetual check/chase
- `terminated=True` when result != 'IN_PROGRESS'

### Thread Safety
- **D-08:** `XiangqiEnv` instance is NOT thread-safe — one env per process
- For `SyncVectorEnv`, each worker process gets its own env instance
- EngineSnapshot pattern from `src/xiangqi/ai/base.py` is NOT used — RL env does not share state across threads

### Reset Behavior
- **D-09:** `reset(seed=None, options=None)` → `(obs, info)`
- `obs`: (16, 10, 9) float32 board planes (canonical rotation applied)
- `info`: contains `legal_mask`, `piece_masks`, `piece_type_to_move`, `player_to_move`
- If `options.get("fen")` provided, initialize from FEN instead of starting position
- Seed sets `self._np_random` for any stochastic behavior

### Canonical Board Rotation
- **D-10:** Observation always from active player's perspective (red at bottom)
- Implemented via `_canonical_observation()` — rotates board 180° when black to move
- This is Phase 10's encoding concern; Phase 09 provides the raw (16,10,9) tensor infrastructure

### Claude's Discretion
- Exact `render()` implementation (human vs rgb_array mode) — not needed for RL training
- Internal method naming conventions
- Whether to use `__slots__` for memory efficiency

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### RL Environment Design
- `.planning/REQUIREMENTS.md` §R1, R2, R4, R6, R8 — interface contracts, action space, terminal detection, thread safety requirements
- `.planning/research/RL_ENV.md` §1, §2, §3, §6 — gym.Env interface code examples, action encoding, canonical rotation, vectorized env patterns

### Engine (wrapping)
- `src/xiangqi/engine/engine.py` — XiangqiEngine public API (reset, apply, undo, is_legal, legal_moves, is_check, result, board, turn)
- `src/xiangqi/engine/state.py` — XiangqiState dataclass, Zobrist hashing
- `src/xiangqi/engine/endgame.py` — get_game_result() terminal detection logic
- `src/xiangqi/engine/types.py` — Piece IntEnum, encode_move/decode_move, ROWS/COLS/NUM_SQUARES constants

### AI Interface (reference)
- `src/xiangqi/ai/base.py` §EngineSnapshot — thread-safe state capture pattern (reference only, not reused)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `XiangqiEngine` — complete game state management, legal move generation, terminal detection. Wrapped directly.
- `XiangqiState` — board (np.ndarray 10×9), turn, king_positions dict. Used by engine internally.
- `encode_move` / `decode_move` — flat action encoding (from_sq * 90 + to_sq). Used for action integer ↔ square pair conversion.
- `generate_legal_moves`, `is_in_check` — engine internals exposed via `engine.legal_moves()` and `engine.is_check()`
- Zobrist hashing already implemented in `state.py` for repetition detection

### Established Patterns
- Lazy imports in `engine.py` to avoid circular dependencies — apply same pattern in env if needed
- `EngineSnapshot(frozen=True)` pattern for thread-safe state — not used in env but good reference
- `get_game_result()` already implements WXF perpetual check/chase detection — env just calls `engine.result()`

### Integration Points
- `src/xiangqi/__init__.py` — likely needs `XiangqiEnv` exported when created at `src/xiangqi/rl/env.py`
- `src/xiangqi/rl/__init__.py` — new package init needed
- Gymnasium registration: `gymnasium.register(id="Xiangqi-v0", entry_point="xiangqi.rl.env:XiangqiEnv")`

</code_context>

<specifics>
## Specific Ideas

No specific examples or references provided — open to standard approaches.

</specifics>

<deferred>
## Deferred Ideas

- Observation encoding as (16,10,9) AlphaZero board planes — Phase 10
- Per-piece-type action masking implementation details — Phase 11
- Self-play E2E validation with Random vs Random — Phase 12
- `render()` implementation (human/rgb_array modes) — Phase 09 or 12
- Gymnasium registration with `gymnasium.make()` — Phase 09 implementation detail (can be done in env `__init__` or separate registration module)

</deferred>

---

*Phase: 09-xiangqi-env-core*
*Context gathered: 2026-03-26*
