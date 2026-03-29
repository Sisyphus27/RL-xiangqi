# Phase 10: Observation Encoding - AlphaZero Board Planes - Context

**Gathered:** 2026-03-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Fix and validate the AlphaZero-style (16, 10, 9) board plane observation encoding in XiangqiEnv. Deliver a correct, tested canonical rotation + 16-channel encoding that replaces Phase 09's placeholder infrastructure.

**Phase 09 already delivered:**
- `XiangqiEnv` gym.Env subclass with `reset()` / `step()` infrastructure
- `observation_space = Box(0.0, 1.0, (16, 10, 9), float32)`
- `info["piece_masks"]`, `info["piece_type_to_move"]`, `info["legal_mask"]`
- Canonical rotation scaffolding (`_canonical_board()`, `_get_observation()`)

**Phase 10 delivers:**
- Corrected (16, 10, 9) encoding — all 16 channels verified
- Canonical rotation bug fixed
- Full test suite validating all encoding cases

**Out of scope for Phase 10:**
- History planes (channels 16-31, deferred to v0.1)
- Flying-General channel (channel 16, deferred)
- Action masking implementation (Phase 11)

</domain>

<decisions>
## Implementation Decisions

### Encoding Shape
- **D-10-01:** Keep `(16, 10, 9)` — no expansion to 17 or 32 channels in Phase 10
- Observation space from Phase 09 (`Box(0.0, 1.0, (16, 10, 9), float32)`) remains correct

### Channel Layout (16 planes)
- **D-10-02:** Channels 0-6: Red piece types (General, Advisor, Elephant, Horse, Chariot, Cannon, Soldier)
- **D-10-03:** Channels 7-13: Black piece types (same 7 types)
- **D-10-04:** Channel 14: Repetition count, normalized 0-3 (clipped / 3.0)
- **D-10-05:** Channel 15: Halfmove clock, normalized 0-1 (clipped to [0,100] / 100.0)

### Canonical Board Rotation (Critical Fix)
- **D-10-06:** Observation always from active player's perspective (per D-10 from Phase 09)
- **D-10-07:** Bug confirmed in current `_canonical_board()` — rotates coordinates 180° but does NOT negate piece values
  - Effect: black pieces stay negative after rotation → routed to channels 7-13 → WRONG in canonical view
  - Fix required: negate piece values after rotation so active player always appears as red
  - Consequence: ALL existing observation tests for black-to-move positions are invalid

### History Planes
- **D-10-08:** Skip history planes in Phase 10
- Keep (16, 10, 9) only — current shape sufficient for Phase 10 validation
- History (channels 16-31, 8 plies) deferred to v0.1 per RL_ENV.md §3 guidance

### Flying-General Channel
- **D-10-09:** Skip Flying-General channel in Phase 10
- Engine `is_legal()` already blocks flying-general violations via action mask
- RL does not need to read this from observation — deferred to future phase

### Test Coverage Strategy
- **D-10-10:** Complete validation set — 4 test categories required:
  1. **Piece channel encoding** — starting position, all 14 piece channels present and correct
  2. **Canonical rotation** — black-to-move position, all pieces mapped to red channels (0-6)
  3. **Repetition channel** — sequence of moves creating loop, channel 14 value correct
  4. **Halfmove clock channel** — non-capture/non-pawn moves sequence, channel 15 increments correctly

### Claude's Discretion
- Internal method naming conventions (`_get_observation` vs `_encode_board` vs `_build_planes`)
- Exact implementation of the canonical rotation fix (negate values before or after rotation)
- Test file organization and naming conventions (follow Phase 09 pattern)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 09 Context (binding decisions)
- `.planning/phases/09-xiangqi-env-core/09-CONTEXT.md` — D-10 (canonical rotation), D-09 (observation space shape), Phase 09 deferred items

### RL Environment Design
- `.planning/research/RL_ENV.md` §3 — AlphaZero board plane specification, channel layout, canonical rotation rationale
- `.planning/research/RL_ENV.md` §3 (History Planes) — guidance to defer history to v0.1
- `.planning/research/RL_ENV.md` §8 — AlphaXiangqi paper (arXiv:2410.04865) as architecture reference

### Engine (wrapping)
- `src/xiangqi/engine/engine.py` — `XiangqiEngine` public API used by env
- `src/xiangqi/engine/state.py` — `XiangqiState` board array, `halfmove_clock`, `zobrist_hash_history`
- `src/xiangqi/engine/types.py` — `Piece` IntEnum, `encode_move`/`decode_move`
- `src/xiangqi/engine/endgame.py` — `get_game_result()` terminal detection (for repetition testing)

### Current Implementation (must read before fixing)
- `src/xiangqi/rl/env.py` — current `_get_observation()`, `_canonical_board()`, `_build_legal_mask()` — contains the canonical rotation bug

### Tests (reference for coverage pattern)
- `tests/test_rl.py` — existing RL tests (Phase 09)

</canonical_refs>

<code_context>
## Existing Code Insights

### Bug Location
`src/xiangqi/rl/env.py:152-157` — `_canonical_board()`:
```python
def _canonical_board(self):
    board = self._engine.board.copy()  # (10, 9)
    if self._engine.turn == -1:  # black to move
        board = np.rot90(board, k=2)  # 180 degree rotation
    return board
```
**Problem:** Rotates coordinates but leaves piece values unchanged (negative = black stays negative).
After rotation, `_get_observation()` sees black pieces as `piece > 0 == False` → routes to channels 7-13.
In canonical view (active player = red), all pieces should map to channels 0-6.

### Current `_get_observation()` Logic (correct once canonical_board is fixed)
```python
for r in range(10):
    for c in range(9):
        piece = int(board[r, c])
        if piece == 0:
            continue
        is_red = piece > 0
        pt = abs(piece) - 1  # 0-6
        channel = pt if is_red else (pt + 7)
        planes[channel, r, c] = 1.0
```
This is structurally correct — the fix is in `_canonical_board()`.

### Established Patterns
- Phase 09 uses lazy imports (`_get_engine_class()`) to avoid circular dependencies
- Tests in `tests/test_rl.py` use `pytest` with `XiangqiEnv` direct instantiation
- Engine's `from_fen()` already tested for WXF 5-field FEN (Phase 09-05)

### Integration Points
- `src/xiangqi/rl/env.py` — primary file to modify (canonical rotation fix + test)
- `src/xiangqi/rl/__init__.py` — no changes needed
- `src/xiangqi/__init__.py` — XiangqiEnv already exported from Phase 09

</code_context>

<specifics>
## Specific Ideas

No additional specific requirements — standard AlphaZero encoding approach, open to planner's implementation details.

</specifics>

<deferred>
## Deferred Ideas

None — all suggestions were discussed and explicitly deferred within scope.

### Reviewed and Deferred
- **History planes (channels 16-31)** — Phase 10 keeps (16,10,9); history deferred to v0.1 per RL_ENV.md §3
- **Flying-General channel (channel 16)** — Phase 10 skips; engine `is_legal()` blocks these moves via mask; deferred to future phase

</deferred>

---

*Phase: 10-observation-encoding-alpha-planes*
*Context gathered: 2026-03-27*
